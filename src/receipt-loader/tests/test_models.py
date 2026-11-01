from datetime import date, time

import pytest
from pydantic import ValidationError

from receipt_loader.models.receipt import Receipt


def test_valid_receipt_parses(receipt_data):
    receipt = Receipt.model_validate(receipt_data)

    assert receipt.receipt_id == "20260115-rewe-183045"
    assert receipt.date == date(2026, 1, 15)
    assert receipt.time == time(18, 30, 45)
    assert len(receipt.items) == 3
    assert receipt.items[1].is_discounted is True


def test_store_name_is_normalised(receipt_data):
    receipt_data["store"] = "  lidl "
    assert Receipt.model_validate(receipt_data).store == "Lidl"


def test_unknown_store_is_rejected(receipt_data):
    receipt_data["store"] = "Tesco"
    with pytest.raises(ValidationError, match="Unknown store"):
        Receipt.model_validate(receipt_data)


def test_optional_fields_have_defaults(receipt_data):
    del receipt_data["store_wide_discount"]
    del receipt_data["warnings"]
    del receipt_data["items"][0]["category_id"]

    receipt = Receipt.model_validate(receipt_data)

    assert receipt.store_wide_discount == 0.0
    assert receipt.warnings == []
    assert receipt.items[0].category_id is None
    assert receipt.items[0].is_discounted is False


@pytest.mark.parametrize("unit", ["Stück", "kg", "g", "L", "ml", "Pack"])
def test_allowed_units(receipt_data, unit):
    receipt_data["items"][0]["unit"] = unit
    assert Receipt.model_validate(receipt_data).items[0].unit == unit


def test_unknown_unit_is_rejected(receipt_data):
    receipt_data["items"][0]["unit"] = "litre"
    with pytest.raises(ValidationError):
        Receipt.model_validate(receipt_data)


@pytest.mark.parametrize("field", ["receipt_id", "store", "date", "time", "receipt_total", "items"])
def test_required_fields(receipt_data, field):
    del receipt_data[field]
    with pytest.raises(ValidationError):
        Receipt.model_validate(receipt_data)


def test_invalid_date_is_rejected(receipt_data):
    receipt_data["date"] = "15.01.2026"  # German format must be converted upstream
    with pytest.raises(ValidationError):
        Receipt.model_validate(receipt_data)
