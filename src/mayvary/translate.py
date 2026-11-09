import logging
from dataclasses import dataclass

import sqlglot
from sqlglot import exp


@dataclass(frozen=True)
class Translation:
    sql: str
    warnings: list[str]


class _Collect(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def to_postgres(oracle_sql: str) -> Translation:
    # sqlglot reports some lossy translations only as log warnings, (+) joins
    # among them. Keep those, since they're often the reason the answers differ.
    handler = _Collect()
    logger = logging.getLogger("sqlglot")
    logger.addHandler(handler)
    try:
        statements = sqlglot.transpile(oracle_sql, read="oracle", write="postgres")
    finally:
        logger.removeHandler(handler)
    if len(statements) != 1:
        raise ValueError(f"expected one statement, got {len(statements)}")
    return Translation(statements[0], list(dict.fromkeys(handler.messages)))


def has_top_level_order_by(oracle_sql: str) -> bool:
    tree = sqlglot.parse_one(oracle_sql, read="oracle")
    return isinstance(tree, exp.Query) and tree.args.get("order") is not None
