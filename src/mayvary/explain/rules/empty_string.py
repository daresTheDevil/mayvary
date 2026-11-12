"""Oracle stores and compares '' as NULL. Postgres keeps '' as a value.

Two shapes show up: a cell that's NULL on Oracle and '' on Postgres, and rows
that only Oracle returns because a string function gave '' and Oracle read it
as NULL. Only string functions sqlglot names are checked, so others slip past.
"""

from sqlglot import exp

from mayvary.explain.core import (
    DATA_ONLY,
    QUERY_AND_DATA,
    Context,
    Explanation,
    column_list,
    plural,
)

RULE = "empty-string-is-null"
TITLE = "Oracle treats '' as NULL"
SOURCES = ("https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Nulls.html",)
STRING_FUNCTIONS = (exp.Trim, exp.Substring, exp.Upper, exp.Lower, exp.DPipe)


def check(ctx: Context) -> Explanation | None:
    return null_vs_empty_cells(ctx) or blank_tested_as_null(ctx)


def null_vs_empty_cells(ctx: Context) -> Explanation | None:
    hits = [d for d in ctx.cell_diffs if d.oracle is None and d.postgres == ""]
    if not hits:
        return None
    confidence = QUERY_AND_DATA if has_empty_literal(ctx.tree) else DATA_ONLY
    return Explanation(
        rule=RULE,
        title=TITLE,
        confidence=confidence,
        evidence=f"{plural(len(hits), 'value')} NULL on Oracle and '' on Postgres ({column_list(hits)})",
        fix="Oracle can't return '', so a '' default like NVL(x, '') stays NULL. "
        "Wrap the Postgres expression in NULLIF(..., '') to match.",
        sources=SOURCES,
    )


def blank_tested_as_null(ctx: Context) -> Explanation | None:
    if not ctx.unpaired_oracle or ctx.unpaired_postgres:
        return None
    test = next(
        (i for i in ctx.tree.find_all(exp.Is) if is_null_test_on_string_function(i)),
        None,
    )
    if test is None:
        return None
    expr = test.this.sql(dialect="postgres")
    return Explanation(
        rule=RULE,
        title=TITLE,
        confidence=QUERY_AND_DATA,
        evidence=f"{plural(len(ctx.unpaired_oracle), 'row')} only on Oracle, and the query tests "
        f"{test.this.sql(dialect='oracle')} IS NULL. Where it gives '', Oracle reads NULL.",
        fix=f"On Postgres, test NULLIF({expr}, '') IS NULL.",
        sources=SOURCES,
    )


def is_null_test_on_string_function(node: exp.Is) -> bool:
    return isinstance(node.expression, exp.Null) and node.this.find(*STRING_FUNCTIONS) is not None


def has_empty_literal(tree: exp.Expression) -> bool:
    return any(lit.is_string and lit.this == "" for lit in tree.find_all(exp.Literal))
