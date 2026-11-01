-- Migration: add Uncategorized category for items Claude cannot confidently categorise
-- Claude should use this ID (12) when uncertain — user then fills in the real category manually

INSERT INTO categories (category_name)
VALUES ('Uncategorized')
ON CONFLICT (category_name) DO NOTHING;
