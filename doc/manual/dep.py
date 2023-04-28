#!/usr/bin/env python3


import sys


BS = '\\'
TOKSEP = ' \\& '


def escape(token):
    return token.replace('$', '\\$')


def clean(token):
    if token.startswith('_') and token.endswith('_'):
        return token[1:-1]
    return token.rsplit('_', 1)[0]


def dep(tokens):
    """Renders a local dependency tree using LaTeX.

    tokens are the tokens of a sentence with markup encoding a local
    dependency tree (only one head), like:

    Kim_nsubj *loves* Sandy_dobj

    Returns a rendering of this local tree in LaTeX code, using
    tikz-dependency.
    """
    result = ''
    pred_idx = -1
    for i, token in enumerate(tokens):
        if token.startswith('_') and token.endswith('_'):
            pred_idx = i
    if pred_idx == 1:
        raise ValueError('predicate not marked: {" ".join(tokens)}')
    result += f'''{BS}begin{{dependency}}
    {BS}begin{{deptext}}
        {TOKSEP.join(escape(clean(t)) for t in tokens)} {BS}{BS}
    {BS}end{{deptext}}'''
    height = 1
    for i in reversed(range(0, pred_idx)):
        if '_' in tokens[i]:
            rel = tokens[i].rsplit('_', 1)[1]
            result += f'    {BS}depedge[edge height={height}{BS}baselineskip]{{{pred_idx + 1}}}{{{i + 1}}}{{{rel}}}'
            height += 1
    height = 1
    for i in range(pred_idx + 1, len(tokens)):
        if '_' in tokens[i]:
            rel = tokens[i].rsplit('_', 1)[1]
            result += f'    {BS}depedge[edge height={height}{BS}baselineskip]{{{pred_idx + 1}}}{{{i + 1}}}{{{rel}}}'
            height += 1
    result += '\\end{dependency}'
    return result


if __name__ == '__main__':
    print(dep(sys.argv[1:]))
