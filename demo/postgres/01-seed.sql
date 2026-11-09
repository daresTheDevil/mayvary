-- The Oracle schema moved over with the usual type mapping. Same rows.
CREATE TABLE customers (
  id          bigint      PRIMARY KEY,
  first_name  varchar(30) NOT NULL,
  middle_name varchar(30),
  status      char(10)    NOT NULL
);

CREATE TABLE orders (
  id          bigint         PRIMARY KEY,
  customer_id bigint         NOT NULL REFERENCES customers (id),
  sku         varchar(20)    NOT NULL,
  status      varchar(10)    NOT NULL,
  total       numeric(10, 2) NOT NULL
);

INSERT INTO customers VALUES
  (1, 'Ada',      NULL,       'ACTIVE'),
  (2, 'Grace',    'Brewster', 'ACTIVE'),
  (3, 'Linus',    ' ',        'CLOSED'),
  (4, 'Margaret', NULL,       'ACTIVE'),
  (5, 'Ken',      'L',        'PENDING');

INSERT INTO orders VALUES
  (101, 1, 'ABC-1001', 'OPEN',    19.99),
  (102, 1, 'XYZ-2001', 'SHIPPED',  5.00),
  (103, 2, 'ABC-1002', 'OPEN',    42.50),
  (104, 3, 'QRS-3001', 'SHIPPED', 12.00),
  (105, 5, 'XYZ-2002', 'OPEN',     7.25);
