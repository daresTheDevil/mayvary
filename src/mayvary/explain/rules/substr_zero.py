"""SUBSTR with start position 0.

Oracle treats 0 as 1. Postgres counts 0 as a position before the string, so
the result is one character short. Negative starts differ too, not covered yet.
"""

from sqlglot import exp

from mayvary.explain.core import (
    QUERY_AND_DATA,
    Context,
    Explanation,
    column_list,
    first_example,
    plural,
)

RULE = "substr-position-zero"
TITLE = "SUBSTR position 0 means 1 on Oracle only"
SOURCES = (
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/SUBSTR.html",
    "https://www.postgresql.org/docs/current/functions-string.html",
)


def check(ctx: Context) -> Explanation | None:
    if not any(starts_at_zero(s) for s in ctx.tree.find_all(exp.Substring)):
        return None
    hits = [d for d in ctx.cell_diffs if one_char_short(d.oracle, d.postgres)]
    if not hits:
        return None
    return Explanation(
        rule=RULE,
        title=TITLE,
        confidence=QUERY_AND_DATA,
        evidence=f"{plural(len(hits), 'value')} one character short on Postgres "
        f"({column_list(hits)}), for example {first_example(hits)}",
        fix="Start at 1. It means the same thing on Oracle and gives the full length on Postgres.",
        sources=SOURCES,
    )


def starts_at_zero(node: exp.Substring) -> bool:
    start = node.args.get("start")
    return isinstance(start, exp.Literal) and start.is_int and int(start.this) == 0


def one_char_short(oracle: object, postgres: object) -> bool:
    if not isinstance(oracle, str) or not isinstance(postgres, str):
        return False
    return len(postgres) == len(oracle) - 1 and oracle.startswith(postgres)
