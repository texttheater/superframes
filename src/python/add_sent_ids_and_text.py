#!/usr/bin/env python3


import sys


import blocks


if __name__ == '__main__':
    for sent_id, block in enumerate(blocks.read(sys.stdin), start=1):
        print('# sent_id =', sent_id)
        text = ' '.join(l.split()[1] for l in block)
        print('# text =', text)
        blocks.write(block, sys.stdout)
