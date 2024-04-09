#!/usr/bin/env python3


"""Converts CONLL-U input to the CUSF format

CUSF has additional blocks after each sentence, one for every predicate to be
annotated. The first line of each such block indicates the predicate, and the
following lines represents a list of its arguments (that may however be
incomplete and has to be completed by annotators, e.g., in the case of control
relations.
"""


# TODO: no complicated tree traversal rules, just treat every PNVAR as a
# predicate.


import sys
from typing import Iterable


import pyconll


ARG_DEPS = set(('nsubj', 'obj', 'iobj', 'csubj', 'ccomp', 'xcomp', 'obl',
        'advcl', 'advmod', 'nmod', 'appos', 'nummod', 'acl', 'amod',
        'compound', 'orphan'))
PRED_DEPS = ARG_DEPS | set(('root', 'conj', 'parataxis', 'list', 'reparandum',
        'dep', 'vocative', 'dislocated'))


def is_semantic_predicate(tree: pyconll.tree.Tree) -> bool:
    return tree.data.deprel.split(':')[0] in PRED_DEPS


def is_semantic_dependent(tree: pyconll.tree.Tree) -> bool:
    return tree.data.deprel.split(':')[0] in ARG_DEPS


def yld(tree: pyconll.tree.Tree) -> Iterable[pyconll.tree.Tree]:
    yield tree
    for child in tree:
        yield from yld(child)


def serialize_subtree(tree: pyconll.tree.Tree) -> str:
    nodes = sorted(yld(tree), key=lambda t: int(t.data.id))
    nodes = (t.data.form for t in nodes)
    return ' '.join(nodes) + f' ({tree.data.id})'


def print_frames(tree: pyconll.tree.Tree):
    if is_semantic_predicate(tree):
        print(f'[] {tree.data.form} ({tree.data.id})')
        for child in tree:
            if is_semantic_dependent(child):
                print(f'[] {serialize_subtree(child)}')
        print()
    for child in tree:
        print_frames(child)


if __name__ == '__main__':
    corpus = pyconll.load_from_resource(sys.stdin)
    for sentence in corpus:
        print(sentence.conll())
        print()
        tree = sentence.to_tree()
        print_frames(tree)
