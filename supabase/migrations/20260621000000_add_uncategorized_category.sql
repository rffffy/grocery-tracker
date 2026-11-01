-- Migration: add Uncategorized category for items Claude cannot confidently categorise
-- Claude uses this ID (12) when uncertain — the user then fills in the real category manually.
-- Fixed ID so a fresh database gets the same IDs as seed.sql, regardless of run order.

INSERT INTO categories (category_id, category_name)
VALUES (12, 'Uncategorized')
ON CONFLICT DO NOTHING;

SELECT setval(pg_get_serial_sequence('categories', 'category_id'), (SELECT MAX(category_id) FROM categories));
