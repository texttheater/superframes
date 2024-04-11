#!/usr/bin/env python3


"""
Lints and checks a CUSF file.
"""


import argparse
import shutil


import cusf


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('file')
    args = arg_parser.parse_args()
    backup_file = args.file + '~'
    shutil.copyfile(args.file, backup_file)
    with open(args.file) as f:
        sentences = [s for s in cusf.read(f)]
    with open(args.file, 'w') as f:
        for sentence in sentences:
            sentence.fill()
            sentence.write(f)
