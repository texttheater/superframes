#!/usr/bin/env python3


"""Split a text file into 50-block chunks."""


import sys


import blocks


if __name__ == '__main__':
    try:
        _, name = sys.argv
    except ValueError:
        print('USAGE: python3 burst.py NAME', file=sys.stderr)
        sys.exit(1)
    base, ext = name.split('.', 1)
    with open(name) as f:
        blx = list(blocks.read(f))
    for chunk, offset in enumerate(range(0, len(blx), 50)):
        name = f'{base}.{chunk:02d}.{ext}'
        with open(name, 'w') as f:
            for block in blx[offset:offset + 50]:
                blocks.write(block, f)





