#!/usr/bin/env python3


"""Converts CONLL-U input to the CUSF format

CUSF has additional blocks after each sentence, one for every predicate to be
annotated. The first line of each such block indicates the predicate, and the
following lines represents a list of its arguments (that may however be
incomplete and has to be completed by annotators, e.g., in the case of control
relations.
"""


import sys


import pyconll


SEMDEPS = set(('nsubj', 'obj', 'iobj', 'csubj', 'ccomp', 'xcomp', 'obl',
        'advcl', 'advmod', 'nmod', 'appos', 'nummod', 'acl', 'amod',
        'compound'))


def hruid(token: pyconll.unit.token.Token) -> str:
    """Human-readable identifier"""
    return f'{token.id}_{token.form}'


def is_semdep(tree: pyconll.tree.Tree) -> bool:
    """Whether a node is a 'semantic dependency' of its parent"""
    return tree.data.deprel in SEMDEPS


def print_frames(tree: pyconll.tree.Tree):
    if any(is_semdep(c) for c in tree):
        print(hruid(tree.data) + ': ')
        for child in tree:
            if is_semdep(child):
                print(hruid(child.data) + ': ')
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
