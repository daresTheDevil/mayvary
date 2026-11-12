import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg

from mayvary.cases import Case, load_cases
from mayvary.compare import Outcome, Verdict, compare
from mayvary.explain import Explanation, explain
from mayvary.run import (
    Limits,
    connect_oracle,
    connect_postgres,
    fetch_oracle,
    fetch_postgres,
)
from mayvary.translate import has_top_level_order_by, to_postgres

SHOWN_ROWS = 5


@dataclass(frozen=True)
class Checked:
    case: Case
    postgres_sql: str
    translated: bool
    warnings: list[str]
    verdict: Verdict
    explanations: list[Explanation]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    limits = Limits(args.timeout, args.max_rows)
    cases = load_cases(args.cases)
    with (
        connect_oracle(args.oracle, limits) as ora,
        connect_postgres(args.postgres, limits) as pg,
    ):
        checked = [check(case, ora, pg, limits) for case in cases]
    for item in checked:
        print_checked(item)
    print_summary(checked)
    return 0 if all(c.verdict.outcome is Outcome.SAME for c in checked) else 1


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mayvary",
        description="Run each query on Oracle and Postgres and show where the answers differ.",
    )
    parser.add_argument("cases", type=Path, help="TOML file of [[case]] entries")
    parser.add_argument("--oracle", default=os.environ.get("MAYVARY_ORACLE"),
                        help="user/password@host:port/service (or MAYVARY_ORACLE)")
    parser.add_argument("--postgres", default=os.environ.get("MAYVARY_POSTGRES"),
                        help="libpq connection string (or MAYVARY_POSTGRES)")
    parser.add_argument("--timeout", type=int, default=30, help="seconds per query")
    parser.add_argument("--max-rows", type=int, default=10_000)
    args = parser.parse_args(argv)
    if not args.oracle or not args.postgres:
        parser.error("need --oracle and --postgres, or MAYVARY_ORACLE and MAYVARY_POSTGRES")
    return args


def check(case: Case, ora, pg, limits: Limits) -> Checked:
    translated = case.postgres is None
    translation = to_postgres(case.oracle) if translated else None
    postgres_sql = translation.sql if translation else case.postgres
    warnings = translation.warnings if translation else []

    oracle_result = fetch_oracle(ora, case.oracle, limits)
    try:
        postgres_result = fetch_postgres(pg, postgres_sql, limits)
    except psycopg.Error as error:
        verdict = Verdict(Outcome.POSTGRES_ERROR, note=str(error).strip())
        return Checked(case, postgres_sql, translated, warnings, verdict, [])

    ordered = has_top_level_order_by(case.oracle)
    verdict = compare(oracle_result, postgres_result, ordered)
    columns = tuple(name.lower() for name in oracle_result.columns)
    explanations = explain(case.oracle, columns, verdict.only_oracle, verdict.only_postgres)
    return Checked(case, postgres_sql, translated, warnings, verdict, explanations)


def print_checked(item: Checked) -> None:
    verdict = item.verdict
    source = "  (translated by sqlglot)" if item.translated else ""
    print(f"{verdict.outcome.value:<18} {item.case.name}{source}")
    if verdict.outcome is Outcome.SAME:
        return
    for warning in item.warnings:
        print(f"    sqlglot warned: {warning}")
    if verdict.note:
        print(f"    {verdict.note}")
    print_explanations(item)
    print_rows("only in Oracle", verdict.only_oracle)
    print_rows("only in Postgres", verdict.only_postgres)
    print(f"    postgres sql: {item.postgres_sql}")
    print()


def print_explanations(item: Checked) -> None:
    if item.verdict.outcome is not Outcome.DIFFERENT:
        return
    if not item.explanations:
        print("    cause: unexplained")
        return
    for e in item.explanations:
        print(f"    cause: {e.title} ({e.confidence}, rule {e.rule})")
        print(f"      seen: {e.evidence}")
        print(f"      fix:  {e.fix}")
        for source in e.sources:
            print(f"      see:  {source}")


def print_rows(label: str, rows: list[tuple]) -> None:
    if not rows:
        return
    print(f"    {label} ({len(rows)}):")
    for row in rows[:SHOWN_ROWS]:
        print(f"      {format_row(row)}")
    if len(rows) > SHOWN_ROWS:
        print(f"      ... {len(rows) - SHOWN_ROWS} more")


def format_row(row: tuple) -> str:
    return "(" + ", ".join(repr(v) if isinstance(v, str) else str(v) for v in row) + ")"


def print_summary(checked: list[Checked]) -> None:
    counts = {o: sum(c.verdict.outcome is o for c in checked) for o in Outcome}
    parts = [f"{n} {o.value.lower()}" for o, n in counts.items() if n]
    different = [c for c in checked if c.verdict.outcome is Outcome.DIFFERENT]
    if different:
        explained = sum(bool(c.explanations) for c in different)
        parts.append(f"{explained} of {len(different)} differences explained")
    print(f"{len(checked)} cases: " + ", ".join(parts))


if __name__ == "__main__":
    sys.exit(main())
