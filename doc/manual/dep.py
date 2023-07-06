#!/usr/bin/env python3


from collections import defaultdict
from dataclasses import dataclass
import re
import sys
from typing import Iterable


BS = '\\'
TOKSEP = ' \\& '


@dataclass
class Token:
    form: str
    prednum: int
    deprels: dict[int, str]


def tokenize(depstr: str) -> Iterable[Token]:
    while depstr:
        match = re.match(r'\s*(\**)([^*_\s]+)(\**)\s*', depstr)
        prednum = len(match.group(1))
        form = match.group(2)
        assert len(match.group(3)) == prednum
        depstr = depstr[match.end():]
        deprels = {}
        while depstr.startswith('_'):
            print('dssw_', file=sys.stderr)
            match = re.match('(_+)([^_\s]+)\s*', depstr)
            dprednum = len(match.group(1))
            ddeprel = match.group(2)
            deprels[dprednum] = ddeprel
            depstr = depstr[match.end():]
        yield Token(form, prednum, deprels)


def clean(token):
    if token.startswith('*') and token.endswith('*'):
        token = token[1:-1]
        if '_' in token:
            word, frame = token.split('_', 1)
            frame = frame.replace('_', '\\_')
            return f'{word}$_\\text{{\\smaller {frame}}}$'
        return token
    return token.rsplit('_', 1)[0]


def render(depstr: str) -> str:
    """Renders a local dependency tree using LaTeX.

    tokens are the tokens of a sentence with markup encoding a local
    dependency tree (only one head), like:

    Kim_nsubj *loves* Sandy_dobj

    Returns a rendering of this local tree in LaTeX code, using
    tikz-dependency.
    """
    # Front matter
    print(depstr, file=sys.stderr)
    tokens = list(tokenize(depstr))
    print(tokens, file=sys.stderr)
    result = ''
    result += r'\raisebox{-.5\baselineskip}{'
    result += r'\begin{dependency}[label style={font=\sffamily}]'
    result += r'\begin{deptext}'
    result += r' \& '.join(t.form for t in tokens)
    result += r' \\'
    result += r'\end{deptext}'
    # Map predicate numbers to head indices
    prednum_head_map = {}
    for h, token in enumerate(tokens):
        if token.prednum:
            prednum_head_map[token.prednum] = h
    # Collect edges
    edges = []
    for i, token in enumerate(tokens):
        for h, rel in token.deprels.items():
            h = prednum_head_map[h]
            edges.append((h + 1, i + 1, rel))
    # Sort edges by length
    edges.sort(key=lambda e: abs(e[1] - e[0]))
    # Determine edge height
    profile = defaultdict(int) # edge height per position
    edge_height_map = {}
    for h, i, rel in edges:
        rng = range(min(h, i), max(h, i))
        height = max(profile[j] for j in rng) + 1
        for j in rng:
            profile[j] = height
        edge_height_map[(h, i, rel)] = height
    # Render edges (long ones first so short ones cover them)
    for h, i, rel in reversed(edges):
        height = edge_height_map[(h, i, rel)]
        result += r'\depedge[edge height='
        result += str(height)
        result += r'\baselineskip]{'
        result += str(h)
        result += r'}{'
        result += str(i)
        result += '}{'
        result += rel
        result += '}'
    # Back matter
    result += r'\end{dependency}'
    result += r'}'
    return result


if __name__ == '__main__':
    tex = sys.stdin.read()
    tex = re.sub(r'\\dep\{([^}]*)\}', lambda m: render(m.group(1)), tex)
    sys.stdout.write(tex)
