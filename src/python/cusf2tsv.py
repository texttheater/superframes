#!/usr/bin/env python3


"""Creates a .tsv annotation table from the CUSF format

The output contains a row for each edge with the following columns: sentence
ID, dependent token number, head token number, edge label, head label,
annotator.
"""

import argparse


import cusf


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('cusf', type=argparse.FileType())
    args = arg_parser.parse_args()
    seen = set()
    for sentence in cusf.read(args.cusf):
        sentence_id = sentence.syntax[0].id
        for frame in sentence.frames:
            if not isinstance(frame, cusf.Frame):
                continue
            head_id = frame.head
            if (sentence_id, head_id) in seen:
                continue # skip duplicate frame annotations
            if not frame.is_completely_annotated():
                continue
            ok, _ = frame.check(sentence, 0, True, True, True)
            if not ok:
                continue
            seen.add((sentence_id, head_id))
            head_label = frame.label
            for arg in frame.args:
                arg_id = arg.head
                arg_label = arg.label
                print(sentence_id, head_id, head_label, arg_id, arg_label, sep='\t')
