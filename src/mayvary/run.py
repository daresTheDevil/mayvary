from dataclasses import dataclass

import oracledb
import psycopg

from mayvary.compare import Result

oracledb.defaults.fetch_decimals = True


@dataclass(frozen=True)
class Limits:
    timeout_seconds: int
    max_rows: int


class TooManyRows(Exception):
    pass


def connect_oracle(dsn: str, limits: Limits) -> oracledb.Connection:
    credentials, _, address = dsn.rpartition("@")
    user, _, password = credentials.partition("/")
    if not (user and password and address):
        raise ValueError("Oracle DSN must look like user/password@host:port/service")
    conn = oracledb.connect(user=user, password=password, dsn=address)
    conn.call_timeout = limits.timeout_seconds * 1000
    return conn


def connect_postgres(dsn: str, limits: Limits) -> psycopg.Connection:
    options = (
        "-c default_transaction_read_only=on "
        f"-c statement_timeout={limits.timeout_seconds * 1000}"
    )
    return psycopg.connect(dsn, options=options)


def fetch_oracle(conn: oracledb.Connection, sql: str, limits: Limits) -> Result:
    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        try:
            cur.execute(strip_semicolon(sql))
            return collect(cur, limits)
        finally:
            conn.rollback()


def fetch_postgres(conn: psycopg.Connection, sql: str, limits: Limits) -> Result:
    with conn.cursor() as cur:
        try:
            cur.execute(strip_semicolon(sql))
            return collect(cur, limits)
        finally:
            conn.rollback()


def collect(cur, limits: Limits) -> Result:
    columns = tuple(d[0] for d in cur.description)
    rows = cur.fetchmany(limits.max_rows + 1)
    if len(rows) > limits.max_rows:
        raise TooManyRows(f"more than {limits.max_rows} rows")
    return Result(columns, tuple(tuple(r) for r in rows))


def strip_semicolon(sql: str) -> str:
    return sql.strip().removesuffix(";")
