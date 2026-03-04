#!/usr/bin/env python3


"""Creates a .tsv annotation table from the CUSF format

The output contains a row for each edge with the following columns: sentence
ID, dependent token number, head token number, edge label, head label,
annotator.
"""


import argparse
import json
import logging
import pathlib


import cusf


def zerobase(head):
    return str(int(head) - 1)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('cusf', nargs='*', type=argparse.FileType())
    args = arg_parser.parse_args()
    data = {}
    for f in args.cusf:
        path = pathlib.Path(f.name)
        annotator = path.stem
        for sentence in cusf.read(f):
            sentence_id = sentence.syntax[0].id
            if sentence_id not in data:
                data[sentence_id] = {}
            if annotator in data[sentence_id]:
                logging.warn(
                    'duplicate sentence %s for annotator %s',
                    sentence_id,
                    annotator,
                )
                continue
            sa_data = {'roles': {}, 'status': 1, 'comment': None}
            data[sentence_id][annotator] = sa_data
            for frame in sentence.frames:
                if not isinstance(frame, cusf.Frame):
                    continue
                head_id = frame.head
                if zerobase(head_id) in sa_data['roles']:
                    logging.warn(
                        'duplicate frame %s in sentence %s for annotator %s',
                        sentence_id,
                        head_id,
                        annotator,
                    )
                    continue
                if not frame.is_completely_annotated():
                    continue
                ok, _ = frame.check(sentence, 0, True, True, True)
                if not ok:
                    continue
                args = {}
                sa_data['roles'][zerobase(head_id)] = {'args': args, 'frame': frame.label}
                for arg in frame.args:
                    args[zerobase(arg.head)] = arg.label
    for sentence_id, sentence_data in data.items():
        print(sentence_id, json.dumps(sentence_data), sep='\t')
