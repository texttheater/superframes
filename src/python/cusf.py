import collections
import logging
import math
import re
import sys
from typing import Callable, Dict, Iterable, List, Optional, Set, TextIO, \
        Tuple, Union


from pyconll.exception import ParseError
from pyconll.tree import Tree as PyCoNLLTree
from pyconll.unit.sentence import Sentence as PyCoNLLSentence
import pyconll


import blocks
import labels


# FIXME word IDs are not always ints
FRAME_LINE = re.compile(r'\[(?P<label>[^]]*)] (?P<text>.*?) \((?P<head>\d+)\)(?: *# *(?P<comment>.*))?$')
ARG_DEPS = set((
    'nsubj', 'obj', 'iobj', 'csubj', 'ccomp', 'xcomp', 'obl', 'advcl',
    'advmod', 'nmod', 'nummod', 'acl', 'amod', 'compound', 'orphan',
    'det:poss',
    # SUD deps:
    'subj', 'udep', 'mod', 'comp',
))
PRED_DEPS = ARG_DEPS | set((
    'root', 'conj', 'parataxis', 'list', 'reparandum', 'dep', 'vocative',
    'dislocated', 'appos',
))


def subtrees(
    tree: PyCoNLLTree,
    test: Callable[[PyCoNLLTree],bool]=lambda _: True
) -> Iterable[PyCoNLLTree]:
    """Returns the subtrees of the given tree

    If test is given, subtrees for which it returns False (and all their
    subtrees) will be excluded."""
    yield tree
    for child in tree:
        if test(child):
            yield from subtrees(child)


def arg_subtrees(tree: PyCoNLLTree) -> Iterable[PyCoNLLTree]:
    yield tree
    for child in tree:
        if not child.data.deprel.startswith('conj'):
            yield from subtrees(child)


def form_for_predicate(tree: PyCoNLLTree) -> str:
    def is_mwe_tree(t: PyCoNLLTree) -> bool:
        return t.data.deprel.split(':')[0] in ('fixed', 'flat', 'mwe', 'appos', 'goeswith')
    trees = sorted(subtrees(tree, is_mwe_tree), key=lambda t: id_sort_key(t.data.id))
    return ' '.join(t.data.form for t in trees)


def form_for_argument(tree: PyCoNLLTree) -> str:
    trees = [tree]
    nc_children = [c for c in tree if not c.data.deprel.startswith('conj')]
    trees.extend(s for c in nc_children for s in subtrees(c))
    trees.sort(key=lambda t: id_sort_key(t.data.id))
    return ' '.join(t.data.form for t in trees)


def id_sort_key(token_id: str) -> int: # TODO support other kinds of token IDs
    return int(token_id)


def tree_for_token(token_id: str, tree: PyCoNLLTree) -> PyCoNLLTree:
    for t in subtrees(tree):
        if t.data.id == token_id:
            return t


def remove_features(deprel: str) -> str:
    return re.split(r'[:@]', deprel)[0]


def is_semantic_predicate(tree: PyCoNLLTree) -> bool:
    # Prevent spuriously including function word conjuncts
    if tree.data.deprel == 'conj' and tree.parent \
            and not is_semantic_predicate(tree.parent):
        return False
    # Exclude verb particles
    if tree.data.deprel == 'compound:prt':
        return False
    # Include any predicate with one of PRED_DEPS as relation
    return any(tree.data.deprel.startswith(r) for r in PRED_DEPS)


def is_semantic_dependent(tree: PyCoNLLTree) -> bool:
    return any(tree.data.deprel.startswith(r) for r in ARG_DEPS)


class Arg:

    def __init__(self, head: str, text: str, label: str, comment: str):
        self.head = head
        self.text = text
        self.label = label
        self.comment = comment

    def is_empty(self) -> bool:
        return not self.label and not self.comment

    def to_line(self) -> str:
        comment = (f' # {self.comment}') if self.comment else ''
        return f'[{self.label}] {self.text} ({self.head}){comment}'

    @staticmethod
    def from_line(line: str) -> 'Arg':
        m = FRAME_LINE.match(line)
        head = m.group('head')
        text = m.group('text')
        label = m.group('label')
        comment = m.group('comment') or ''
        arg = Arg(head, text, label, comment)
        return arg


class Frame:

    def __init__(self, head: str, text: str = '', label: str='',
            comment:str ='', args: Optional[List[Arg]]=None):
        self.head = head
        self.text = text
        self.label = label
        self.comment = comment
        self.args = [] if args is None else args

    def to_block(self) -> blocks.Block:
        block = []
        comment = (f' # {self.comment}') if self.comment else ''
        block.append(f'[{self.label}] {self.text} ({self.head}){comment}')
        for arg in self.args:
            block.append(arg.to_line())
        return block

    def fill_args(self, expected_args: Set[Tuple[str, str]]):
        # Keep existing args, fill in missing expected args
        existing_args_by_head = collections.defaultdict(list)
        for arg in self.args:
            if arg.label or arg.comment:
                existing_args_by_head[arg.head].append(arg)
        self.args = []
        for head, text in expected_args:
            if head in existing_args_by_head:
                for arg in existing_args_by_head[head]:
                    self.args.append(arg)
            else:
                self.args.append(Arg(head, text, '', ''))
        for args in existing_args_by_head.values():
            for arg in args:
                if arg not in self.args:
                    self.args.append(arg)

    def find_arg(self, label: str) -> Optional[Arg]:
        for arg in self.args:
            if arg.label == label:
                return arg
        return None

    def is_empty(self) -> bool:
        return not self.label and not self.comment and all(a.is_empty() for a in self.args)

    def is_completely_annotated(self) -> bool:
        return self.label and all(a.label for a in self.args)

    def check(self, sentence: 'Sentence', lineno: int) -> Tuple[bool, int]:
        # Convert sentence to tree
        tree = sentence.syntax[0].to_tree()
        # Find subtree corresponding to predicate
        pred_tree = tree_for_token(self.head, tree)
        if pred_tree is None:
            logging.warning(
                'sent %s line %s token %s not found in syntax',
                sentence.syntax[0].id, lineno, self.head,
            )
            return False, 1
        # Check for wrong text
        expected_text = form_for_predicate(pred_tree)
        if self.text != expected_text:
            logging.warning(
                'sent %s line %s wrong text for frame: '
                'is "%s" but should be "%s"',
                sentence.syntax[0].id, lineno, self.text, expected_text,
            )
        # Check for missing frame label
        if not self.label:
            return False, 0
        # Check for wrong frame label
        if not labels.check_frame_label(self.label):
            logging.warning('sent %s line %s unknown frame label: %s',
                    sentence.syntax[0].id, lineno, self.label)
            return False, 1
        # Check arguments
        ok = True
        warnings = 0
        for i, arg in enumerate(self.args, start=lineno + 1):
            # Find token corresponding to argument
            try:
                arg_token = sentence.syntax[0][arg.head]
            except KeyError:
                logging.warning(
                    'sent %s line %s token % not found in syntax',
                    sentence.syntax[0].id, i, arg.head,
                )
                return False, 1
            arg_tree = tree_for_token(arg.head, tree)
            if arg_tree is None:
                logging.warning(
                    'sent %s line %s token % not found in syntax',
                    sentence.syntax[0].id, i, arg.head,
                )
                return False, 1
            # Check for wrong text
            if arg_token.head == self.head:
                expected_text = form_for_argument(arg_tree)
                if arg.text != expected_text:
                    logging.warning(
                        'sent %s line %s wrong text for subtree with root %s: '
                        'is "%s" but should be "%s"',
                        sentence.syntax[0].id, i,
                        arg.head, arg.text, expected_text,
                    )
            else:
                expected_text = arg_token.form
                # We don't check in this case, for now.
            # Check for annotated appos edges:
            arg_token = sentence.syntax[0][arg.head]
            if arg_token.head == self.head and \
                    arg_token.deprel.startswith('appos'):
                logging.warning('sent %s line %s appos edges should not be '
                        'annotated', sentence.syntax[0].id, i)
            # Check for wrong dep label
            if not labels.check_dep_label(arg.label, self.label):
                logging.warning('sent %s line %s unknown dep label for %s: %s',
                        sentence.syntax[0].id, i, self.label, arg.label)
                ok = False
                warnings += 1
            # Check for missing depictive backlinks
            if arg.label == 'm-depictive':
                arg_trees = [
                    tree_for_token(a.head, tree)
                    for a in self.args
                    if a.head != arg.head
                ]
                subtree_ids = set(
                    s.data.id
                    for a in arg_trees
                    for s in arg_subtrees(a)
                )
                backlink_found = False
                for frame in sentence.frames:
                    if isinstance(frame, Frame) and frame.head == arg.head:
                        for arg2 in frame.args:
                            if arg2.head in subtree_ids:
                                backlink_found = True
                                logging.debug(
                                    'sent %s line %s found backlink: %s',
                                    sentence.syntax[0].id,
                                    i,
                                    arg2.head,
                                )
                if not backlink_found:
                    logging.warning(
                        'sent %s line %s depictive has to share an argument with its parent frame',
                        sentence.syntax[0].id,
                        i,
                    )
                    ok = False
                    warnings += 1
        return ok, warnings

    @staticmethod
    def from_block(block: blocks.Block) -> 'Frame':
        m = FRAME_LINE.match(block[0])
        head = m.group('head')
        text = m.group('text')
        label = m.group('label')
        comment = m.group('comment') or ''
        frame = Frame(head, text, label, comment)
        for line in block[1:]:
            frame.args.append(Arg.from_line(line))
        return frame

    @staticmethod
    def init_from_tree(tree: PyCoNLLTree) -> 'Frame':
        frame = Frame(tree.data.id, form_for_predicate(tree))
        return frame


"""Can't parse a frame? Represent it as a block."""
Frameish = Union[Frame, blocks.Block]


class Sentence:

    syntax: PyCoNLLSentence
    lineno: int
    frames: List[Frameish]
    frame_linenos: List[int]

    def __init__(self, syntax: PyCoNLLSentence, lineno: int):
        self.syntax = syntax
        self.lineno = lineno
        self.frames = []
        self.frame_linenos = []

    def add_frame(self, block: blocks.Block, lineno: int):
        try:
            frame = Frame.from_block(block)
            self.frames.append(frame)
        except:
            self.frames.append(block)
        self.frame_linenos.append(lineno)

    def get_frame(self, head: str) -> Optional[Frame]:
        """Returns the frame with the given head ID, or None"""
        for frame in self.frames:
            if frame.head == head:
                return frame

    def traverse(self, head: str) -> Set[str]:
        """Traverses the semantic graph.

        Returns the head IDs of frames that are reachable via semantic links
        from the one with the given head ID.
        """
        seen = set()
        agenda = [head]
        while agenda:
            head = agenda.pop()
            seen.add(head)
            match self.get_frame(head):
                case None:
                    pass
                case frame:
                    for arg in frame.args:
                        if arg.label:
                            if arg.head not in seen:
                                agenda.append(arg.head)
        return seen

    def link_exists(self, ancestor_head: str, descendant_head: str) -> bool:
        return descendant_head in self.traverse(ancestor_head)

    def deep_link_exists(self: str, ancestor_head: str, descendant_head: str) -> bool:
        return any(
            self.link_exists(a, descendant_head)
            for a in self.traverse(ancestor_head)
        )

    def fill(self):
        """Add missing frames/args"""
        # Phase 0: ignore sentences with syntax errors
        if not all(isinstance(f, Frame) for f in self.frames):
            return
        # Phase 1: collect expected frame-arg links
        expected_links = collections.defaultdict(list)
        # Phase 1a: syntactic links
        for sentence in self.syntax:
            try:
                tree = sentence.to_tree()
            except ValueError as e:
                logging.warning('sent %s line %s invalid syntax: %s', sentence.id, self.lineno, e)
                return
            for subtree in subtrees(sentence.to_tree()):
                if is_semantic_predicate(subtree):
                    for child in subtree:
                        if is_semantic_dependent(child):
                            arg_tree = tree_for_token(child.data.id, tree)
                            expected_links[subtree.data.id].append((
                                child.data.id,
                                form_for_argument(arg_tree),
                            ))
                            for grandchild in child:
                                if grandchild.data.deprel.startswith('conj'):
                                    arg_tree = tree_for_token(grandchild.data.id, tree)
                                    expected_links[subtree.data.id].append((
                                        grandchild.data.id,
                                        form_for_argument(arg_tree)
                                    ))
        # Phase 1b: participant-scene links
        for frame in self.frames:
            if frame.label.split('-')[0] == 'SCENE':
                participant = frame.find_arg('participant')
                initial_scene = frame.find_arg('initial-scene')
                transitory_scene = frame.find_arg('transitory-scene')
                scene = frame.find_arg('scene')
                target_scene = frame.find_arg('target-scene')
                if participant:
                    protoarg = (participant.head, participant.text)
                    if initial_scene and not self.deep_link_exists(initial_scene.head, participant.head):
                        expected_links[initial_scene.head].append(protoarg)
                    if transitory_scene and not self.deep_link_exists(transitory_scene.head, participant.head):
                        expected_links[transitory_scene.head].append(protoarg)
                    if scene and not self.deep_link_exists(scene.head, participant.head):
                        expected_links[scene.head].append(protoarg)
                    if target_scene and not self.deep_link_exists(target_scene.head, participant.head):
                        expected_links[target_scene.head].append(protoarg)
            for arg in frame.args:
                if arg.label == 'm-scene' and not self.deep_link_exists(arg.head, frame.head):
                    protoarg = (frame.head, frame.text)
                    if not self.deep_link_exists(arg.head, frame.head):
                        expected_links[arg.head].append(protoarg)
        # Phase 1c: topic-content links
        for frame in self.frames:
            if frame.label.split('-')[0] == 'MESSAGE':
                topic = frame.find_arg('topic')
                initial_content = frame.find_arg('initial-content')
                transitory_content = frame.find_arg('transitory-content')
                content = frame.find_arg('content')
                target_content = frame.find_arg('target-content')
                if topic:
                    protoarg = (topic.head, topic.text)
                    if initial_content and not self.deep_link_exists(initial_content.head, topic.head):
                        expected_links[initial_content.head].append(protoarg)
                    if transitory_content and not self.deep_link_exists(transitory_content.head, topic.head):
                        expected_links[transitory_content.head].append(protoarg)
                    if content and not self.deep_link_exists(content.head, topic.head):
                        expected_links[content.head].append(protoarg)
                    if target_content and not self.deep_link_exists(target_content.head, topic.head):
                        expected_links[target_content.head].append(protoarg)
            for arg in frame.args:
                if arg.label == 'm-content' and not self.deep_link_exists(arg.head, frame.head):
                    protoarg = (frame.head, frame.text)
                    expected_links[arg.head].append(protoarg)
        # Phase 2: remove empty frames
        self.frames = [f for f in self.frames if not f.is_empty()]
        # Phase 3: add missing frames and args
        cursor = 0 # index at which we insert the next missing frame
        for sentence in self.syntax:
            for tree in subtrees(sentence.to_tree()):
                if is_semantic_predicate(tree):
                    frame_already_present = False
                    for index, frame in enumerate(self.frames):
                        if frame.head == tree.data.id:
                            frame_already_present = True
                            frame.fill_args(expected_links[frame.head])
                            cursor = index + 1
                            break
                    if not frame_already_present:
                        frame = Frame.init_from_tree(tree)
                        frame.fill_args(expected_links[frame.head])
                        self.frames.insert(cursor, frame)
                        cursor += 1

    def check(self, warn_non_semantic_dependent: bool=False) -> Tuple[int, int, int]:
        head_frame_map = {}
        head_lineno_map = {}
        for frame_lineno, frame in zip(self.frame_linenos, self.frames):
            if isinstance(frame, Frame):
                if frame.head in head_frame_map:
                    logging.warning(
                        'sent %s line %s duplicate frame for head word %s',
                        self.syntax[0].id, frame_lineno, frame.head,
                    )
                else:
                    head_frame_map[frame.head] = frame
                    head_lineno_map[frame.head] = frame_lineno
            else:
                logging.warning('sent %s line %s cannot parse frame %s',
                        self.syntax[0].id, frame_lineno, repr('\n'.join(frame)))
        annotated_count = 0
        warnings = 0
        for frame in head_frame_map.values():
            ok, w = frame.check(self, head_lineno_map[frame.head])
            if ok:
                annotated_count += 1
            warnings += w
        return len(head_frame_map), annotated_count, warnings

    def write(self, io: TextIO=sys.stdout):
        print(self.syntax.conll(), file=io, end='')
        for frame in self.frames:
            if isinstance(frame, Frame):
                blocks.write(frame.to_block(), io=io)
            else:
                blocks.write(frame, io=io)

def read(io: TextIO=sys.stdin) -> Iterable[Sentence]:
    current_sentence = None
    lineno = 1
    for block in blocks.read(io):
        try:
            new_sentence = Sentence(
                pyconll.load_from_string('\n'.join(block)),
                lineno,
            )
            if current_sentence:
                yield current_sentence
            current_sentence = new_sentence
        except ParseError:
            current_sentence.add_frame(block, lineno)
        lineno += len(block) + 1
    if current_sentence:
        yield current_sentence
