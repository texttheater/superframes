#!/usr/bin/env python3


"""Computes agreement on edges between two annotators.

Only predicates fully annotated by both annotators are considered.

Annotators are counted as in agreement on an edge if they have at least one
label in common (multiple labels per annotator can come from
ambiguity/uncertainty/figurativity).
"""


import argparse
import collections
from typing import Dict, Iterable, List, Tuple


import cusf
import labels


def create_pred_edges_map(sentences: Iterable[cusf.Sentence]) -> \
        Dict[Tuple[str, str], Dict[str, str]]:
    result = {}
    for sentence in sentences:
        seen = set()
        for frame in sentence.frames:
            if not isinstance(frame, cusf.Frame):
                continue
            key = sentence.syntax[0].id, frame.head
            if key in result:
                continue # skip duplicate frame annotations
            if not frame.is_completely_annotated():
                continue
            ok, _ = frame.check(sentence, 0)
            if not ok:
                continue
            head_label_map = collections.defaultdict(str)
            result[key] = head_label_map
            for arg in frame.args:
                head_label_map[arg.head] = arg.label
    return result


def count_matches(head_label_map_1, head_label_map_2, simplify=False):
    edge_count = 0
    match_count = 0
    for head, label1 in head_label_map_1.items():
        parts1 = set(labels.split_label(label1))
        parts2 = set(labels.split_label(head_label_map_2[head]))
        if simplify:
            parts1 = set(labels.simplify(p) for p in parts1)
            parts2 = set(labels.simplify(p) for p in parts2)
        if parts1:
            edge_count += 1
        if parts1 & parts2:
            match_count += 1
    return edge_count, match_count


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('file1', type=argparse.FileType())
    arg_parser.add_argument('file2', type=argparse.FileType())
    arg_parser.add_argument('--ignore-preds', type=argparse.FileType())
    arg_parser.add_argument('--simplify', action='store_true')
    args = arg_parser.parse_args()
    map1 = create_pred_edges_map(cusf.read(args.file1))
    map2 = create_pred_edges_map(cusf.read(args.file2))
    if args.ignore_preds:
        ignore_map = create_pred_edges_map(cusf.read(args.ignore_preds))
    else:
        ignore_map = {}
    common_predicates = (set(map1.keys()) & set(map2.keys())) - set(ignore_map.keys())
    print(f'{len(common_predicates)} common predicates')
    total1 = 0
    match1 = 0
    total2 = 0
    match2 = 0
    for pred in common_predicates:
        head_label_map_1 = map1[pred]
        head_label_map_2 = map2[pred]
        edge_count, match_count = count_matches(head_label_map_1, head_label_map_2, args.simplify)
        total1 += edge_count
        match1 += match_count
        edge_count, match_count = count_matches(head_label_map_2, head_label_map_1, args.simplify)
        total2 += edge_count
        match2 += match_count
    print(f"{match1}/{total1} ({match1 / total1}) of annotators 1's edges matched by annotator 2")
    print(f"{match2}/{total2} ({match2 / total2}) of annotators 2's edges matched by annotator 1")
