-- Migration: add is_discounted flag to receipt_items
-- Indicates whether a coupon or discount was applied to this line item

ALTER TABLE receipt_items
ADD COLUMN is_discounted BOOLEAN NOT NULL DEFAULT FALSE;
