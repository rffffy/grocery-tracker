"""End-to-end tests for the CLI: stdin JSON in, stdout JSON out. The database is faked."""
import io
import json

import pytest

from receipt_loader import main as main_module


def run_cli(monkeypatch, capsys, stdin_text: str, argv: list[str] | None = None) -> tuple[dict, int]:
    """Run main() with the given stdin; return (parsed stdout JSON, exit code)."""
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    monkeypatch.setattr("sys.argv", ["receipt-loader", *(argv or [])])

    exit_code = 0
    try:
        main_module.main_sync()
    except SystemExit as e:
        exit_code = e.code

    return json.loads(capsys.readouterr().out), exit_code


@pytest.fixture
def fake_load(monkeypatch):
    """Replace the DB call with a fake that records what it was given."""
    calls = []

    async def _fake_load_receipt(receipt):
        calls.append(receipt)
        return {
            "status": "inserted",
            "receipt_id": receipt.receipt_id,
            "num_items": len(receipt.items),
            "new_aliases": [],
        }

    monkeypatch.setattr(main_module, "load_receipt", _fake_load_receipt)
    return calls


def test_invalid_json_returns_error(monkeypatch, capsys, fake_load):
    out, code = run_cli(monkeypatch, capsys, "{not json")

    assert code == 1
    assert out["status"] == "error"
    assert out["error"].startswith("Invalid JSON")
    assert fake_load == []


def test_validation_error_returns_error(monkeypatch, capsys, fake_load, receipt_data):
    receipt_data["store"] = "Tesco"
    out, code = run_cli(monkeypatch, capsys, json.dumps(receipt_data))

    assert code == 1
    assert out["status"] == "error"
    assert "Unknown store" in out["error"]
    assert fake_load == []


def test_dry_run_does_not_touch_database(monkeypatch, capsys, fake_load, receipt_data):
    out, code = run_cli(monkeypatch, capsys, json.dumps(receipt_data), ["--dry-run"])

    assert code == 0
    assert out == {
        "status": "dry-run",
        "receipt_id": "20260115-rewe-183045",
        "store": "REWE",
        "date": "2026-01-15",
        "num_items": 3,
        "receipt_total": 7.47,
        "warnings": [],
    }
    assert fake_load == []


def test_insert_passes_validated_receipt_to_db(monkeypatch, capsys, fake_load, receipt_data):
    out, code = run_cli(monkeypatch, capsys, json.dumps(receipt_data))

    assert code == 0
    assert out["status"] == "inserted"
    assert out["num_items"] == 3
    assert "sanity_warning" not in out
    assert len(fake_load) == 1
    assert fake_load[0].store == "REWE"


def test_sanity_warning_when_items_do_not_add_up(monkeypatch, capsys, fake_load, receipt_data):
    receipt_data["receipt_total"] = 10.00  # items sum to 7.47

    out, _ = run_cli(monkeypatch, capsys, json.dumps(receipt_data))

    assert out["status"] == "inserted"
    assert out["sanity_warning"] is True
    assert out["item_sum"] == 7.47
    assert out["receipt_total"] == 10.00


def test_rounding_within_one_cent_is_tolerated(monkeypatch, capsys, fake_load, receipt_data):
    receipt_data["receipt_total"] = 7.48  # off by exactly one cent

    out, _ = run_cli(monkeypatch, capsys, json.dumps(receipt_data))

    assert "sanity_warning" not in out


def test_basket_coupon_is_subtracted_before_comparing(monkeypatch, capsys, fake_load, receipt_data):
    # Items sum to 7.47; a 0.75 store-wide coupon brings the amount paid to 6.72
    receipt_data["store_wide_discount"] = 0.75
    receipt_data["receipt_total"] = 6.72

    out, _ = run_cli(monkeypatch, capsys, json.dumps(receipt_data))

    assert out["status"] == "inserted"
    assert "sanity_warning" not in out


def test_coupon_receipt_that_does_not_add_up_still_warns(monkeypatch, capsys, fake_load, receipt_data):
    receipt_data["store_wide_discount"] = 0.75
    receipt_data["receipt_total"] = 7.47  # coupon not reflected in the total

    out, _ = run_cli(monkeypatch, capsys, json.dumps(receipt_data))

    assert out["sanity_warning"] is True


def test_skipped_receipt_gets_no_sanity_check(monkeypatch, capsys, receipt_data):
    async def _already_loaded(receipt):
        return {"status": "skipped", "receipt_id": receipt.receipt_id}

    monkeypatch.setattr(main_module, "load_receipt", _already_loaded)
    receipt_data["receipt_total"] = 99.99

    out, code = run_cli(monkeypatch, capsys, json.dumps(receipt_data))

    assert code == 0
    assert out == {"status": "skipped", "receipt_id": "20260115-rewe-183045"}
