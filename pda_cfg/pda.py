"""
Pushdown automata: simulation with instantaneous descriptions (IDs),
determinism check, and the standard CFG -> PDA construction.

An ID is (state, remaining input, stack) with the stack top on the LEFT,
written exactly as in the textbook: (q, w, Xα).
"""
from collections import deque

EPS = "ε"


class PDA:
    def __init__(self, name, states, input_alpha, stack_alpha, delta, start,
                 start_stack, final=None, accept_by="final", classify=None):
        """
        delta: dict {(state, input_symbol_or_EPS, stack_top): [(next_state, push_string), ...]}
               push_string is a tuple of stack symbols, leftmost = new top; () pops.
        accept_by: "final" or "empty"
        """
        self.name = name
        self.states = list(states)
        self.sigma = list(input_alpha)
        self.gamma = list(stack_alpha)
        self.delta = {k: [(q, tuple(p)) for q, p in v] for k, v in delta.items()}
        self.start = start
        self.Z0 = start_stack
        self.final = set(final or [])
        self.accept_by = accept_by
        self.classify = classify or (lambda t: t)

    # -------------------------------------------------------- determinism
    def nondeterministic_points(self):
        """List of (state, stack_top, reason) where the PDA has a choice."""
        bad = []
        for (q, a, X), moves in self.delta.items():
            if len(moves) > 1:
                bad.append((q, a, X, f"{len(moves)} moves on the same (q, a, X)"))
        for (q, a, X) in self.delta:
            if a == EPS:
                for b in self.sigma:
                    if (q, b, X) in self.delta:
                        bad.append((q, b, X, "ε-move and input move both possible"))
        return bad

    def is_deterministic(self):
        return not self.nondeterministic_points()

    # ---------------------------------------------------------- simulate
    def run(self, tokens, max_configs=200000):
        """Breadth-first search over IDs.
        Returns dict(accepted, path, explored) where path is the list of IDs
        on one accepting computation (or the longest one tried if rejected)."""
        toks = [self.classify(t) for t in tokens]
        n = len(toks)
        start = (self.start, 0, (self.Z0,))
        parent = {start: None}
        todo = deque([start])
        explored = 0
        best = start
        accept_id = None
        while todo and explored < max_configs:
            cfg = todo.popleft()
            explored += 1
            q, i, stack = cfg
            if i > best[1] or (i == best[1] and len(stack) < len(best[2])):
                best = cfg
            if self._accepting(cfg, n):
                accept_id = cfg
                break
            top = stack[0] if stack else None
            if top is None:
                continue
            moves = []
            if i < n:
                for nq, push in self.delta.get((q, toks[i], top), []):
                    moves.append((nq, i + 1, push))
            for nq, push in self.delta.get((q, EPS, top), []):
                moves.append((nq, i, push))
            for nq, ni, push in moves:
                new_stack = tuple(push) + stack[1:]
                if len(new_stack) > 2 * n + 4:      # stack can't usefully exceed this here
                    continue
                nxt = (nq, ni, new_stack)
                if nxt not in parent:
                    parent[nxt] = cfg
                    todo.append(nxt)
        end = accept_id or best
        path = []
        while end is not None:
            path.append(end)
            end = parent[end]
        path.reverse()
        pretty = [(q, " ".join(tokens[i:]) or EPS, "".join(s) or EPS) for q, i, s in path]
        return {"accepted": accept_id is not None, "path": pretty, "explored": explored}

    def _accepting(self, cfg, n):
        q, i, stack = cfg
        if i != n:
            return False
        if self.accept_by == "final":
            return q in self.final
        return len(stack) == 0

    def accepts(self, tokens):
        return self.run(tokens)["accepted"]

    # ------------------------------------------------------------- export
    def transitions_text(self):
        lines = []
        for (q, a, X), moves in self.delta.items():
            for nq, push in moves:
                lines.append(f"δ({q}, {a}, {X}) ∋ ({nq}, {''.join(push) or EPS})")
        return lines

    def to_dot(self):
        out = [f'digraph "{self.name}" {{', "  rankdir=LR;",
               '  node [shape=circle fontname="Helvetica" fontsize=12];',
               '  edge [fontname="Helvetica" fontsize=10];',
               "  __s [shape=point width=0.08];"]
        for q in self.states:
            shape = "doublecircle" if q in self.final else "circle"
            out.append(f'  "{q}" [shape={shape}];')
        out.append(f'  __s -> "{self.start}";')
        edges = {}
        for (q, a, X), moves in self.delta.items():
            for nq, push in moves:
                edges.setdefault((q, nq), []).append(f"{a}, {X} / {''.join(push) or EPS}")
        for (q, nq), labels in edges.items():
            lab = "\\l".join(labels) + "\\l"
            out.append(f'  "{q}" -> "{nq}" [label="{lab}"];')
        out.append("}")
        return "\n".join(out)


def cfg_to_pda(cfg, name=None):
    """Standard construction (Hopcroft-Motwani-Ullman Thm 6.13):
    one state q, accept by empty stack.
      for every A -> α :  δ(q, ε, A) ∋ (q, α)
      for every terminal a: δ(q, a, a) ∋ (q, ε)"""
    delta = {}
    for A, rhss in cfg.prods.items():
        for rhs in rhss:
            delta.setdefault(("q", EPS, A), []).append(("q", tuple(rhs)))
    for a in cfg.terminals:
        delta.setdefault(("q", a, a), []).append(("q", ()))
    return PDA(name or f"PDA for {cfg.name}", ["q"], sorted(cfg.terminals),
               sorted(cfg.terminals | cfg.nonterminals), delta, "q", cfg.start,
               accept_by="empty")
