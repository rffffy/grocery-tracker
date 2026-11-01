import copy

import pytest

# Fictional receipt used across tests — not real purchase data.
SAMPLE_RECEIPT = {
    "receipt_id": "20260115-rewe-183045",
    "store": "REWE",
    "date": "2026-01-15",
    "time": "18:30:45",
    "receipt_total": 7.47,
    "store_wide_discount": 0.0,
    "items": [
        {
            "raw_name": "BIO VOLLMILCH 3,8%",
            "category_id": 2,
            "quantity": 1,
            "unit": "L",
            "unit_price": 1.29,
            "total_price": 1.29,
        },
        {
            "raw_name": "BANANEN",
            "category_id": 4,
            "quantity": 1.2,
            "unit": "kg",
            "unit_price": 1.65,
            "total_price": 1.98,
            "is_discounted": True,
        },
        {
            "raw_name": "VOLLKORNBROT",
            "category_id": 3,
            "quantity": 2,
            "unit": "Stück",
            "unit_price": 2.10,
            "total_price": 4.20,
        },
    ],
    "warnings": [],
}


@pytest.fixture
def receipt_data() -> dict:
    """A fresh, mutable copy of the sample receipt for each test."""
    return copy.deepcopy(SAMPLE_RECEIPT)
