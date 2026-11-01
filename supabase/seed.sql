-- Seed: default spending categories
-- Supabase CLI runs this automatically on `supabase db reset`.
-- To run manually: paste into the Supabase SQL editor after migrations.

INSERT INTO categories (category_name) VALUES
  ('Meat & Deli'),
  ('Dairy & Eggs'),
  ('Bakery & Bread'),
  ('Fruit & Vegetables'),
  ('Drinks'),
  ('Snacks & Sweets'),
  ('Pantry & Dry Goods'),
  ('Frozen'),
  ('Household'),
  ('Personal Care'),
  ('Other'),
  ('Uncategorized'),
  ('Ready To Eat Meals'),
  ('Baby & Kids')
ON CONFLICT (category_name) DO NOTHING;
