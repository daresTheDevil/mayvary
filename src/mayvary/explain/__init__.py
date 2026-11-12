import sqlglot

from mayvary.explain.core import Check, Explanation, build_context
from mayvary.explain.rules import char_padding, empty_string, outer_join, substr_zero

RULES: tuple[Check, ...] = (
    empty_string.check,
    char_padding.check,
    outer_join.check,
    substr_zero.check,
)


def explain(
    oracle_sql: str,
    columns: tuple[str, ...],
    only_oracle: list[tuple],
    only_postgres: list[tuple],
) -> list[Explanation]:
    tree = sqlglot.parse_one(oracle_sql, read="oracle")
    ctx = build_context(tree, columns, only_oracle, only_postgres)
    return [found for rule in RULES if (found := rule(ctx)) is not None]


__all__ = ["Explanation", "explain"]
