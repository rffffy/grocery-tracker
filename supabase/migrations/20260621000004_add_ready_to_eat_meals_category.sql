INSERT INTO categories (category_name) VALUES ('Ready To Eat Meals')
ON CONFLICT (category_name) DO NOTHING;
