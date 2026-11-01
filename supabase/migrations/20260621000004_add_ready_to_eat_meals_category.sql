-- Fixed ID so a fresh database gets the same IDs as seed.sql, regardless of run order.
INSERT INTO categories (category_id, category_name) VALUES (13, 'Ready To Eat Meals')
ON CONFLICT DO NOTHING;

SELECT setval(pg_get_serial_sequence('categories', 'category_id'), (SELECT MAX(category_id) FROM categories));
