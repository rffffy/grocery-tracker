-- Migration: add store_wide_discount to receipts
-- Captures basket-level/storewide coupons that cannot be attributed to a specific item.
-- Item prices remain at list price; this column explains any gap between
-- sum(receipt_items.total_price) and receipt_total.
-- Formula: sum(receipt_items.total_price) - store_wide_discount = receipt_total

ALTER TABLE receipts
ADD COLUMN store_wide_discount NUMERIC(10, 2) NOT NULL DEFAULT 0;
