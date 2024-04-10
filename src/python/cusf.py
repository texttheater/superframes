import re
import sys
from typing import Iterable, TextIO, Optional, Union


from pyconll.exception import ParseError
from pyconll.unit.sentence import Sentence as PyCoNLLSentence
import pyconll


import blocks


FRAME_LINE = re.compile(r'\[(?P<label>[^]]*)] (?P<text>.*?) \((?P<head>\d+)\)$')


class Arg:

    def __init__(self, head: int, text: str = '', label: str=''):
        self.head = head
        self.text = text
        self.label = label

    def to_line(self) -> str:
        return f'[{self.label}] {self.text} ({self.head})'

    @staticmethod
    def from_line(line: str) -> 'Arg':
        m = FRAME_LINE.match(line)
        head = int(m.group('head'))
        text = m.group('text')
        label = m.group('label')
        arg = Arg(head, text, label)
        return arg


class Frame:

    def __init__(self, head: int, text: str = '', label: str='', args: Optional[dict]=None):
        self.head = head
        self.text = text
        self.label = label
        self.args = [] if args is None else args

    def to_block(self) -> blocks.Block:
        block = []
        block.append(f'[{self.label}] {self.text} ({self.head})')
        for arg in self.args:
            block.append(arg.to_line())
        return block

    @staticmethod
    def from_block(block: blocks.Block) -> 'Frame':
        m = FRAME_LINE.match(block[0])
        head = int(m.group('head'))
        text = m.group('text')
        label = m.group('label')
        frame = Frame(head, text, label)
        for line in block[1:]:
            frame.args.append(Arg.from_line(line))
        return frame


"""Can't parse a frame? Represent it as a block."""
Frameish = Union[Frame, blocks.Block]


class Sentence:

    def __init__(self, syntax: PyCoNLLSentence, frames: Optional[list[Frameish]]=None):
        self.syntax = syntax
        self.frames = [] if frames is None else frames

    def add_frame(self, block: blocks.Block):
        if self.frames is None:
            self.frames = []
        try:
            frame = Frame.from_block(block)
            self.frames.append(frame)
        except:
            self.frames.append(block)

    def write(self, io: TextIO=sys.stdout):
        print(self.syntax.conll(), file=io, end='')
        for frame in self.frames:
            if isinstance(frame, Frame):
                blocks.write(frame.to_block(), io=io)
            else:
                blocks.write(frame, io=io)


def read(io: TextIO=sys.stdin) -> Iterable[Sentence]:
    current_sentence = None
    for block in blocks.read(io):
        try:
            new_sentence = Sentence(
                pyconll.load_from_string('\n'.join(block)),
            )
            if current_sentence:
                yield current_sentence
            current_sentence = new_sentence
        except ParseError:
            current_sentence.add_frame(block)
    if current_sentence:
        yield current_sentence


if __name__ == '__main__':
    for sentence in read():
        sentence.write()
