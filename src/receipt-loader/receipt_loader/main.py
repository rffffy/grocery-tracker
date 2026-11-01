import asyncio
import json
import sys

from pydantic import ValidationError

from receipt_loader.db.supabase import load_receipt
from receipt_loader.models.receipt import Receipt


async def main() -> None:
    dry_run = "--dry-run" in sys.argv
    raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        receipt = Receipt.model_validate(data)
    except ValidationError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)

    if dry_run:
        print(json.dumps({
            "status": "dry-run",
            "receipt_id": receipt.receipt_id,
            "store": receipt.store,
            "date": str(receipt.date),
            "num_items": len(receipt.items),
            "receipt_total": receipt.receipt_total,
            "warnings": receipt.warnings,
        }))
        return

    result = await load_receipt(receipt)

    if result["status"] == "inserted":
        item_sum = sum(item.total_price for item in receipt.items)
        if abs(item_sum - receipt.receipt_total) > 0.01:
            result["sanity_warning"] = True
            result["item_sum"] = round(item_sum, 2)
            result["receipt_total"] = receipt.receipt_total

    print(json.dumps(result))


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
