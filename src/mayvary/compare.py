from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


@dataclass(frozen=True)
class Result:
    columns: tuple[str, ...]
    rows: tuple[tuple, ...]


class Outcome(Enum):
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    POSTGRES_ERROR = "ERROR ON POSTGRES"


@dataclass(frozen=True)
class Verdict:
    outcome: Outcome
    only_oracle: list[tuple] = field(default_factory=list)
    only_postgres: list[tuple] = field(default_factory=list)
    note: str = ""


def normalize_value(value):
    # Oracle hands back NUMBER as Decimal, Postgres hands back bigint as int.
    # Both mean the same number, so compare them as one type.
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return Decimal(value)
    return value


def normalize(result: Result) -> Result:
    columns = tuple(name.lower() for name in result.columns)
    rows = tuple(tuple(normalize_value(v) for v in row) for row in result.rows)
    return Result(columns, rows)


def compare(oracle: Result, postgres: Result, ordered: bool) -> Verdict:
    oracle, postgres = normalize(oracle), normalize(postgres)

    if oracle.columns != postgres.columns:
        note = f"columns differ: {oracle.columns} vs {postgres.columns}"
        return Verdict(Outcome.DIFFERENT, note=note)

    only_oracle = list((Counter(oracle.rows) - Counter(postgres.rows)).elements())
    only_postgres = list((Counter(postgres.rows) - Counter(oracle.rows)).elements())

    if only_oracle or only_postgres:
        return Verdict(Outcome.DIFFERENT, only_oracle, only_postgres)

    if ordered and oracle.rows != postgres.rows:
        return Verdict(Outcome.DIFFERENT, note="same rows, different order")

    return Verdict(Outcome.SAME)
