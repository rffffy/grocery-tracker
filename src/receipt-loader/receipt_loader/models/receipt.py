from datetime import date, time
from typing import Literal

from pydantic import BaseModel, field_validator

from receipt_loader.config.stores import normalize_store


class ReceiptItem(BaseModel):
    raw_name: str
    category_id: int | None = None
    quantity: float
    unit: Literal["Stück", "kg", "g", "L", "ml", "Pack"]
    unit_price: float
    total_price: float
    is_discounted: bool = False


class Receipt(BaseModel):
    receipt_id: str
    store: str
    date: date
    time: time
    receipt_total: float
    store_wide_discount: float = 0.0
    items: list[ReceiptItem]
    warnings: list[str] = []

    @field_validator("store")
    @classmethod
    def normalise_store(cls, v: str) -> str:
        return normalize_store(v)
