#!/usr/bin/env python3


"""
Lints and checks a CUSF file.
"""


import argparse
import logging
import shutil


import cusf


if __name__ == '__main__':
    # Process command line
    logging.basicConfig(level=logging.INFO)
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('file')
    args = arg_parser.parse_args()
    # Make backup file
    backup_file = args.file + '~'
    shutil.copyfile(args.file, backup_file)
    # Read file
    with open(args.file) as f:
        sentences = [s for s in cusf.read(f)]
    # Add missing frames
    with open(args.file, 'w') as f:
        for sentence in sentences:
            sentence.fill()
            sentence.write(f)
    # Read file again
    with open(args.file) as f:
        sentences = [s for s in cusf.read(f)]
    # Run checks and emit warnings
    predicate_count = 0
    annotated_count = 0
    for sentence in sentences:
        p, a = sentence.check()
        predicate_count += p
        annotated_count += a
    logging.info('%s/%s predicates annotated', annotated_count, predicate_count)
