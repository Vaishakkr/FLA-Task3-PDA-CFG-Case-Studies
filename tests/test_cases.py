"""Tests: listed examples, CFG/PDA agreement, ambiguity claims, determinism claims."""
import random
import sys
from itertools import product
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pda_cfg.cases import (BRACKET_STRINGS, BRACKETS, BRACKETS_AMBIGUOUS,  # noqa: E402
                           BRACKETS_DPDA, CODE_SAMPLES, EXPR, EXPR_AMBIGUOUS,
                           EXPR_LL1, EXPR_PDA, EXPR_STRINGS, PAL_ALL, PAL_EVEN_NPDA,
                           PAL_MARKED_DPDA, PAL_STRINGS, bracket_tokens)
from pda_cfg.ll1 import ll1_table, predictive_parse  # noqa: E402


def balanced_ref(s):
    st = []
    pair = {")": "(", "]": "[", "}": "{"}
    for c in s:
        if c in "([{":
            st.append(c)
        elif not st or st.pop() != pair[c]:
            return False
    return not st and len(s) > 0


# ------------------------------------------------------------- brackets
@pytest.mark.parametrize("s", BRACKET_STRINGS["accept"])
def test_brackets_accept(s):
    assert BRACKETS.derives(list(s)) and BRACKETS_DPDA.accepts(list(s))


@pytest.mark.parametrize("s", BRACKET_STRINGS["reject"])
def test_brackets_reject(s):
    assert not BRACKETS.derives(list(s)) and not BRACKETS_DPDA.accepts(list(s))


def test_brackets_exhaustive_agreement():
    for n in range(0, 7):
        for t in product("()[]", repeat=n):
            s = "".join(t)
            ref = balanced_ref(s)
            assert BRACKETS_DPDA.accepts(list(s)) == ref, s
            assert BRACKETS.derives(list(s)) == ref, s
            assert BRACKETS_AMBIGUOUS.derives(list(s)) == ref, s


def test_code_checker():
    for s in CODE_SAMPLES["accept"]:
        assert BRACKETS_DPDA.accepts(bracket_tokens(s)), s
    for s in CODE_SAMPLES["reject"]:
        assert not BRACKETS_DPDA.accepts(bracket_tokens(s)), s


def test_bracket_ambiguity():
    assert BRACKETS_AMBIGUOUS.count_parse_trees(list("()()()")) == 2
    assert BRACKETS_AMBIGUOUS.count_parse_trees(list("()()()()")) == 5   # Catalan number C3
    assert BRACKETS.count_parse_trees(list("()()()()")) == 1


# ---------------------------------------------------------- expressions
@pytest.mark.parametrize("s", EXPR_STRINGS["accept"])
def test_expr_accept(s):
    t = EXPR.tokenize(s)
    assert EXPR.derives(t) and EXPR_PDA.accepts(t) and predictive_parse(EXPR_LL1, t)[0]


@pytest.mark.parametrize("s", EXPR_STRINGS["reject"])
def test_expr_reject(s):
    t = EXPR.tokenize(s)
    assert not EXPR.derives(t) and not EXPR_PDA.accepts(t) and not predictive_parse(EXPR_LL1, t)[0]


def test_expr_random_agreement_with_python_eval():
    """Random token strings: grammar says 'valid' exactly when Python can evaluate it."""
    rnd = random.Random(301)
    toks = ["id", "+", "*", "(", ")"]
    for _ in range(1500):
        t = [rnd.choice(toks) for _ in range(rnd.randint(1, 7))]
        try:
            eval(" ".join("1" if x == "id" else x for x in t).replace("( )", "(@)"))  # noqa: S307
            ok = True
        except Exception:
            ok = False
        # Python accepts unary +, e.g. '+1'; our language does not.
        if ok and (t[0] == "+" or any(a in "+*(" and b == "+" for a, b in zip(t, t[1:]))):
            ok = False
        assert EXPR.derives(t) == ok, t
        assert predictive_parse(EXPR_LL1, t)[0] == ok, t


def test_expr_ambiguity_and_fix():
    w = EXPR.tokenize("id+id*id")
    assert EXPR_AMBIGUOUS.count_parse_trees(w) == 2
    assert EXPR.count_parse_trees(w) == 1
    assert EXPR_LL1.count_parse_trees(w) == 1


def test_ll1_has_no_conflicts():
    assert ll1_table(EXPR_LL1)[1] == []


# ----------------------------------------------------------- palindromes
def test_palindromes():
    for s in PAL_STRINGS["wcwr"]["accept"]:
        assert PAL_MARKED_DPDA.accepts(list(s)), s
    for s in PAL_STRINGS["wcwr"]["reject"]:
        assert not PAL_MARKED_DPDA.accepts(list(s)), s
    for s in PAL_STRINGS["wwr"]["accept"]:
        assert PAL_EVEN_NPDA.accepts(list(s)), s
    for s in PAL_STRINGS["wwr"]["reject"]:
        assert not PAL_EVEN_NPDA.accepts(list(s)), s


def test_palindrome_exhaustive():
    for n in range(0, 9):
        for t in product("ab", repeat=n):
            s = "".join(t)
            assert PAL_ALL.derives(list(s)) == (s == s[::-1]), s
            assert PAL_EVEN_NPDA.accepts(list(s)) == (s == s[::-1] and n % 2 == 0), s


def test_determinism_claims():
    assert BRACKETS_DPDA.is_deterministic()
    assert PAL_MARKED_DPDA.is_deterministic()
    assert not PAL_EVEN_NPDA.is_deterministic()
    assert not EXPR_PDA.is_deterministic()
