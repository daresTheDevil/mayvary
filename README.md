# mayvary

Runs the same queries on Oracle and Postgres and shows you where the answers differ.

The migration finished. The queries run. Nobody checked that they return the same thing,
and a lot of them don't. A translated query that errors is the easy case. The bad case is
the one that runs fine and gives a different answer.

Not on PyPI yet. It finds differences but doesn't explain them yet. That part is next.

## Demo

Same five customers and five orders on both sides. Every Postgres query below came out
of sqlglot 30.29.0.

```
$ make demo
SAME               customer-count  (translated by sqlglot)
SAME               open-orders  (translated by sqlglot)
SAME               active-customers  (translated by sqlglot)
SAME               spend-per-customer  (translated by sqlglot)
DIFFERENT          blank-middle-names  (translated by sqlglot)
    only in Oracle (1):
      (3)
    postgres sql: SELECT id FROM customers WHERE TRIM(middle_name) IS NULL ORDER BY id

DIFFERENT          customers-with-open-orders  (translated by sqlglot)
    sqlglot warned: Outer join syntax using the (+) operator is not supported.
    only in Oracle (2):
      (3, None)
      (4, None)
    postgres sql: SELECT c.id, o.id AS order_id FROM customers AS c, orders AS o WHERE c.id = o.customer_id AND o.status = 'OPEN' ORDER BY c.id

DIFFERENT          sku-prefix  (translated by sqlglot)
    only in Oracle (5):
      (101, 'ABC')
      ...
    only in Postgres (5):
      (101, 'AB')
      ...
...
9 cases: 4 same, 5 different
```

What went wrong in each:

| Case | Oracle | Postgres |
|---|---|---|
| `blank-middle-names` | `TRIM(' ')` is `''`, and `''` is NULL | `trim(' ')` is `''`, which isn't NULL |
| `middle-name-or-empty` | `NVL(x, '')` is `NVL(x, NULL)`, so NULL stays NULL | `COALESCE(x, '')` gives `''` |
| `status-label` | `CHAR(10)` keeps its padding through `\|\|` | the padding goes on the cast to text |
| `customers-with-open-orders` | `(+)` is an outer join | sqlglot drops `(+)`, so it's an inner join |
| `sku-prefix` | `SUBSTR(s, 0, 3)` treats 0 as 1 | `substring(s from 0 for 3)` returns 2 characters |

Needs Docker and [uv](https://docs.astral.sh/uv/). The Oracle side is
`gvenzl/oracle-free`. `make down` throws both databases away.

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
