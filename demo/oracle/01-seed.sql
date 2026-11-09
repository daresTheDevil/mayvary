-- Same rows as demo/postgres/01-seed.sql. Customer 3's middle name is one space.
CONNECT mayvary/mayvary@//localhost:1521/FREEPDB1

CREATE TABLE customers (
  id          NUMBER(10)   PRIMARY KEY,
  first_name  VARCHAR2(30) NOT NULL,
  middle_name VARCHAR2(30),
  status      CHAR(10)     NOT NULL
);

CREATE TABLE orders (
  id          NUMBER(10)    PRIMARY KEY,
  customer_id NUMBER(10)    NOT NULL REFERENCES customers (id),
  sku         VARCHAR2(20)  NOT NULL,
  status      VARCHAR2(10)  NOT NULL,
  total       NUMBER(10, 2) NOT NULL
);

INSERT INTO customers VALUES (1, 'Ada',      NULL,       'ACTIVE');
INSERT INTO customers VALUES (2, 'Grace',    'Brewster', 'ACTIVE');
INSERT INTO customers VALUES (3, 'Linus',    ' ',        'CLOSED');
INSERT INTO customers VALUES (4, 'Margaret', NULL,       'ACTIVE');
INSERT INTO customers VALUES (5, 'Ken',      'L',        'PENDING');

INSERT INTO orders VALUES (101, 1, 'ABC-1001', 'OPEN',    19.99);
INSERT INTO orders VALUES (102, 1, 'XYZ-2001', 'SHIPPED',  5.00);
INSERT INTO orders VALUES (103, 2, 'ABC-1002', 'OPEN',    42.50);
INSERT INTO orders VALUES (104, 3, 'QRS-3001', 'SHIPPED', 12.00);
INSERT INTO orders VALUES (105, 5, 'XYZ-2002', 'OPEN',     7.25);

COMMIT;
