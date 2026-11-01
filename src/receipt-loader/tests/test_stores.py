import pytest

from receipt_loader.config.stores import STORE_ALIASES, normalize_store


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("REWE", "REWE"),
        ("rewe", "REWE"),
        ("  Lidl  ", "Lidl"),
        ("DM", "dm"),
        ("go india", "Go India"),
        ("GO INDIA", "Go India"),
    ],
)
def test_normalize_store_handles_case_and_whitespace(raw, expected):
    assert normalize_store(raw) == expected


def test_every_canonical_name_normalises_to_itself():
    for canonical in STORE_ALIASES.values():
        assert normalize_store(canonical) == canonical


def test_unknown_store_raises_helpful_error():
    with pytest.raises(ValueError, match="Unknown store: 'Tesco'"):
        normalize_store("Tesco")
