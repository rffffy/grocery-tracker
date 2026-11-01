INSERT INTO categories (category_name) VALUES ('Baby & Kids')
ON CONFLICT (category_name) DO NOTHING;
