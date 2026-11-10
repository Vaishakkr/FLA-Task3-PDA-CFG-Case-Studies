"""
The three case studies.

  1. Balanced brackets  -> the core of every programming-language syntax checker
  2. Arithmetic expressions -> ambiguity, precedence, CFG->PDA, LL(1) parsing
  3. Palindromes        -> deterministic (w c wR) vs non-deterministic (w wR) PDA
"""
from .grammar import CFG
from .pda import EPS, PDA, cfg_to_pda

# ======================================================================
# 1. Balanced brackets ( ) [ ] { }
# ======================================================================
OPEN, CLOSE = "([{", ")]}"
MATCH = dict(zip(CLOSE, OPEN))
BR = set(OPEN + CLOSE)

BRACKETS_AMBIGUOUS = CFG(
    "Balanced brackets (ambiguous)", "S",
    {"S": [["S", "S"], ["(", "S", ")"], ["[", "S", "]"], ["{", "S", "}"],
           ["(", ")"], ["[", "]"], ["{", "}"]]},
    BR)

BRACKETS = CFG(
    "Balanced brackets (unambiguous)", "S",
    {"S": [["B", "S"], ["B"]],
     "B": [["(", "S", ")"], ["(", ")"], ["[", "S", "]"], ["[", "]"],
           ["{", "S", "}"], ["{", "}"]]},
    BR)


def _bracket_dpda():
    d = {}
    for o in OPEN:
        d[("q0", o, "Z0")] = [("q1", (o, "Z0"))]
        d[("qf", o, "Z0")] = [("q1", (o, "Z0"))]
        for X in OPEN:
            d[("q1", o, X)] = [("q1", (o, X))]
    for c in CLOSE:
        d[("q1", c, MATCH[c])] = [("q1", ())]
    d[("q1", EPS, "Z0")] = [("qf", ("Z0",))]
    return PDA("DPDA - balanced brackets", ["q0", "q1", "qf"], list(OPEN + CLOSE),
               ["Z0"] + list(OPEN), d, "q0", "Z0", final={"qf"})


BRACKETS_DPDA = _bracket_dpda()


def bracket_tokens(source_code):
    """'Lexer' for the syntax checker: keep only bracket characters and skip
    anything inside string literals. Everything else is irrelevant to the
    bracket structure."""
    out, in_str = [], None
    for ch in source_code:
        if in_str:
            if ch == in_str:
                in_str = None
            continue
        if ch in "\"'":
            in_str = ch
        elif ch in BR:
            out.append(ch)
    return out


CODE_SAMPLES = {
    "accept": [
        "if (a[i] > 0) { sum += f(a[i]); }",
        "int main() { int x[3] = {1, 2, 3}; return x[0]; }",
        "print(\"(not counted\")",
        "while (i < n) { if (v[i]) { c++; } i++; }",
        "matrix[r][c] = (a + b) * {k}[0];",
    ],
    "reject": [
        "if (a[i] > 0 { sum += 1; }",
        "int main() { return 0; ",
        "x = (a + b];",
        "for (i = 0; i < n; i++)) {}",
        "} else {",
        "arr[(i]) = 2;",
    ],
}

BRACKET_STRINGS = {
    "accept": ["()", "[]{}", "([]{})", "{[()()]}", "(((())))", "()[]{}([])"],
    "reject": ["(", ")(", "([)]", "(()", "{]}", "())(()"],
}

# ======================================================================
# 2. Arithmetic expressions over id, +, *, ( )
# ======================================================================
ARITH_T = {"id", "+", "*", "(", ")"}

EXPR_AMBIGUOUS = CFG(
    "Expressions (ambiguous)", "E",
    {"E": [["E", "+", "E"], ["E", "*", "E"], ["(", "E", ")"], ["id"]]},
    ARITH_T)

EXPR = CFG(
    "Expressions (precedence grammar)", "E",
    {"E": [["E", "+", "T"], ["T"]],
     "T": [["T", "*", "F"], ["F"]],
     "F": [["(", "E", ")"], ["id"]]},
    ARITH_T)

EXPR_LL1 = CFG(
    "Expressions (LL(1) form)", "E",
    {"E": [["T", "E'"]],
     "E'": [["+", "T", "E'"], []],
     "T": [["F", "T'"]],
     "T'": [["*", "F", "T'"], []],
     "F": [["(", "E", ")"], ["id"]]},
    ARITH_T)

EXPR_PDA = cfg_to_pda(EXPR, "PDA from precedence grammar (empty stack)")

EXPR_STRINGS = {
    "accept": ["id", "id+id*id", "(id+id)*id", "id*(id+id)*id", "((id))", "id+id+id"],
    "reject": ["", "id+", "+id", "id id", "(id+id", "id*)id(", "id+*id"],
}

# ======================================================================
# 3. Palindromes over {a, b}
# ======================================================================
PAL_ALL = CFG(
    "All palindromes over {a,b}", "S",
    {"S": [["a", "S", "a"], ["b", "S", "b"], ["a"], ["b"], []]},
    {"a", "b"})


def _pal_pda(marked):
    d = {}
    for x in "ab":
        for X in ["Z0", "a", "b"]:
            d[("q0", x, X)] = [("q0", (x, X))]
    if marked:   # w c wR : the centre is visible
        for X in ["Z0", "a", "b"]:
            d[("q0", "c", X)] = [("q1", (X,))]
    else:        # w wR : the PDA has to GUESS the centre
        for X in ["Z0", "a", "b"]:
            d[("q0", EPS, X)] = [("q1", (X,))]
    d[("q1", "a", "a")] = [("q1", ())]
    d[("q1", "b", "b")] = [("q1", ())]
    d[("q1", EPS, "Z0")] = [("q2", ("Z0",))]
    name = "DPDA - w c wR" if marked else "NPDA - w wR (even palindromes)"
    sig = ["a", "b", "c"] if marked else ["a", "b"]
    return PDA(name, ["q0", "q1", "q2"], sig, ["Z0", "a", "b"], d, "q0", "Z0",
               final={"q2"})


PAL_MARKED_DPDA = _pal_pda(True)
PAL_EVEN_NPDA = _pal_pda(False)

PAL_STRINGS = {
    "wcwr": {"accept": ["c", "aca", "abcba", "abbcbba", "babcbab", "aabacabaa"],
             "reject": ["", "ab", "abcab", "abcb", "acca", "abcbaa"]},
    "wwr": {"accept": ["", "aa", "abba", "baab", "abbbba", "aabbaabbaa"],
            "reject": ["a", "ab", "aba", "abab", "aabb", "abbaa"]},
    "all": {"accept": ["", "a", "aba", "abba", "babab", "aabaa"],
            "reject": ["ab", "aab", "abab", "abbab", "ba", "aabba"]},
}
