from collections.abc import Callable
from dataclasses import dataclass

from sqlglot import exp

# How sure a rule is. A rule that only matches the data is a guess.
QUERY_AND_DATA = "query and data"
DATA_ONLY = "data only"

# Pairing rows is quadratic, so very large diffs skip the cell-level rules.
MAX_PAIRED_ROWS = 1_000


@dataclass(frozen=True)
class CellDiff:
    column: str
    oracle: object
    postgres: object


@dataclass(frozen=True)
class Context:
    tree: exp.Expression
    only_oracle: list[tuple]
    only_postgres: list[tuple]
    cell_diffs: list[CellDiff]
    unpaired_oracle: list[tuple]
    unpaired_postgres: list[tuple]


@dataclass(frozen=True)
class Explanation:
    rule: str
    title: str
    confidence: str
    evidence: str
    fix: str
    sources: tuple[str, ...]


Check = Callable[[Context], Explanation | None]


def build_context(
    tree: exp.Expression,
    columns: tuple[str, ...],
    only_oracle: list[tuple],
    only_postgres: list[tuple],
) -> Context:
    if len(only_oracle) > MAX_PAIRED_ROWS or len(only_postgres) > MAX_PAIRED_ROWS:
        return Context(tree, only_oracle, only_postgres, [], only_oracle, only_postgres)
    pairs, unpaired_oracle, unpaired_postgres = pair_rows(only_oracle, only_postgres)
    diffs = [d for o, p in pairs for d in cell_diffs(columns, o, p)]
    return Context(tree, only_oracle, only_postgres, diffs, unpaired_oracle, unpaired_postgres)


def pair_rows(
    only_oracle: list[tuple], only_postgres: list[tuple]
) -> tuple[list[tuple[tuple, tuple]], list[tuple], list[tuple]]:
    """Match each Oracle-only row to the Postgres-only row it shares the most cells with."""
    remaining = list(only_postgres)
    pairs, unpaired = [], []
    for row in only_oracle:
        best = max(range(len(remaining)), key=lambda i: shared(row, remaining[i]), default=None)
        if best is None or shared(row, remaining[best]) == 0:
            unpaired.append(row)
            continue
        pairs.append((row, remaining.pop(best)))
    return pairs, unpaired, remaining


def shared(a: tuple, b: tuple) -> int:
    return sum(x == y for x, y in zip(a, b, strict=True))


def cell_diffs(columns: tuple[str, ...], oracle: tuple, postgres: tuple) -> list[CellDiff]:
    return [
        CellDiff(name, o, p)
        for name, o, p in zip(columns, oracle, postgres, strict=True)
        if o != p
    ]


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def first_example(diffs: list[CellDiff]) -> str:
    d = diffs[0]
    return f"{d.oracle!r} vs {d.postgres!r}"


def column_list(diffs: list[CellDiff]) -> str:
    return ", ".join(sorted({d.column for d in diffs}))
