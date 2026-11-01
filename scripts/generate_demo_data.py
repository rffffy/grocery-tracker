"""Generate fictional receipt JSON files for demos and testing.

The output matches what the Claude extraction agent produces, so the files can be
loaded with the real pipeline:

    uv run --package receipt-loader python scripts/generate_demo_data.py --out demo_data
    for f in demo_data/*.json; do
        SUPABASE_DB_URL="$DEMO_SUPABASE_DB_URL" uv run --package receipt-loader receipt-loader < "$f"
    done

All data is made up. The same --seed always produces the same receipts.
"""
import argparse
import json
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

from receipt_loader.models.receipt import Receipt

# (raw_name as printed, category_id, unit, min_price, max_price)
# For "kg" items the price is per kg and a weight is generated.
SUPERMARKET_ITEMS = [
    ("BIO VOLLMILCH 3,8%", 2, "L", 1.19, 1.39),
    ("H-MILCH 1,5%", 2, "L", 0.99, 1.09),
    ("JOGHURT NATUR 3,5%", 2, "Stück", 0.59, 0.89),
    ("GOUDA JUNG SCHEIBEN", 2, "Stück", 1.79, 2.29),
    ("BUTTER MILDGES.", 2, "Stück", 2.19, 2.49),
    ("EIER FREILAND 10ER", 2, "Pack", 2.99, 3.49),
    ("VOLLKORNBROT", 3, "Stück", 1.99, 2.49),
    ("BROETCHEN", 3, "Stück", 0.29, 0.39),
    ("TOASTBROT", 3, "Stück", 1.29, 1.59),
    ("BANANEN", 4, "kg", 1.49, 1.79),
    ("AEPFEL ELSTAR", 4, "kg", 2.49, 2.99),
    ("TOMATEN RISPEN", 4, "kg", 2.99, 3.99),
    ("GURKE", 4, "Stück", 0.59, 0.89),
    ("KARTOFFELN FESTK.", 4, "Pack", 2.49, 2.99),
    ("ZWIEBELN", 4, "Pack", 1.29, 1.59),
    ("PAPRIKA ROT", 4, "kg", 3.99, 4.99),
    ("HAEHNCHENBRUSTFILET", 1, "kg", 9.99, 12.99),
    ("RINDERHACKFLEISCH", 1, "Stück", 3.99, 4.99),
    ("SALAMI GESCHNITTEN", 1, "Stück", 1.49, 1.99),
    ("MINERALWASSER 6X1,5L", 5, "Pack", 1.99, 2.99),
    ("ORANGENSAFT 1L", 5, "L", 1.49, 1.99),
    ("KAFFEE GEMAHLEN 500G", 5, "Stück", 4.99, 6.99),
    ("SCHOKOLADE VOLLMILCH", 6, "Stück", 0.99, 1.49),
    ("KARTOFFELCHIPS", 6, "Stück", 1.49, 1.99),
    ("SPAGHETTI 500G", 7, "Stück", 0.79, 1.29),
    ("BASMATI REIS 1KG", 7, "Stück", 2.49, 3.29),
    ("PASSIERTE TOMATEN", 7, "Stück", 0.69, 0.99),
    ("OLIVENOEL EXTRA V.", 7, "Stück", 5.99, 7.99),
    ("TK PIZZA SALAMI", 8, "Stück", 2.49, 3.49),
    ("TK SPINAT", 8, "Stück", 1.29, 1.69),
    ("KUECHENROLLE 4ER", 9, "Pack", 2.49, 3.29),
    ("SPUELMITTEL", 9, "Stück", 0.99, 1.49),
    ("FERTIGSALAT CAESAR", 13, "Stück", 2.49, 3.29),
    ("WINDELN GR.4", 14, "Pack", 7.99, 9.99),
    # Items the extraction step is unsure about -> Uncategorized (12)
    ("PROBIER-SET AKTION", 12, "Stück", 1.99, 2.99),
    ("SAISONARTIKEL", 12, "Stück", 2.99, 4.99),
]

DRUGSTORE_ITEMS = [
    ("ZAHNPASTA SENSITIVE", 10, "Stück", 0.95, 1.95),
    ("DUSCHGEL MEN", 10, "Stück", 0.95, 1.65),
    ("SHAMPOO REPAIR", 10, "Stück", 1.45, 2.95),
    ("DEOROLLER", 10, "Stück", 1.95, 3.95),
    ("HANDSEIFE NACHF.", 10, "Stück", 0.85, 1.45),
    ("WASCHMITTEL COLOR", 9, "Stück", 4.95, 6.95),
    ("TOILETTENPAPIER 8ER", 9, "Pack", 3.45, 4.25),
    ("FEUCHTTUECHER BABY", 14, "Pack", 0.95, 1.95),
    ("BIO HAFERFLOCKEN", 7, "Stück", 0.95, 1.45),
]

ETHNIC_GROCERY_ITEMS = [
    ("BASMATI REIS 5KG", 7, "Stück", 9.99, 13.99),
    ("ROTE LINSEN 1KG", 7, "Stück", 2.49, 3.49),
    ("KICHERERBSEN 1KG", 7, "Stück", 2.29, 2.99),
    ("ATTA MEHL 5KG", 7, "Stück", 5.99, 7.99),
    ("GHEE 500G", 2, "Stück", 6.99, 8.99),
    ("PANEER", 2, "Stück", 2.99, 3.99),
    ("KORIANDER FRISCH", 4, "Stück", 0.79, 0.99),
    ("INGWER", 4, "kg", 3.99, 4.99),
    ("KNOBLAUCH", 4, "Stück", 0.49, 0.79),
    ("GARAM MASALA 100G", 7, "Stück", 1.99, 2.79),
    ("KURKUMA 100G", 7, "Stück", 1.49, 1.99),
    ("FLADENBROT", 3, "Stück", 0.99, 1.49),
    ("MANGO LASSI", 5, "Stück", 1.49, 1.99),
    ("SAMOSA TK 10ER", 8, "Pack", 3.99, 4.99),
]

# store: (relative visit frequency, item catalogue, (min_items, max_items))
STORES = {
    "REWE": (5, SUPERMARKET_ITEMS, (5, 14)),
    "Lidl": (5, SUPERMARKET_ITEMS, (5, 14)),
    "Aldi": (3, SUPERMARKET_ITEMS, (4, 11)),
    "Edeka": (2, SUPERMARKET_ITEMS, (3, 9)),
    "Netto": (1, SUPERMARKET_ITEMS, (2, 6)),
    "dm": (2, DRUGSTORE_ITEMS, (2, 5)),
    "Rossmann": (1, DRUGSTORE_ITEMS, (2, 4)),
    "Watan": (1, ETHNIC_GROCERY_ITEMS, (3, 8)),
    "Bamayan": (1, ETHNIC_GROCERY_ITEMS, (3, 7)),
    "Go India": (1, ETHNIC_GROCERY_ITEMS, (3, 7)),
}

ITEM_DISCOUNT_RATE = 0.10   # share of items with a promotion
BASKET_COUPON_RATE = 0.08   # share of receipts with a store-wide coupon


def shopping_time(rng: random.Random, day: date) -> time:
    """Weekday evenings and Saturday mornings, like a typical working household."""
    if day.weekday() == 5:  # Saturday
        start, end = 9 * 60, 14 * 60
    else:
        start, end = 17 * 60, 20 * 60 + 30
    minute = rng.randint(start, end)
    return time(minute // 60, minute % 60, rng.randint(0, 59))


def make_item(rng: random.Random, entry: tuple) -> tuple[dict, str | None]:
    raw_name, category_id, unit, lo, hi = entry
    # Shop prices end in 9 (e.g. 1.49, 2.79), as on real German receipts
    unit_price = round(int(rng.uniform(lo, hi) * 10) / 10 + 0.09, 2)

    if unit == "kg":
        quantity = round(rng.uniform(0.3, 1.6), 3)
    elif raw_name == "BROETCHEN":
        quantity = rng.choice([4, 6, 8])
    else:
        quantity = rng.choices([1, 2, 3], weights=[80, 15, 5])[0]

    total = round(unit_price * quantity, 2)
    warning = None
    is_discounted = rng.random() < ITEM_DISCOUNT_RATE
    if is_discounted:
        discounted = round(total * 0.8, 2)
        warning = f"{raw_name}: list price €{total:.2f} adjusted to €{discounted:.2f} (20% Aktion)"
        total = discounted
    if category_id == 12:
        warning = f"{raw_name}: no clear category — defaulted to Uncategorized (12)"

    item = {
        "raw_name": raw_name,
        "category_id": category_id,
        "quantity": quantity,
        "unit": unit,
        "unit_price": unit_price,
        "total_price": total,
        "is_discounted": is_discounted,
    }
    return item, warning


def make_receipt(rng: random.Random, day: date, store: str) -> dict:
    _, catalogue, (min_items, max_items) = STORES[store]
    at = shopping_time(rng, day)
    entries = rng.sample(catalogue, k=min(rng.randint(min_items, max_items), len(catalogue)))

    items, warnings = [], []
    for entry in entries:
        item, warning = make_item(rng, entry)
        items.append(item)
        if warning:
            warnings.append(warning)

    subtotal = round(sum(i["total_price"] for i in items), 2)
    store_wide_discount = 0.0
    if subtotal > 20 and rng.random() < BASKET_COUPON_RATE:
        store_wide_discount = round(subtotal * 0.10, 2)
        warnings.append(f"10% COUPON (€{store_wide_discount:.2f}) applied as store_wide_discount")

    return {
        "receipt_id": f"{day:%Y%m%d}-{store.lower().replace(' ', '')}-{at:%H%M%S}",
        "store": store,
        "date": day.isoformat(),
        "time": at.isoformat(),
        "receipt_total": round(subtotal - store_wide_discount, 2),
        "store_wide_discount": store_wide_discount,
        "items": items,
        "warnings": warnings,
    }


def generate(start: date, end: date, seed: int) -> list[dict]:
    rng = random.Random(seed)
    stores = list(STORES)
    weights = [STORES[s][0] for s in stores]

    receipts, day = [], start
    while day <= end:
        # Shops are closed on Sundays in Germany; ~40% chance of a trip on other days
        if day.weekday() != 6 and rng.random() < 0.4:
            store = rng.choices(stores, weights=weights)[0]
            receipt = make_receipt(rng, day, store)
            Receipt.model_validate(receipt)  # same validation the real loader uses
            receipts.append(receipt)
        day += timedelta(days=1)
    return receipts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2026, 5, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 10, 31))
    parser.add_argument("--seed", type=int, default=398)
    parser.add_argument("--out", type=Path, default=Path("demo_data"))
    args = parser.parse_args()

    receipts = generate(args.start, args.end, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    for r in receipts:
        (args.out / f"{r['receipt_id']}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")

    total = sum(r["receipt_total"] for r in receipts)
    print(f"Wrote {len(receipts)} receipts ({args.start} → {args.end}), total €{total:.2f}, to {args.out}/")


if __name__ == "__main__":
    main()
