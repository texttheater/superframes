import collections
import logging
import math
import re
import sys
from typing import Dict, Iterable, List, Optional, Set, TextIO, Tuple, Union


from pyconll.exception import ParseError
from pyconll.unit.sentence import Sentence as PyCoNLLSentence
import pyconll


import blocks
import labels


# FIXME word IDs are not always ints
FRAME_LINE = re.compile(r'\[(?P<label>[^]]*)] (?P<text>.*?) \((?P<head>\d+)\)(?: *# *(?P<comment>.*))?$')
ARG_DEPS = set((
    'nsubj', 'obj', 'iobj', 'csubj', 'ccomp', 'xcomp', 'obl', 'advcl',
    'advmod', 'nmod', 'appos', 'nummod', 'acl', 'amod', 'compound', 'orphan',
    'det:poss',
    # SUD deps:
    'subj', 'udep', 'mod', 'comp',
))
PRED_DEPS = ARG_DEPS | set((
    'root', 'conj', 'parataxis', 'list', 'reparandum', 'dep', 'vocative',
    'dislocated',
))


def subtrees(tree: pyconll.tree.Tree) -> Iterable[pyconll.tree.Tree]:
    yield tree
    for child in tree:
        yield from subtrees(child)


def remove_features(deprel: str) -> str:
    return re.split(r'[:@]', deprel)[0]


def is_semantic_predicate(tree: pyconll.tree.Tree) -> bool:
    return any(tree.data.deprel.startswith(r) for r in PRED_DEPS) and tree.data.deprel != 'compound:prt'


def is_semantic_dependent(tree: pyconll.tree.Tree) -> bool:
    return any(tree.data.deprel.startswith(r) for r in ARG_DEPS)


def serialize_subtree(token_id: str, sentence: PyCoNLLSentence) -> str:
    for tree in subtrees(sentence.to_tree()):
        if tree.data.id == token_id:
            nodes = sorted(subtrees(tree), key=lambda t: int(t.data.id))
            nodes = [t.data.form for t in nodes]
            return ' '.join(str(n) for n in nodes)
    return ''


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

    def fill_args(self, args: Set[Tuple[str, str]]):
        # Remove args without annotation
        self.args = [a for a in self.args if a.label or a.comment]
        # Add expected args
        for head, text in args:
            if any(a.head == head for a in self.args):
                continue
            self.args.append(Arg(head, text, '', ''))

    def find_arg(self, label: str) -> Optional[Arg]:
        for arg in self.args:
            if arg.label == label:
                return arg
        return None

    def is_empty(self) -> bool:
        return not self.label and not self.comment and all(a.is_empty() for a in self.args)

    def check(self, sentence: 'Sentence', lineno: int,
            head_frame_map: Dict[int, 'Frame']) -> Tuple[bool, int]:
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
            # Check for wrong text
            arg_token = sentence.syntax[0][arg.head]
            if arg_token.head == self.head:
                expected_text = serialize_subtree(arg.head, sentence.syntax[0])
                if arg.text != expected_text:
                    logging.warning(
                        'sent %s line %s wrong text for subtree with root %s: '
                        'is "%s" but should be "%s"', sentence.syntax[0].id, i,
                        arg.head, arg.text, expected_text,
                    )
            else:
                expected_text = arg_token.form
                # We don't check in this case, for now.
            # Check for wrong dep label
            if not labels.check_dep_label(arg.label, self.label):
                logging.warning('sent %s line %s unknown dep label for %s: %s',
                        sentence.syntax[0].id, i, self.label, arg.label)
                ok = False
                warnings += 1
            # Check for missing depictive backlinks
            if arg.label == 'm-depictive':
                arg_heads = set(a.head for a in self.args)
                backlink_found = False
                for frame in sentence.frames:
                    if frame.head == arg.head:
                        for arg2 in frame.args:
                            if arg2.head in arg_heads:
                                backlink_found = True
                if not backlink_found:
                    logging.warning('sent %s line %s depictive has to share an argument with its parent frame',
                            sentence.syntax[0].id, i)
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
    def init_from_tree(tree: pyconll.tree.Tree) -> 'Frame':
        frame = Frame(tree.data.id, tree.data.form)
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

    def add_frame(self, block: blocks.Block, sentid: str, lineno: int):
        try:
            frame = Frame.from_block(block)
            self.frames.append(frame)
        except:
            self.frames.append(block)
        self.frame_linenos.append(lineno)

    def fill(self):
        """Add missing frames/args"""
        # Phase 0: ignore sentences with syntax errors
        if not all(isinstance(f, Frame) for f in self.frames):
            return
        # Phase 1: collect expected frame-arg links
        expected_links = collections.defaultdict(list)
        # Phase 1a: syntactic links
        for sentence in self.syntax:
            for tree in subtrees(sentence.to_tree()):
                if is_semantic_predicate(tree):
                    for child in tree:
                        if is_semantic_dependent(child):
                            expected_links[tree.data.id].append((
                                child.data.id,
                                serialize_subtree(child.data.id, sentence),
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
                    if initial_scene:
                        expected_links[initial_scene.head].append(protoarg)
                    if transitory_scene:
                        expected_links[transitory_scene.head].append(protoarg)
                    if scene:
                        expected_links[scene.head].append(protoarg)
                    if target_scene:
                        expected_links[target_scene.head].append(protoarg)
            for arg in frame.args:
                if arg.label == 'm-scene':
                    protoarg = (frame.head, frame.text)
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
                    if initial_content:
                        expected_links[initial_content.head].append(protoarg)
                    if transitory_content:
                        expected_links[transitory_content.head].append(protoarg)
                    if content:
                        expected_links[content.head].append(protoarg)
                    if target_content:
                        expected_links[target_content.head].append(protoarg)
            for arg in frame.args:
                if arg.label == 'm-content':
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

    def check(self) -> Tuple[int, int, int]:
        head_frame_map = {}
        head_lineno_map = {}
        for frame_lineno, frame in zip(self.frame_linenos, self.frames):
            if isinstance(frame, Frame):
                if frame.head in head_frame_map:
                    logging.warning(
                        'sent %s line %s duplicate frame for head word %s',
                        self.syntax[0].id, lineno, frame.head,
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
            ok, w = frame.check(self, head_lineno_map[frame.head], head_frame_map)
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
            current_sentence.add_frame(block, current_sentence.syntax[0].id, lineno)
        lineno += len(block) + 1
    if current_sentence:
        yield current_sentence
