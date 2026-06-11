CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY,
    name        TEXT,
    email       TEXT,
    city        TEXT,
    country     TEXT,
    plan        TEXT,
    mrr         REAL,
    signup_date TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    product     TEXT,
    amount      REAL,
    created_at  TEXT
);

DELETE FROM customers;
DELETE FROM orders;

INSERT INTO customers VALUES
    (1,  'Alice Müller',  'alice@example.de',  'Berlin',    'Germany',       'pro',        149.0, '2023-03-12'),
    (2,  'Bob Smith',     'bob@example.com',   'New York',  'United States', 'enterprise', 499.0, '2023-01-05'),
    (3,  'Carla Rossi',   'carla@example.it',  'Rome',      'Italy',         'free',       0.0,   '2024-02-20'),
    (4,  'David Lee',     'david@example.sg',  'Singapore', 'Singapore',     'pro',        149.0, '2023-07-18'),
    (5,  'Eva Kowalski',  'eva@example.pl',    'Warsaw',    'Poland',        'pro',        149.0, '2023-11-01'),
    (6,  'Frank Chen',    'frank@example.cn',  'Shanghai',  'China',         'enterprise', 499.0, '2022-09-30'),
    (7,  'Grace Okafor',  'grace@example.ng',  'Lagos',     'Nigeria',       'free',       0.0,   '2024-05-15'),
    (8,  'Hana Nakamura', 'hana@example.jp',   'Tokyo',     'Japan',         'pro',        149.0, '2023-04-22'),
    (9,  'Ivan Petrov',   'ivan@example.ru',   'Moscow',    'Russia',        'free',       0.0,   '2024-01-11'),
    (10, 'Julia Santos',  'julia@example.br',  'São Paulo', 'Brazil',        'enterprise', 499.0, '2022-12-03');

INSERT INTO orders VALUES
    (1,  2,  'Annual License',       4990.0, '2024-01-05'),
    (2,  6,  'Annual License',       4990.0, '2023-09-30'),
    (3,  10, 'Annual License',       4990.0, '2023-12-03'),
    (4,  1,  'Monthly Subscription', 149.0,  '2024-03-01'),
    (5,  4,  'Monthly Subscription', 149.0,  '2024-03-15'),
    (6,  5,  'Monthly Subscription', 149.0,  '2024-04-01'),
    (7,  8,  'Monthly Subscription', 149.0,  '2024-03-22'),
    (8,  3,  'Upgrade to Pro',       149.0,  '2024-06-01'),
    (9,  7,  'Upgrade to Pro',       149.0,  '2024-06-08'),
    (10, 9,  'Upgrade to Pro',       149.0,  '2024-06-09');
