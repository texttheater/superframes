import re
import sys
from typing import Iterable, TextIO, Optional, Union


from pyconll.exception import ParseError
from pyconll.unit.sentence import Sentence as PyCoNLLSentence
import pyconll


import blocks


FRAME_LINE = re.compile(r'\[(?P<label>[^]]*)] (?P<text>.*?) \((?P<tokid>\d+)\)$')


class Frame:

    def __init__(self, head: int, label: str='', args: Optional[dict]=None):
        self.head = head
        self.label = label
        self.args = [] if args is None else args

    @classmethod
    def from_block(block: blocks.Block) -> 'Frame':
        raise NotImplemented()


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
            frame = Frame.from_block(block, self.syntax)
            self.frames.append(frame)
        except:
            self.frames.append(block)

    def write(self, io: TextIO=sys.stdout):
        print(self.syntax.conll(), file=io, end='')
        for frame in self.frames:
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
