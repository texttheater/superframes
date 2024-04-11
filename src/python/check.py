#!/usr/bin/env python3


"""
Lints and checks a CUSF file.
"""


import argparse
import logging
import shutil


import cusf


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('file')
    args = arg_parser.parse_args()
    backup_file = args.file + '~'
    shutil.copyfile(args.file, backup_file)
    with open(args.file) as f:
        sentences = [s for s in cusf.read(f)]
    predicate_count = 0
    annotated_count = 0
    with open(args.file, 'w') as f:
        for sentence in sentences:
            sentence.fill()
            for frame in sentence.frames:
                if isinstance(frame, cusf.Frame):
                    predicate_count += 1
                    if frame.check():
                        annotated_count += 1
            sentence.write(f)
    logging.info('%s/%s predicates annotated', annotated_count, predicate_count)
