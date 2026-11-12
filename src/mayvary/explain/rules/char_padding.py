"""CHAR padding survives concatenation on Oracle and is dropped on Postgres.

Matches values that are equal once spaces are removed and longer on Oracle.
Without the column types this can't tell CHAR from a value that changed its
spacing some other way, so it needs a concatenation in the query too.
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

RULE = "char-padding"
TITLE = "CHAR padding is kept by Oracle and dropped by Postgres"
SOURCES = (
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Concatenation-Operator.html",
    "https://www.postgresql.org/docs/current/datatype-character.html",
)


def check(ctx: Context) -> Explanation | None:
    if ctx.tree.find(exp.DPipe, exp.Concat) is None:
        return None
    hits = [d for d in ctx.cell_diffs if lost_padding(d.oracle, d.postgres)]
    if not hits:
        return None
    return Explanation(
        rule=RULE,
        title=TITLE,
        confidence=QUERY_AND_DATA,
        evidence=f"{plural(len(hits), 'value')} lost spaces on Postgres ({column_list(hits)}), "
        f"for example {first_example(hits)}",
        fix="Postgres trims char(n) when it casts to text. "
        "Use rpad(col, n) on Postgres to keep the padding, or rtrim on both sides.",
        sources=SOURCES,
    )


def lost_padding(oracle: object, postgres: object) -> bool:
    if not isinstance(oracle, str) or not isinstance(postgres, str):
        return False
    return len(oracle) > len(postgres) and oracle.replace(" ", "") == postgres.replace(" ", "")
