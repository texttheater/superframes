#!/usr/bin/env python3


"""
Lints and checks a CUSF file.
"""


import argparse
import logging
import shutil
import tempfile


import cusf


if __name__ == '__main__':
    # Process command line
    logging.basicConfig(
        format='%(levelname)s %(message)s',
        level=logging.INFO,
    )
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('--warn-incomplete',
            action=argparse.BooleanOptionalAction, default=True)
    arg_parser.add_argument('file')
    args = arg_parser.parse_args()
    # Make backup file
    backup_file = args.file + '~'
    shutil.copyfile(args.file, backup_file)
    # Read file
    with open(args.file) as f:
        sentences = [s for s in cusf.read(f)]
    # Add missing frames
    with tempfile.NamedTemporaryFile('w', delete=False) as f:
        for sentence in sentences:
            sentence.fill()
            sentence.write(f)
        f.close()
        shutil.move(f.name, args.file)
    # Read file again
    with open(args.file) as f:
        sentences = [s for s in cusf.read(f)]
    # Run checks and emit warnings
    predicate_count = 0
    annotated_count = 0
    for sentence in sentences:
        p, a, w = sentence.check()
        if args.warn_incomplete and a > 0 and a < p and w == 0:
            logging.warning('sent %s line %s annotation of sentence not complete',
                    sentence.syntax[0].id, sentence.lineno)
        predicate_count += p
        annotated_count += a
    logging.info('%s/%s predicates annotated', annotated_count, predicate_count)
