"""
Terminal demo for the three case studies.

  python -m pda_cfg.cli brackets     balanced brackets / code syntax checker
  python -m pda_cfg.cli expr         arithmetic expressions (ambiguity, PDA, LL(1))
  python -m pda_cfg.cli palindrome   w c wR (DPDA) vs w wR (NPDA)
  python -m pda_cfg.cli ambiguity    bounded ambiguity check of every grammar
  python -m pda_cfg.cli all          everything above
"""
import sys

from .cases import (BRACKET_STRINGS, BRACKETS, BRACKETS_AMBIGUOUS, BRACKETS_DPDA,
                    CODE_SAMPLES, EXPR, EXPR_AMBIGUOUS, EXPR_LL1, EXPR_PDA,
                    EXPR_STRINGS, PAL_ALL, PAL_EVEN_NPDA, PAL_MARKED_DPDA,
                    PAL_STRINGS, bracket_tokens)
from .grammar import evaluate_expr_tree
from .ll1 import ll1_table, predictive_parse

C = sys.stdout.isatty() or "--color" in sys.argv
G, R, B, D, E = ("\033[32m", "\033[31m", "\033[1m", "\033[2m", "\033[0m") if C else ("",) * 5


def head(t):
    print(f"\n{B}{'=' * 72}\n{t}\n{'=' * 72}{E}")


def sub(t):
    print(f"\n{B}-- {t}{E}")


def verdict(x):
    return f"{G}ACCEPT{E}" if x else f"{R}REJECT{E}"


def ids(path, limit=None):
    rows = path if limit is None or len(path) <= limit else path[:limit // 2] + [("...", "...", "...")] + path[-limit // 2:]
    for k, (q, w, s) in enumerate(rows):
        arrow = "   " if k == 0 else " ⊢ "
        print(f"   {arrow}({q}, {w}, {s})")


def grammar(g):
    print(f"   {g.name}")
    for line in g.productions_text():
        print(f"     {line}")


def number_ids(tree, counter):
    sym, kids = tree
    if sym == "id" and not kids:
        counter[0] += 1
        return (f"x{counter[0]}", [])
    return (sym, [number_ids(k, counter) for k in kids])


# ---------------------------------------------------------------------------
def brackets():
    head("CASE STUDY 1 - Balanced brackets / programming-language syntax checker")
    sub("Grammars")
    grammar(BRACKETS_AMBIGUOUS)
    grammar(BRACKETS)
    sub("Ambiguity: number of parse trees")
    print(f"   {'string':<12}{'ambiguous G':>12}{'revised G':>12}")
    for s in ["()", "()()", "()()()", "()()()()", "([]){}()"]:
        print(f"   {s:<12}{BRACKETS_AMBIGUOUS.count_parse_trees(list(s)):>12}"
              f"{BRACKETS.count_parse_trees(list(s)):>12}")
    sub("DPDA transitions (accept by final state qf)")
    for line in BRACKETS_DPDA.transitions_text():
        print("   " + line)
    print(f"   deterministic: {BRACKETS_DPDA.is_deterministic()}")
    for s in ["{[()]}", "([)]"]:
        r = BRACKETS_DPDA.run(list(s))
        sub(f"Stack moves on {s}  ->  {verdict(r['accepted'])}")
        ids(r["path"])
    sub("Test strings")
    for s in BRACKET_STRINGS["accept"] + BRACKET_STRINGS["reject"]:
        t = list(s)
        print(f"   {s:<14} CFG: {verdict(BRACKETS.derives(t))}   DPDA: {verdict(BRACKETS_DPDA.accepts(t))}")
    sub("Syntax checker on code fragments (brackets extracted by a tiny lexer)")
    for s in CODE_SAMPLES["accept"] + CODE_SAMPLES["reject"]:
        toks = bracket_tokens(s)
        print(f"   {verdict(BRACKETS_DPDA.accepts(toks))}  {s:<52} {D}{''.join(toks)}{E}")


def expr():
    head("CASE STUDY 2 - Arithmetic expression validation")
    sub("Grammars")
    grammar(EXPR_AMBIGUOUS)
    grammar(EXPR)
    grammar(EXPR_LL1)
    w = EXPR.tokenize("id+id*id")
    sub("Ambiguity of E → E+E | E*E | (E) | id on  id + id * id")
    lmds = EXPR_AMBIGUOUS.leftmost_derivations(w)
    for k, d in enumerate(lmds, 1):
        forms = EXPR_AMBIGUOUS.sentential_forms(d)
        print(f"   LMD {k}: " + " ⇒ ".join("".join(f) for f in forms))
        tree = number_ids(EXPR_AMBIGUOUS.tree(d), [0])
        val = evaluate_expr_tree(tree, {"x1": 2, "x2": 3, "x3": 4})
        print(f"          with x1=2, x2=3, x3=4 this tree computes {B}{val}{E}")
    print("   -> two parse trees, two different values: the grammar is ambiguous.")
    sub("Revised precedence grammar on the same string")
    d = EXPR.leftmost_derivations(w)
    print(f"   parse trees: {len(d)}")
    print("   LMD: " + " ⇒ ".join("".join(f) for f in EXPR.sentential_forms(d[0])))
    rmd = EXPR.rightmost_from_tree(EXPR.tree(d[0]))
    print("   RMD: " + " ⇒ ".join("".join(f) for f in rmd))
    print(f"   value: {evaluate_expr_tree(number_ids(EXPR.tree(d[0]), [0]), {'x1': 2, 'x2': 3, 'x3': 4})} (correct, * binds tighter)")
    sub("PDA obtained from the precedence grammar (CFG -> PDA construction)")
    for line in EXPR_PDA.transitions_text():
        print("   " + line)
    print(f"   deterministic: {EXPR_PDA.is_deterministic()}  "
          f"({len(EXPR_PDA.nondeterministic_points())} choice points)")
    r = EXPR_PDA.run(w)
    sub(f"Accepting computation of the PDA on id+id*id  ->  {verdict(r['accepted'])}")
    ids(r["path"])
    print(f"   configurations explored by breadth-first search: {r['explored']}")
    table, conflicts, first, follow = ll1_table(EXPR_LL1)
    sub("LL(1) form: FIRST / FOLLOW")
    for A in EXPR_LL1.prods:
        print(f"   FIRST({A}) = {{{', '.join(sorted(first[A]))}}}   FOLLOW({A}) = {{{', '.join(sorted(follow[A]))}}}")
    print(f"   LL(1) conflicts: {len(conflicts)} -> deterministic parsing with one-token look-ahead")
    ok, steps = predictive_parse(EXPR_LL1, w)
    sub(f"Predictive parser stack moves on id+id*id  ->  {verdict(ok)}")
    print(f"   {'stack (top at left)':<22}{'input':<18}action")
    for st, inp, act in steps:
        print(f"   {st:<22}{inp:<18}{act}")
    sub("Test strings")
    print(f"   {'input':<16}{'CFG':<9}{'PDA':<9}{'LL(1)':<9}{'trees in ambiguous G'}")
    for s in EXPR_STRINGS["accept"] + EXPR_STRINGS["reject"]:
        t = EXPR.tokenize(s)
        print(f"   {repr(s) if not s else s:<16}{verdict(EXPR.derives(t)):<{9 + len(G + E)}}"
              f"{verdict(EXPR_PDA.accepts(t)):<{9 + len(G + E)}}"
              f"{verdict(predictive_parse(EXPR_LL1, t)[0]):<{9 + len(G + E)}}"
              f"{EXPR_AMBIGUOUS.count_parse_trees(t)}")


def palindrome():
    head("CASE STUDY 3 - Palindrome checker")
    grammar(PAL_ALL)
    d = PAL_ALL.leftmost_derivations(list("abba"))[0]
    print("   derivation of abba: " + " ⇒ ".join("".join(f) or "ε" for f in PAL_ALL.sentential_forms(d)))
    d = PAL_ALL.leftmost_derivations(list("babab"))[0]
    print("   derivation of babab: " + " ⇒ ".join("".join(f) or "ε" for f in PAL_ALL.sentential_forms(d)))
    for pda in (PAL_MARKED_DPDA, PAL_EVEN_NPDA):
        sub(f"{pda.name}")
        for line in pda.transitions_text():
            print("   " + line)
        print(f"   deterministic: {pda.is_deterministic()}")
        for p in pda.nondeterministic_points()[:3]:
            print(f"   {D}choice at ({p[0]}, {p[1]}, {p[2]}): {p[3]}{E}")
    r = PAL_MARKED_DPDA.run(list("abcba"))
    sub(f"DPDA on abcba -> {verdict(r['accepted'])}")
    ids(r["path"])
    r = PAL_EVEN_NPDA.run(list("abba"))
    sub(f"NPDA on abba (accepting branch) -> {verdict(r['accepted'])}")
    ids(r["path"])
    sub("Cost of guessing the centre: configurations explored")
    print(f"   {'n':>4}{'w c wR (DPDA)':>16}{'w wR (NPDA)':>16}")
    for half in [2, 4, 8, 16, 32]:
        w = ("ab" * half)[:half]
        a = PAL_MARKED_DPDA.run(list(w + "c" + w[::-1]))["explored"]
        b = PAL_EVEN_NPDA.run(list(w + w[::-1]))["explored"]
        print(f"   {2 * half:>4}{a:>16}{b:>16}")
    sub("Test strings")
    for key, m in [("wcwr", PAL_MARKED_DPDA), ("wwr", PAL_EVEN_NPDA), ("all", None)]:
        for s in PAL_STRINGS[key]["accept"] + PAL_STRINGS[key]["reject"]:
            ok = m.accepts(list(s)) if m else PAL_ALL.derives(list(s))
            print(f"   {key:<5} {repr(s) if not s else s:<12} {verdict(ok)}")


def ambiguity():
    head("Bounded ambiguity check (count parse trees of every short string)")
    for g, n in [(BRACKETS_AMBIGUOUS, 8), (BRACKETS, 8), (EXPR_AMBIGUOUS, 7),
                 (EXPR, 7), (EXPR_LL1, 7), (PAL_ALL, 8)]:
        counts, worst = g.ambiguity_report(n)
        total = sum(counts.values())
        amb = sum(v for k, v in counts.items() if k > 1)
        msg = f"{R}AMBIGUOUS{E} e.g. '{worst[0]}' has {worst[1]} trees" if worst else f"{G}no ambiguity found{E}"
        print(f"   {g.name:<36} strings ≤{n}: {total:>4}   with >1 tree: {amb:>4}   {msg}")
    print(f"   {D}(CFG ambiguity is undecidable in general; this is evidence, not a proof){E}")


def main(argv):
    args = [a for a in argv if a != "--color"] or ["all"]
    jobs = {"brackets": brackets, "expr": expr, "palindrome": palindrome, "ambiguity": ambiguity}
    if args[0] == "all":
        for f in jobs.values():
            f()
        return 0
    if args[0] in jobs:
        jobs[args[0]]()
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
