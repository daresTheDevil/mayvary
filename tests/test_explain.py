import sqlglot

from mayvary.explain import explain
from mayvary.explain.core import DATA_ONLY, QUERY_AND_DATA, build_context, pair_rows


def rules(sql, columns, only_oracle, only_postgres):
    return [e.rule for e in explain(sql, columns, only_oracle, only_postgres)]


def test_pairs_rows_by_shared_cells():
    pairs, oracle_left, postgres_left = pair_rows([(1, "a"), (2, "b")], [(2, "x"), (1, "y")])
    assert pairs == [((1, "a"), (1, "y")), ((2, "b"), (2, "x"))]
    assert oracle_left == postgres_left == []


def test_rows_with_nothing_in_common_stay_unpaired():
    pairs, oracle_left, postgres_left = pair_rows([(1, "a")], [(2, "b")])
    assert pairs == []
    assert oracle_left == [(1, "a")]
    assert postgres_left == [(2, "b")]


def test_cell_diffs_name_the_column():
    tree = sqlglot.parse_one("SELECT id, v FROM t", read="oracle")
    ctx = build_context(tree, ("id", "v"), [(1, None)], [(1, "")])
    assert [(d.column, d.oracle, d.postgres) for d in ctx.cell_diffs] == [("v", None, "")]


def test_null_vs_empty_with_empty_literal_in_query():
    found = explain("SELECT id, NVL(m, '') AS m FROM t", ("id", "m"), [(1, None)], [(1, "")])
    assert [(e.rule, e.confidence) for e in found] == [("empty-string-is-null", QUERY_AND_DATA)]


def test_null_vs_empty_without_empty_literal_is_a_guess():
    found = explain("SELECT id, m FROM t", ("id", "m"), [(1, None)], [(1, "")])
    assert [(e.rule, e.confidence) for e in found] == [("empty-string-is-null", DATA_ONLY)]


def test_trim_is_null_explains_rows_only_on_oracle():
    found = explain("SELECT id FROM t WHERE TRIM(m) IS NULL", ("id",), [(3,)], [])
    assert [e.rule for e in found] == ["empty-string-is-null"]
    assert "NULLIF(TRIM(m), '') IS NULL" in found[0].fix


def test_plain_is_null_does_not_blame_empty_strings():
    assert rules("SELECT id FROM t WHERE m IS NULL", ("id",), [(3,)], []) == []


def test_char_padding_needs_a_concatenation():
    oracle, postgres = [(1, "ACTIVE    |")], [(1, "ACTIVE|")]
    assert rules("SELECT id, s || '|' AS l FROM t", ("id", "l"), oracle, postgres) == [
        "char-padding"
    ]
    assert rules("SELECT id, l FROM t", ("id", "l"), oracle, postgres) == []


def test_outer_join_plus_explains_missing_null_rows():
    sql = "SELECT c.id, o.id FROM c, o WHERE c.id = o.cid(+)"
    assert rules(sql, ("id", "id"), [(3, None)], []) == ["outer-join-plus"]


def test_outer_join_plus_ignores_rows_without_nulls():
    sql = "SELECT c.id, o.id FROM c, o WHERE c.id = o.cid(+)"
    assert rules(sql, ("id", "id"), [(3, 7)], []) == []


def test_ansi_join_is_not_blamed():
    sql = "SELECT c.id, o.id FROM c LEFT JOIN o ON c.id = o.cid"
    assert rules(sql, ("id", "id"), [(3, None)], []) == []


def test_substr_zero_explains_one_char_short():
    sql = "SELECT id, SUBSTR(s, 0, 3) AS p FROM t"
    assert rules(sql, ("id", "p"), [(1, "ABC")], [(1, "AB")]) == ["substr-position-zero"]


def test_substr_from_one_is_not_blamed():
    sql = "SELECT id, SUBSTR(s, 1, 3) AS p FROM t"
    assert rules(sql, ("id", "p"), [(1, "ABC")], [(1, "AB")]) == []


def test_unrelated_difference_stays_unexplained():
    assert rules("SELECT id, LENGTH(s) AS n FROM t", ("id", "n"), [(1, 10)], [(1, 6)]) == []
