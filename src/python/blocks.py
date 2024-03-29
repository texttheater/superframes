"""Utilities for working with files structured into blocks

A block is a contiguous sequence of nonempty lines. A block is terminated by
an empty line, meaning a line that contains only the end-of-line string. The
terminating empty line is optional at the end of the file. Two or more
consecutive empty lines mean one or more empty blocks. Blocks are represented
as lists of lines, with no line-terminating strings.
"""


import sys
from typing import Iterable, TextIO


Line = str
Block = list[Line]


def read(io: TextIO) -> Iterable[Block]:
    current_block: Block = []
    for line in io:
        line, = line.splitlines()
        if line:
            current_block.append(line)
        else:
            yield current_block
            current_block = []
    if current_block:
        yield current_block


def write(block: Block, io: TextIO=sys.stdout):
    for line in block:
        print(line, file=io)
    print(file=io)
