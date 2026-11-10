"""
FIRST / FOLLOW sets, LL(1) table and a predictive (table-driven) parser.

A predictive parser is a deterministic PDA that also peeks at one input
token. Printing its stack after every move shows the 'stack moves' the
assignment asks for, without any guessing.
"""
from .grammar import EPS

END = "$"


def first_follow(cfg):
    first = {a: set() for a in cfg.nonterminals}

    def first_of(seq):
        out = set()
        for s in seq:
            f = {s} if s in cfg.terminals else first[s]
            out |= f - {EPS}
            if EPS not in f:
                return out
        out.add(EPS)
        return out

    changed = True
    while changed:
        changed = False
        for A, rhss in cfg.prods.items():
            for r in rhss:
                f = first_of(r)
                if not f <= first[A]:
                    first[A] |= f
                    changed = True
    follow = {a: set() for a in cfg.nonterminals}
    follow[cfg.start].add(END)
    changed = True
    while changed:
        changed = False
        for A, rhss in cfg.prods.items():
            for r in rhss:
                for i, B in enumerate(r):
                    if B not in cfg.nonterminals:
                        continue
                    f = first_of(r[i + 1:])
                    add = (f - {EPS}) | (follow[A] if EPS in f else set())
                    if not add <= follow[B]:
                        follow[B] |= add
                        changed = True
    return first, follow, first_of


def ll1_table(cfg):
    first, follow, first_of = first_follow(cfg)
    table, conflicts = {}, []
    for A, rhss in cfg.prods.items():
        for r in rhss:
            f = first_of(r)
            targets = (f - {EPS}) | (follow[A] if EPS in f else set())
            for a in targets:
                if (A, a) in table and table[(A, a)] != r:
                    conflicts.append((A, a))
                table[(A, a)] = r
    return table, conflicts, first, follow


def predictive_parse(cfg, tokens):
    """Returns (accepted, steps). steps rows: (stack, remaining input, action)."""
    table, conflicts, _, _ = ll1_table(cfg)
    assert not conflicts, f"grammar is not LL(1): {conflicts}"
    stack = [END, cfg.start]
    toks = list(tokens) + [END]
    i = 0
    steps = []

    def show():
        return "".join(reversed(stack)), " ".join(toks[i:])
    while True:
        top = stack[-1]
        a = toks[i]
        st, inp = show()
        if top == END and a == END:
            steps.append((st, inp, "accept"))
            return True, steps
        if top in cfg.terminals or top == END:
            if top == a:
                steps.append((st, inp, f"match {a}"))
                stack.pop()
                i += 1
                continue
            steps.append((st, inp, f"error: expected {top}, found {a}"))
            return False, steps
        rhs = table.get((top, a))
        if rhs is None:
            steps.append((st, inp, f"error: no rule for M[{top}, {a}]"))
            return False, steps
        steps.append((st, inp, f"{top} → {' '.join(rhs) if rhs else EPS}"))
        stack.pop()
        for s in reversed(rhs):
            stack.append(s)
