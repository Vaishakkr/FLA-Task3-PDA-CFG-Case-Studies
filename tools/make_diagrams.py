"""Rebuild docs/diagrams (PDA state diagrams and parse trees). Needs Graphviz."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pda_cfg.cases import (BRACKETS, BRACKETS_AMBIGUOUS, BRACKETS_DPDA, EXPR,  # noqa: E402
                           EXPR_AMBIGUOUS, PAL_ALL, PAL_EVEN_NPDA, PAL_MARKED_DPDA)
from pda_cfg.grammar import tree_to_dot  # noqa: E402

OUT = ROOT / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def save(name, dot):
    (OUT / f"{name}.dot").write_text(dot)
    subprocess.run(["dot", "-Gdpi=170", "-Tpng", "-o", str(OUT / f"{name}.png")], input=dot.encode(), check=True)
    subprocess.run(["dot", "-Tsvg", "-o", str(OUT / f"{name}.svg")], input=dot.encode(), check=True)
    print("wrote", name)


save("pda_brackets", BRACKETS_DPDA.to_dot())
save("pda_palindrome_wcwr", PAL_MARKED_DPDA.to_dot())
save("pda_palindrome_wwr", PAL_EVEN_NPDA.to_dot())

w = EXPR.tokenize("id+id*id")
for k, d in enumerate(EXPR_AMBIGUOUS.leftmost_derivations(w), 1):
    save(f"tree_expr_ambiguous_{k}", tree_to_dot(EXPR_AMBIGUOUS.tree(d), f"Ambiguous grammar, tree {k}"))
save("tree_expr_precedence", tree_to_dot(EXPR.tree(EXPR.leftmost_derivations(w)[0]), "Precedence grammar (only tree)"))
for k, d in enumerate(BRACKETS_AMBIGUOUS.leftmost_derivations(list("()()()")), 1):
    save(f"tree_brackets_ambiguous_{k}", tree_to_dot(BRACKETS_AMBIGUOUS.tree(d), f"S → SS | (S) | (), tree {k}"))
save("tree_brackets_revised", tree_to_dot(BRACKETS.tree(BRACKETS.leftmost_derivations(list("()()()"))[0]), "Revised grammar (only tree)"))
save("tree_palindrome_abba", tree_to_dot(PAL_ALL.tree(PAL_ALL.leftmost_derivations(list("abba"))[0]), "abba"))
