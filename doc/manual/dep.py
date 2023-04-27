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


if __name__ == '__main__':
    tokens = sys.argv[1:]
    pred_idx = -1
    for i, token in enumerate(tokens):
        if token.startswith('_') and token.endswith('_'):
            pred_idx = i
    if pred_idx == 1:
        print(f'ERROR: predicate not marked: {" ".join(tokens)}',
                file=sys.stderr)
        sys.exit(1)
    print(f'''{BS}begin{{dependency}}
    {BS}begin{{deptext}}
        {TOKSEP.join(escape(clean(t)) for t in tokens)} {BS}{BS}
    {BS}end{{deptext}}''')
    height = 1
    for i in reversed(range(0, pred_idx)):
        if '_' in tokens[i]:
            rel = tokens[i].rsplit('_', 1)[1]
            print(f'    {BS}depedge[edge height={height}{BS}baselineskip]{{{pred_idx + 1}}}{{{i + 1}}}{{{rel}}}')
            height += 1
    height = 1
    for i in range(pred_idx + 1, len(tokens)):
        if '_' in tokens[i]:
            rel = tokens[i].rsplit('_', 1)[1]
            print(f'    {BS}depedge[edge height={height}{BS}baselineskip]{{{pred_idx + 1}}}{{{i + 1}}}{{{rel}}}')
            height += 1
    print('\\end{dependency}')
