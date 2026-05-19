INSERT INTO customers (email, full_name, plan, created_at, updated_at) VALUES
 ('ada@example.com',       'Ada Lovelace',   'pro',  '2025-09-01', '2025-09-01'),
 ('alan@example.com',      'Alan Turing',    'free', '2025-09-02', '2025-12-15'),
 ('grace@example.com',     'Grace Hopper',   'pro',  '2025-10-12', '2025-11-30'),
 ('linus@example.com',     'Linus Torvalds', 'free', '2025-11-04', '2025-11-04'),
 ('katherine@example.com', 'Katherine J.',   'pro',  '2026-01-08', '2026-04-20');

INSERT INTO orders (customer_id, status, total_cents, currency, placed_at, updated_at) VALUES
 (1, 'paid',      4990,  'USD', '2025-09-15', '2025-09-15'),
 (1, 'paid',      12990, 'USD', '2025-10-02', '2025-10-02'),
 (2, 'cancelled', 990,   'USD', '2025-09-10', '2025-09-12'),
 (3, 'shipped',   24990, 'USD', '2025-10-20', '2025-10-25'),
 (3, 'pending',   9990,  'USD', '2026-05-10', '2026-05-10'),
 (5, 'paid',      4990,  'EUR', '2026-04-22', '2026-04-22');

INSERT INTO line_items (order_id, sku, qty, price_cents, updated_at) VALUES
 (1, 'BOOK-CALC', 1, 4990,  '2025-09-15'),
 (2, 'BOOK-CALC', 1, 4990,  '2025-10-02'),
 (2, 'STICKER-PI',4, 2000,  '2025-10-02'),
 (3, 'MUG-GO',    1, 990,   '2025-09-10'),
 (4, 'BOOK-COBOL',2, 12495, '2025-10-20'),
 (5, 'TSHIRT-LX', 1, 9990,  '2026-05-10'),
 (6, 'BOOK-EU',   1, 4990,  '2026-04-22');
