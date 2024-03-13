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
    subscript: str
    prednum: int
    deprels: dict[int, str]

    def render(self):
        if self.subscript:
            return self.form + r'$_\text{\textsf{' + self.subscript + r'}}$'
        return self.form


@dataclass(frozen=True)
class Edge:

    head: int
    dep: int
    rel: str

    def __len__(self):
        return abs(self.dep - self.head)

    def range(self):
        return range(min(self.head, self.dep), max(self.head, self.dep))


def tokenize(depstr: str) -> Iterable[Token]:
    while depstr:
        match = re.match(r'\s*(\**)([^*_\s]+)(\**)\s*', depstr)
        prednum = len(match.group(1))
        form = match.group(2)
        if '#' in form:
            form, subscript = form.split('#')
        else:
            subscript = None
        if len(match.group(3)) != prednum:
            raise ValueError('unbalanced asterisks: ' + match.group(0).strip())
        assert len(match.group(3)) == prednum
        depstr = depstr[match.end():]
        deprels = {}
        while depstr.startswith('_'):
            match = re.match(r'(_+)([^_\s]+)\s*', depstr)
            dprednum = len(match.group(1))
            ddeprel = match.group(2)
            deprels[dprednum] = ddeprel
            depstr = depstr[match.end():]
        yield Token(form, subscript, prednum, deprels)


def render(depstr: str) -> str:
    """Renders a local dependency tree using LaTeX.

    tokens are the tokens of a sentence with markup encoding a local
    dependency tree (only one head), like:

    Kim_nsubj *loves* Sandy_dobj

    Returns a rendering of this local tree in LaTeX code, using
    tikz-dependency.
    """
    # Front matter
    tokens = list(tokenize(depstr))
    result = ''
    result += r'\raisebox{-.5\baselineskip}{'
    result += r'\begin{dependency}[label style={font=\sffamily}]'
    result += r'\begin{deptext}'
    result += r' \& '.join(t.render() for t in tokens)
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
            edges.append(Edge(h + 1, i + 1, rel))
    # Sort edges by length
    edges.sort(key=len)
    # Determine edge height
    profile = defaultdict(int) # edge height per position
    edge_height_map = {}
    for edge in edges:
        height = max(profile[j] for j in edge.range()) + 1
        for j in edge.range():
            profile[j] = height
        edge_height_map[edge] = height
    # Render edges (long ones first so short ones cover them)
    for edge in reversed(edges):
        height = edge_height_map[edge]
        result += r'\depedge[edge height='
        result += str(height)
        result += r'\baselineskip]{'
        result += str(edge.head)
        result += r'}{'
        result += str(edge.dep)
        result += '}{'
        result += edge.rel
        result += '}'
    # Back matter
    result += r'\end{dependency}'
    result += r'}'
    return result


if __name__ == '__main__':
    tex = sys.stdin.read()
    tex = re.sub(r'\\dep\{([^}]*)\}', lambda m: render(m.group(1)), tex)
    sys.stdout.write(tex)
