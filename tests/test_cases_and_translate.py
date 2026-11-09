import pytest

from mayvary.cases import CaseFileError, load_cases
from mayvary.translate import has_top_level_order_by, to_postgres


def write(tmp_path, text):
    path = tmp_path / "cases.toml"
    path.write_text(text)
    return path


def test_loads_case_without_postgres_sql(tmp_path):
    cases = load_cases(write(tmp_path, '[[case]]\nname = "a"\noracle = "SELECT 1 FROM dual"\n'))
    assert cases[0].postgres is None


def test_rejects_unknown_keys(tmp_path):
    path = write(tmp_path, '[[case]]\nname = "a"\noracle = "SELECT 1"\nbinds = 1\n')
    with pytest.raises(CaseFileError, match="unknown keys"):
        load_cases(path)


def test_rejects_missing_oracle_sql(tmp_path):
    with pytest.raises(CaseFileError, match="'oracle' is required"):
        load_cases(write(tmp_path, '[[case]]\nname = "a"\n'))


def test_rejects_empty_file(tmp_path):
    with pytest.raises(CaseFileError, match="no \\[\\[case\\]\\]"):
        load_cases(write(tmp_path, ""))


def test_keeps_sqlglot_warning_for_dropped_outer_join():
    translation = to_postgres("SELECT a.x FROM a, b WHERE a.id = b.id(+)")
    assert any("(+)" in w for w in translation.warnings)


def test_order_by_detection():
    assert has_top_level_order_by("SELECT x FROM t ORDER BY x")
    assert not has_top_level_order_by("SELECT x FROM (SELECT x FROM t ORDER BY x)")
