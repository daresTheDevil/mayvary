from decimal import Decimal

from mayvary.compare import Outcome, Result, compare


def result(*rows, columns=("id", "v")):
    return Result(columns, tuple(rows))


def test_same_rows_in_any_order_are_same_without_order_by():
    verdict = compare(result((1, "a"), (2, "b")), result((2, "b"), (1, "a")), ordered=False)
    assert verdict.outcome is Outcome.SAME


def test_order_matters_with_order_by():
    verdict = compare(result((1, "a"), (2, "b")), result((2, "b"), (1, "a")), ordered=True)
    assert verdict.outcome is Outcome.DIFFERENT
    assert verdict.note == "same rows, different order"


def test_oracle_decimal_matches_postgres_int():
    verdict = compare(result((Decimal("1"), "a")), result((1, "a")), ordered=False)
    assert verdict.outcome is Outcome.SAME


def test_null_and_empty_string_differ():
    verdict = compare(result((1, None)), result((1, "")), ordered=False)
    assert verdict.outcome is Outcome.DIFFERENT
    assert verdict.only_oracle == [(Decimal(1), None)]
    assert verdict.only_postgres == [(Decimal(1), "")]


def test_duplicate_rows_count():
    verdict = compare(result((1, "a"), (1, "a")), result((1, "a")), ordered=False)
    assert verdict.outcome is Outcome.DIFFERENT
    assert verdict.only_oracle == [(Decimal(1), "a")]


def test_column_names_compare_case_insensitively():
    oracle = result((1, "a"), columns=("ID", "V"))
    verdict = compare(oracle, result((1, "a")), ordered=False)
    assert verdict.outcome is Outcome.SAME


def test_different_columns_are_different():
    postgres = result((1, "a"), columns=("id", "w"))
    verdict = compare(result((1, "a")), postgres, ordered=False)
    assert verdict.outcome is Outcome.DIFFERENT
    assert "columns differ" in verdict.note
