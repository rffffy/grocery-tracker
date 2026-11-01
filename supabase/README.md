# Database

## Migration tooling: Supabase CLI

We use the **Supabase CLI** to manage migrations. It tracks which migrations have been applied in a `supabase_migrations` table in the DB, so there's no guesswork about what's been run.

Migration files live in `supabase/migrations/` (timestamp-prefixed). Seed data lives in `supabase/seed.sql`.

### One-time setup

```bash
# Install Supabase CLI (macOS)
brew install supabase/tap/supabase

# Initialise (run once in the project root — creates supabase/config.toml)
supabase init

# Link to your remote Supabase project
supabase link --project-ref <your-project-ref>
# Project ref is the string in your Supabase project URL:
# https://supabase.com/dashboard/project/<project-ref>
```

### Before running CLI commands

Load your `.env` into the shell so variables like `$SUPABASE_PROJECT_REF` are available:

```bash
set -a && source .env && set +a
```

### Applying migrations

```bash
# Push all unapplied migrations to the remote DB
supabase db push

# Check which migrations have been applied
supabase migration list
```

### Seeding

`seed.sql` is **not** applied automatically to the hosted database, only on local resets. To seed the hosted database, open the Supabase dashboard → **SQL Editor**, paste `seed.sql` and run it. The file is idempotent (`ON CONFLICT DO NOTHING`), so running it more than once is safe.

### Creating a new migration

```bash
supabase migration new <descriptive_name>
# Creates supabase/migrations/<timestamp>_<descriptive_name>.sql
# Write your ALTER TABLE / CREATE TABLE SQL in that file, then run supabase db push
```

### Resetting (local dev only — destroys all data)

```bash
supabase db reset
# Drops and recreates the DB, re-runs all migrations, then runs seed.sql
```

---

## Useful queries

### Full item detail with category

```sql
SELECT
  r.date,
  r.store,
  ri.raw_name,
  pa.common_name,
  c.category_name,
  ri.quantity,
  ri.unit,
  ri.unit_price,
  ri.total_price
FROM receipt_items ri
JOIN receipts r         ON r.receipt_id   = ri.receipt_id
JOIN product_aliases pa ON pa.alias_id    = ri.alias_id
LEFT JOIN categories c  ON c.category_id  = pa.category_id;
```

### Aliases still needing review

```sql
SELECT alias_id, raw_name, store, first_seen
FROM product_aliases
WHERE common_name IS NULL OR category_id IS NULL
ORDER BY first_seen DESC;
```

### Monthly spend by category

Item prices are stored at list price. When a receipt has a `store_wide_discount`, distribute it proportionally across categories by item weight:

```sql
SELECT
  DATE_TRUNC('month', r.date)                                                        AS month,
  c.category_name,
  SUM(ri.total_price)
    - SUM(ri.total_price / subtotals.subtotal * r.store_wide_discount)               AS actual_spend
FROM receipt_items ri
JOIN receipts r ON r.receipt_id = ri.receipt_id
JOIN (
  SELECT receipt_id, SUM(total_price) AS subtotal
  FROM receipt_items
  GROUP BY receipt_id
) subtotals ON subtotals.receipt_id = ri.receipt_id
JOIN product_aliases pa ON pa.alias_id   = ri.alias_id
LEFT JOIN categories c  ON c.category_id = pa.category_id
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

> For receipts with no store-wide discount (`store_wide_discount = 0`), the second term is zero and the query behaves identically to a simple `SUM(total_price)`.

### Spend per store over time

```sql
SELECT
  DATE_TRUNC('month', date) AS month,
  store,
  SUM(receipt_total)        AS total_spend
FROM receipts
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

### Top 20 most-bought products

```sql
SELECT
  pa.common_name,
  c.category_name,
  COUNT(*)            AS purchase_count,
  SUM(ri.total_price) AS total_spent
FROM receipt_items ri
JOIN product_aliases pa ON pa.alias_id   = ri.alias_id
LEFT JOIN categories c  ON c.category_id = pa.category_id
WHERE pa.common_name IS NOT NULL
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 20;
```
