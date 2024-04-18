import logging
import math
from numbers import Number
import re
import sys
from typing import Iterable, TextIO, Optional, Union


from pyconll.exception import ParseError
from pyconll.unit.sentence import Sentence as PyCoNLLSentence
import pyconll


import blocks
import labels


# FIXME word IDs are not always ints
FRAME_LINE = re.compile(r'\[(?P<label>[^]]*)] (?P<text>.*?) \((?P<head>\d+)\)(?: *# *(?P<comment>.*))?$')
ARG_DEPS = set(('nsubj', 'obj', 'iobj', 'csubj', 'ccomp', 'xcomp', 'obl',
        'advcl', 'advmod', 'nmod', 'appos', 'nummod', 'acl', 'amod',
        'compound', 'orphan'))
PRED_DEPS = ARG_DEPS | set(('root', 'conj', 'parataxis', 'list', 'reparandum',
        'dep', 'vocative', 'dislocated'))


def subtrees(tree: pyconll.tree.Tree) -> Iterable[pyconll.tree.Tree]:
    yield tree
    for child in tree:
        yield from subtrees(child)


def is_semantic_predicate(tree: pyconll.tree.Tree) -> bool:
    return tree.data.deprel.split(':')[0] in PRED_DEPS


def is_semantic_dependent(tree: pyconll.tree.Tree) -> bool:
    return tree.data.deprel.split(':')[0] in ARG_DEPS


def yld(tree: pyconll.tree.Tree) -> Iterable[pyconll.tree.Tree]:
    yield tree
    for child in tree:
        yield from yld(child)


def serialize_subtree(tree: pyconll.tree.Tree) -> str:
    nodes = sorted(yld(tree), key=lambda t: int(t.data.id))
    nodes = (t.data.form for t in nodes)
    return ' '.join(nodes)


class Arg:

    def __init__(self, head: str, text: str = '', label: str='', comment: str=''):
        self.head = head
        self.text = text
        self.label = label
        self.comment = comment

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
            comment:str ='', args: Optional[list[Arg]]=None):
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

    def check(self, sentid, lineno) -> bool:
        if not self.label:
            return False
        if not labels.check_frame_label(self.label):
            logging.warning('sent %s line %s unknown frame label: %s',
                    sentid, lineno, self.label)
            return False
        ok = True
        for i, arg in enumerate(self.args, start=lineno + 1):
            if not labels.check_dep_label(arg.label, self.label):
                logging.warning('sent %s line %s unknown dep label for %s: %s',
                        sentid, i, self.label, arg.label)
                ok = False
        return ok

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
        for child in tree:
            if is_semantic_dependent(child):
                frame.args.append(
                    Arg(child.data.id, serialize_subtree(child)),
                )
        return frame


"""Can't parse a frame? Represent it as a block."""
Frameish = Union[Frame, blocks.Block]


class Sentence:

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
        """Add missing frames"""
        if not all(isinstance(f, Frame) for f in self.frames):
            return
        cursor = 0 # index at which we insert the next missing frame
        for sentence in self.syntax:
            for tree in subtrees(sentence.to_tree()):
                if is_semantic_predicate(tree):
                    frame_already_present = False
                    for index, frame in enumerate(self.frames):
                        if frame.head == tree.data.id:
                            frame_already_present = True
                            cursor = index + 1
                            break
                    if not frame_already_present:
                        self.frames.insert(cursor, Frame.init_from_tree(tree))
                        cursor += 1

    def check(self) -> tuple[int, int]:
        frame_count = 0
        annotated_count = 0
        for lineno, frame in zip(self.frame_linenos, self.frames):
            if not isinstance(frame, Frame):
                logging.warning('sent %s line %s cannot parse frame %s',
                        self.syntax[0].id, lineno, repr('\n'.join(frame)))
                continue
            frame_count += 1
            if frame.check(self.syntax[0].id, lineno):
                annotated_count += 1
        return frame_count, annotated_count

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
