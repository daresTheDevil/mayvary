import tomllib
from dataclasses import dataclass
from pathlib import Path

KNOWN_KEYS = {"name", "oracle", "postgres"}


@dataclass(frozen=True)
class Case:
    name: str
    oracle: str
    postgres: str | None


class CaseFileError(Exception):
    pass


def load_cases(path: Path) -> list[Case]:
    data = tomllib.loads(path.read_text())
    entries = data.get("case")
    if not entries:
        raise CaseFileError(f"{path}: no [[case]] entries")
    return [parse_case(path, i, entry) for i, entry in enumerate(entries, 1)]


def parse_case(path: Path, index: int, entry: dict) -> Case:
    where = f"{path}: case {index}"
    unknown = set(entry) - KNOWN_KEYS
    if unknown:
        raise CaseFileError(f"{where}: unknown keys {sorted(unknown)}")
    for key in ("name", "oracle"):
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            raise CaseFileError(f"{where}: '{key}' is required")
    postgres = entry.get("postgres")
    if postgres is not None and not isinstance(postgres, str):
        raise CaseFileError(f"{where}: 'postgres' must be a string")
    return Case(entry["name"], entry["oracle"].strip(), postgres and postgres.strip())
