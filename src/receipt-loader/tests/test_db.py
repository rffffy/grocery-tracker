"""Tests for load_receipt() using a fake psycopg connection — no real database needed."""
import asyncio
from contextlib import asynccontextmanager

import pytest

from receipt_loader.db import supabase as db_module
from receipt_loader.models.receipt import Receipt


class FakeCursor:
    def __init__(self, db: "FakeDB"):
        self.db = db
        self._result = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, sql: str, params: tuple):
        sql = " ".join(sql.split())
        self.db.executed.append((sql, params))

        if sql.startswith("SELECT 1 FROM receipts"):
            self._result = (1,) if params[0] in self.db.existing_receipts else None
        elif sql.startswith("INSERT INTO product_aliases"):
            key = (params[0], params[1])
            if key in self.db.aliases:
                self._result = None  # ON CONFLICT DO NOTHING → no row returned
            else:
                self.db.next_alias_id += 1
                self.db.aliases[key] = self.db.next_alias_id
                self._result = (self.db.next_alias_id,)
        elif sql.startswith("SELECT alias_id FROM product_aliases"):
            self._result = (self.db.aliases[(params[0], params[1])],)
        else:
            self._result = None

    async def fetchone(self):
        return self._result


class FakeConnection:
    def __init__(self, db: "FakeDB"):
        self.db = db

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def cursor(self):
        return FakeCursor(self.db)

    @asynccontextmanager
    async def transaction(self):
        yield


class FakeDB:
    def __init__(self, existing_receipts=(), aliases=None):
        self.existing_receipts = set(existing_receipts)
        self.aliases = dict(aliases or {})
        self.next_alias_id = max(self.aliases.values(), default=0)
        self.executed: list[tuple[str, tuple]] = []

    def statements(self, prefix: str) -> list[tuple]:
        return [params for sql, params in self.executed if sql.startswith(prefix)]


@pytest.fixture
def fake_db(monkeypatch):
    def install(**kwargs) -> FakeDB:
        db = FakeDB(**kwargs)

        async def _connect(url, **_):
            assert url == "postgresql://test"
            return FakeConnection(db)

        monkeypatch.setattr(db_module.psycopg.AsyncConnection, "connect", _connect)
        return db

    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://test")
    return install


def load(receipt_data) -> dict:
    return asyncio.run(db_module.load_receipt(Receipt.model_validate(receipt_data)))


def test_duplicate_receipt_is_skipped(fake_db, receipt_data):
    db = fake_db(existing_receipts={"20260115-rewe-183045"})

    result = load(receipt_data)

    assert result == {"status": "skipped", "receipt_id": "20260115-rewe-183045"}
    assert db.statements("INSERT") == []


def test_new_receipt_inserts_receipt_and_items(fake_db, receipt_data):
    db = fake_db()

    result = load(receipt_data)

    assert result["status"] == "inserted"
    assert result["num_items"] == 3
    assert len(db.statements("INSERT INTO receipts")) == 1
    assert len(db.statements("INSERT INTO receipt_items")) == 3


def test_new_products_are_reported_as_new_aliases(fake_db, receipt_data):
    fake_db()

    result = load(receipt_data)

    assert [a["raw_name"] for a in result["new_aliases"]] == [
        "BIO VOLLMILCH 3,8%",
        "BANANEN",
        "VOLLKORNBROT",
    ]
    assert all(a["store"] == "REWE" for a in result["new_aliases"])


def test_known_products_reuse_existing_alias(fake_db, receipt_data):
    db = fake_db(aliases={("BANANEN", "REWE"): 42})

    result = load(receipt_data)

    assert "BANANEN" not in [a["raw_name"] for a in result["new_aliases"]]
    banana_item = next(p for p in db.statements("INSERT INTO receipt_items") if p[2] == "BANANEN")
    assert banana_item[1] == 42  # alias_id column


def test_same_product_name_at_different_store_is_a_new_alias(fake_db, receipt_data):
    fake_db(aliases={("BANANEN", "Lidl"): 7})

    result = load(receipt_data)

    assert "BANANEN" in [a["raw_name"] for a in result["new_aliases"]]
