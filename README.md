# mayvary

Runs the same queries on Oracle and Postgres and shows you where the answers differ.

The migration finished. The queries run. Nobody checked that they return the same thing,
and a lot of them don't. A translated query that errors is the easy case. The bad case is
the one that runs fine and gives a different answer.

Not on PyPI yet. It explains 4 kinds of difference so far. Anything else is marked
unexplained, not guessed at.

## Demo

Same five customers and five orders on both sides. Every Postgres query below came out
of sqlglot 30.29.0.

```
$ make demo
SAME               customer-count  (translated by sqlglot)
...
DIFFERENT          blank-middle-names  (translated by sqlglot)
    cause: Oracle treats '' as NULL (query and data, rule empty-string-is-null)
      seen: 1 row only on Oracle, and the query tests TRIM(middle_name) IS NULL. Where it gives '', Oracle reads NULL.
      fix:  On Postgres, test NULLIF(TRIM(middle_name), '') IS NULL.
      see:  https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Nulls.html
    only in Oracle (1):
      (3)

DIFFERENT          customers-with-open-orders  (translated by sqlglot)
    sqlglot warned: Outer join syntax using the (+) operator is not supported.
    cause: The (+) outer join became an inner join (query and data, rule outer-join-plus)
      seen: 2 rows only on Oracle, each with NULLs, and the query outer-joins on o.customer_id (+), o.status (+)
      fix:  Rewrite it as LEFT JOIN and move every (+) condition into the ON clause. A (+) that's dropped, or left in WHERE, makes it an inner join.
    only in Oracle (2):
      (3, None)
      (4, None)

DIFFERENT          status-length  (translated by sqlglot)
    cause: unexplained
    only in Oracle (5):
      (1, 10)
      ...
...
10 cases: 4 same, 6 different, 5 of 6 differences explained
```

`demo/fixes.toml` has the fix for each cause. `make fixes` runs them and they all come out
SAME.

Needs Docker and [uv](https://docs.astral.sh/uv/). The Oracle side is
`gvenzl/oracle-free`. `make down` throws both databases away.

## How it explains

Each rule is one file in `src/mayvary/explain/rules/`. A rule looks at the Oracle query and
at the rows that differ, and only names a cause when the rows match its pattern. "query and
data" means both matched. "data only" means the rows look right but the query didn't confirm
it, so treat it as a guess.

| Rule | Oracle | Postgres |
|---|---|---|
| `empty-string-is-null` | `''` is NULL, so `TRIM(' ') IS NULL` is true and `NVL(x, '')` stays NULL | `''` is a value |
| `char-padding` | `CHAR(10)` keeps its padding through `\|\|` | the padding goes on the cast to text |
| `outer-join-plus` | `(+)` is an outer join | sqlglot drops `(+)`, so it's an inner join |
| `substr-position-zero` | `SUBSTR(s, 0, 3)` treats 0 as 1 | `substring(s from 0 for 3)` returns 2 characters |

A difference no rule matches is printed as `cause: unexplained`. That's on purpose. A wrong
cause is worse than none.

## Cases

A TOML file of `[[case]]` entries. Leave out `postgres` and sqlglot translates the
Oracle SQL for you.

```toml
[[case]]
name = "sku-prefix"
oracle = "SELECT id, SUBSTR(sku, 0, 3) AS prefix FROM orders ORDER BY id"

[[case]]
name = "sku-prefix-fixed"
oracle = "SELECT id, SUBSTR(sku, 0, 3) AS prefix FROM orders ORDER BY id"
postgres = "SELECT id, substr(sku, 1, 3) AS prefix FROM orders ORDER BY id"
```

```
mayvary cases.toml \
  --oracle 'user/password@host:1521/SERVICE' \
  --postgres 'postgresql://user:password@host:5432/db'
```

Or set `MAYVARY_ORACLE` and `MAYVARY_POSTGRES`. Rows are compared as a multiset unless
the Oracle query ends in `ORDER BY`. Exit code is 0 when everything matches, 1 when
anything doesn't.

## Where to point it

**Point it at a clone or a restored copy, not production.** It runs SELECTs only, in
read-only transactions, with a timeout and a row cap. A SELECT can still call a function
that writes, so connect as a user that can only read.

It compares answers, never timings.

## License

MIT
