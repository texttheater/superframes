import blocks
from pyconll.exception import ParseError
from pyconll.unit.sentence import Sentence as PyCoNLLSentence
import pyconll
import sys
from typing import Iterable, TextIO


class Sentence:

    def __init__(self, sentence: PyCoNLLSentence):
        self.sentence = sentence
        self.frames = []

    def write(self, io: TextIO=sys.stdout):
        print(self.sentence.conll(), file=io, end='')
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
            current_sentence.frames.append(block)
    if current_sentence:
        yield current_sentence


if __name__ == '__main__':
    for sentence in read():
        sentence.write()
