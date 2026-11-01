-- Migration: initial schema
-- Tables in dependency order: categories → product_aliases → receipts → receipt_items

CREATE TABLE categories (
  category_id   SERIAL PRIMARY KEY,
  category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE product_aliases (
  alias_id      SERIAL PRIMARY KEY,
  raw_name      TEXT NOT NULL,
  store         TEXT NOT NULL,
  common_name   TEXT,
  category_id   INT REFERENCES categories(category_id),
  first_seen    DATE NOT NULL DEFAULT CURRENT_DATE,
  UNIQUE (raw_name, store)
);

CREATE INDEX idx_aliases_raw_store ON product_aliases (raw_name, store);

CREATE TABLE receipts (
  receipt_id    TEXT PRIMARY KEY,
  date          DATE NOT NULL,
  time          TIME NOT NULL,
  store         TEXT NOT NULL,
  receipt_total NUMERIC(10, 2) NOT NULL,
  ingested_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_receipts_date ON receipts (date);

CREATE TABLE receipt_items (
  item_id      SERIAL PRIMARY KEY,
  receipt_id   TEXT NOT NULL REFERENCES receipts(receipt_id) ON DELETE CASCADE,
  alias_id     INT NOT NULL REFERENCES product_aliases(alias_id),
  raw_name     TEXT NOT NULL,
  quantity     NUMERIC(10, 3) NOT NULL,
  unit         TEXT NOT NULL CHECK (unit IN ('Stück', 'kg', 'g', 'L', 'ml', 'Pack')),
  unit_price   NUMERIC(10, 2) NOT NULL,
  total_price  NUMERIC(10, 2) NOT NULL
);

CREATE INDEX idx_items_receipt ON receipt_items (receipt_id);
CREATE INDEX idx_items_alias   ON receipt_items (alias_id);
