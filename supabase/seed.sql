-- Seed: default spending categories
-- Supabase CLI runs this automatically on `supabase db reset`.
-- To run manually: paste into the Supabase SQL editor after migrations.
--
-- IDs are fixed because the extraction prompt and the n8n workflows refer to them
-- (e.g. 12 = Uncategorized). Safe to run more than once.

INSERT INTO categories (category_id, category_name) VALUES
  (1,  'Meat & Deli'),
  (2,  'Dairy & Eggs'),
  (3,  'Bakery & Bread'),
  (4,  'Fruit & Vegetables'),
  (5,  'Drinks'),
  (6,  'Snacks & Sweets'),
  (7,  'Pantry & Dry Goods'),
  (8,  'Frozen'),
  (9,  'Household'),
  (10, 'Personal Care'),
  (11, 'Other'),
  (12, 'Uncategorized'),
  (13, 'Ready To Eat Meals'),
  (14, 'Baby & Kids')
ON CONFLICT DO NOTHING;

-- Keep the ID counter ahead of the fixed IDs so new categories don't collide
SELECT setval(pg_get_serial_sequence('categories', 'category_id'), (SELECT MAX(category_id) FROM categories));
