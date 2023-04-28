#!/usr/bin/env python3


import re
import sys


BS = '\\'
TOKSEP = ' \\& '


def clean(token):
    if token.startswith('*') and token.endswith('*'):
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
        if token.startswith('*') and token.endswith('*'):
            pred_idx = i
    if pred_idx == -1:
        raise ValueError(f'predicate not marked: {repr(tokens)}')
    result += f'''{BS}raisebox{{-.5{BS}baselineskip}}{{{BS}begin{{dependency}}[label style={{font={BS}sffamily}}]
    {BS}begin{{deptext}}
        {TOKSEP.join(clean(t) for t in tokens)} {BS}{BS}
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
    result += f'{BS}end{{dependency}}}}'
    return result


if __name__ == '__main__':
    tex = sys.stdin.read()
    tex = re.sub(r'\\dep\{([^}]*)\}', lambda m: dep(m.group(1).split()), tex)
    sys.stdout.write(tex)
