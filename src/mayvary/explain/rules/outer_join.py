"""A (+) outer join that came out as an inner join.

Fires when the Oracle query has (+) and Oracle returns extra rows with NULLs
that Postgres doesn't. A correct LEFT JOIN with a different bug looks the same.
"""

from sqlglot import exp

from mayvary.explain.core import QUERY_AND_DATA, Context, Explanation, plural

RULE = "outer-join-plus"
TITLE = "The (+) outer join became an inner join"
SOURCES = ("https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Joins.html",)


def check(ctx: Context) -> Explanation | None:
    marked = [c for c in ctx.tree.find_all(exp.Column) if c.args.get("join_mark")]
    if not marked or not ctx.only_oracle or ctx.only_postgres:
        return None
    if not all(None in row for row in ctx.only_oracle):
        return None
    columns = ", ".join(sorted({c.sql(dialect="oracle") for c in marked}))
    return Explanation(
        rule=RULE,
        title=TITLE,
        confidence=QUERY_AND_DATA,
        evidence=f"{plural(len(ctx.only_oracle), 'row')} only on Oracle, each with NULLs, "
        f"and the query outer-joins on {columns}",
        fix="Rewrite it as LEFT JOIN and move every (+) condition into the ON clause. "
        "A (+) that's dropped, or left in WHERE, makes it an inner join.",
        sources=SOURCES,
    )
