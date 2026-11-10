"""
Context-free grammars: leftmost derivations, parse trees, rightmost
derivations and a bounded ambiguity check.

Derivations are found by a plain backtracking search over leftmost
derivations. Two prunings keep it finite for the grammars in this repo:
  * the terminal prefix of a sentential form must match the input,
  * a sentential form may never need more terminals than the input has
    (each nonterminal is charged its minimum yield length).
The grammars used here have no unit cycles (A =>+ A without consuming
anything), which is what the search needs to terminate.
"""
import re
from collections import Counter

EPS = "ε"


class CFG:
    def __init__(self, name, start, productions, terminals):
        """productions: dict A -> list of right-hand sides, each a list of symbols
        ([] means ε). terminals: set of terminal symbols."""
        self.name = name
        self.start = start
        self.prods = {a: [list(r) for r in rhss] for a, rhss in productions.items()}
        self.terminals = set(terminals)
        self.nonterminals = set(self.prods)
        self._min = self._min_yield()

    # ----------------------------------------------------------- helpers
    def _min_yield(self):
        INF = 10 ** 9
        m = {a: INF for a in self.nonterminals}
        changed = True
        while changed:
            changed = False
            for a, rhss in self.prods.items():
                for r in rhss:
                    v = sum(1 if s in self.terminals else m[s] for s in r)
                    if v < m[a]:
                        m[a] = v
                        changed = True
        return m

    def cost(self, form):
        return sum(1 if s in self.terminals else self._min[s] for s in form)

    def tokenize(self, text):
        """Split text into terminals (longest match first, spaces ignored)."""
        terms = sorted(self.terminals, key=len, reverse=True)
        pat = re.compile("|".join(re.escape(t) for t in terms) + r"|\S")
        return [t for t in pat.findall(text)]

    def productions_text(self):
        lines = []
        for a in self.prods:
            alts = [" ".join(r) if r else EPS for r in self.prods[a]]
            lines.append(f"{a} → " + " | ".join(alts))
        return lines

    # ------------------------------------------------------- derivations
    def leftmost_derivations(self, tokens, limit=50, max_steps=400):
        """All leftmost derivations of tokens (up to `limit`).
        Each derivation = list of (nonterminal, rhs) applied in order."""
        n = len(tokens)
        found = []

        def search(form, applied, matched, steps):
            if len(found) >= limit or steps > max_steps:
                return
            # advance over the terminal prefix
            i = matched
            k = 0
            while k < len(form) and form[k] in self.terminals:
                if i >= n or tokens[i] != form[k]:
                    return
                i += 1
                k += 1
            rest = form[k:]
            if not rest:
                if i == n:
                    found.append(list(applied))
                return
            if i + self.cost(rest) > n:
                return
            A = rest[0]
            for rhs in self.prods[A]:
                applied.append((A, tuple(rhs)))
                search(list(rhs) + rest[1:], applied, i, steps + 1)
                applied.pop()

        search([self.start], [], 0, 0)
        return found

    def derives(self, tokens):
        return bool(self.leftmost_derivations(tokens, limit=1))

    def count_parse_trees(self, tokens, limit=50):
        # leftmost derivations are in 1-1 correspondence with parse trees
        return len(self.leftmost_derivations(tokens, limit=limit))

    def sentential_forms(self, derivation):
        """Replay a leftmost derivation; return the list of sentential forms."""
        form = [self.start]
        out = [list(form)]
        for A, rhs in derivation:
            j = next(i for i, s in enumerate(form) if s in self.nonterminals)
            assert form[j] == A
            form = form[:j] + list(rhs) + form[j + 1:]
            out.append(list(form))
        return out

    def tree(self, derivation):
        """Build a parse tree (nested tuples) from a leftmost derivation."""
        it = iter(derivation)

        def build(sym):
            if sym in self.terminals:
                return (sym, [])
            A, rhs = next(it)
            assert A == sym
            if not rhs:
                return (A, [(EPS, [])])
            return (A, [build(s) for s in rhs])
        return build(self.start)

    def rightmost_from_tree(self, tree):
        """Rightmost derivation (as sentential forms) of the same parse tree."""
        forms = [[tree]]
        # work with tree nodes; expand the rightmost unexpanded nonterminal node
        while True:
            cur = forms[-1]
            idx = None
            for i in range(len(cur) - 1, -1, -1):
                sym, kids = cur[i]
                if sym in self.nonterminals:
                    idx = i
                    break
            if idx is None:
                break
            sym, kids = cur[idx]
            kids = [] if (len(kids) == 1 and kids[0][0] == EPS) else kids
            forms.append(cur[:idx] + kids + cur[idx + 1:])
        return [[n[0] for n in f] for f in forms]

    def strings_up_to(self, max_len):
        """Every terminal string of length <= max_len the grammar generates
        (bounded breadth-first expansion of leftmost sentential forms)."""
        out = set()
        frontier = [[self.start]]
        seen = set()
        while frontier:
            nxt = []
            for form in frontier:
                key = tuple(form)
                if key in seen:
                    continue
                seen.add(key)
                if self.cost(form) > max_len:
                    continue
                j = next((i for i, s in enumerate(form) if s in self.nonterminals), None)
                if j is None:
                    out.add(tuple(form))
                    continue
                for rhs in self.prods[form[j]]:
                    nxt.append(form[:j] + list(rhs) + form[j + 1:])
            frontier = nxt
        return out

    def ambiguity_report(self, max_len):
        """Bounded ambiguity check: count parse trees of every generated
        string up to max_len tokens. (Ambiguity of CFGs is undecidable in
        general, so a bounded check is the best a tool can promise.)"""
        counts = Counter()
        worst = None
        for s in sorted(self.strings_up_to(max_len), key=lambda t: (len(t), t)):
            c = self.count_parse_trees(list(s), limit=50)
            counts[c] += 1
            if c > 1 and (worst is None or c > worst[1]):
                worst = (" ".join(s), c)
        return counts, worst


def tree_to_dot(tree, title="", highlight=None):
    lines = ["digraph T {", '  node [fontname="Helvetica" fontsize=12 shape=plaintext];',
             '  edge [arrowhead=none];']
    if title:
        lines.append(f'  labelloc="t"; label="{title}"; fontname="Helvetica"; fontsize=13;')
    counter = [0]

    def walk(node):
        sym, kids = node
        my = f"n{counter[0]}"
        counter[0] += 1
        is_leaf = not kids
        style = ' fontcolor="#1a5fb4"' if is_leaf else ""
        lines.append(f'  {my} [label="{sym}"{style}];')
        for k in kids:
            child = walk(k)
            lines.append(f"  {my} -> {child};")
        return my
    walk(tree)
    lines.append("}")
    return "\n".join(lines)


def evaluate_expr_tree(tree, env):
    """Evaluate an arithmetic parse tree (any of the grammars in cases.py)."""
    sym, kids = tree
    if not kids:
        return env.get(sym, sym)
    vals = [evaluate_expr_tree(k, env) for k in kids]
    syms = [k[0] for k in kids]
    if len(kids) == 1:
        return vals[0]
    if syms[0] == "(":
        return vals[1]
    if len(kids) == 3 and syms[1] == "+":
        return vals[0] + vals[2]
    if len(kids) == 3 and syms[1] == "*":
        return vals[0] * vals[2]
    raise ValueError(f"cannot evaluate node {sym} -> {syms}")
