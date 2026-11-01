import os

import psycopg

from receipt_loader.models.receipt import Receipt


async def load_receipt(receipt: Receipt) -> dict:
    db_url = os.environ["SUPABASE_DB_URL"]

    async with await psycopg.AsyncConnection.connect(db_url, prepare_threshold=None) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM receipts WHERE receipt_id = %s",
                (receipt.receipt_id,),
            )
            if await cur.fetchone():
                return {"status": "skipped", "receipt_id": receipt.receipt_id}

        new_aliases: list[dict] = []

        async with conn.transaction():
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO receipts (receipt_id, date, time, store, receipt_total, store_wide_discount)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        receipt.receipt_id,
                        receipt.date,
                        receipt.time,
                        receipt.store,
                        receipt.receipt_total,
                        receipt.store_wide_discount,
                    ),
                )

                for item in receipt.items:
                    await cur.execute(
                        """
                        INSERT INTO product_aliases (raw_name, store, category_id)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (raw_name, store) DO NOTHING
                        RETURNING alias_id
                        """,
                        (item.raw_name, receipt.store, item.category_id),
                    )
                    row = await cur.fetchone()
                    if row:
                        alias_id = row[0]
                        new_aliases.append({
                            "alias_id": alias_id,
                            "raw_name": item.raw_name,
                            "store": receipt.store,
                            "category_id": item.category_id,
                        })
                    else:
                        await cur.execute(
                            "SELECT alias_id FROM product_aliases WHERE raw_name = %s AND store = %s",
                            (item.raw_name, receipt.store),
                        )
                        alias_id = (await cur.fetchone())[0]

                    await cur.execute(
                        """
                        INSERT INTO receipt_items
                            (receipt_id, alias_id, raw_name, quantity, unit, unit_price, total_price, is_discounted)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            receipt.receipt_id,
                            alias_id,
                            item.raw_name,
                            item.quantity,
                            item.unit,
                            item.unit_price,
                            item.total_price,
                            item.is_discounted,
                        ),
                    )

        return {
            "status": "inserted",
            "receipt_id": receipt.receipt_id,
            "num_items": len(receipt.items),
            "new_aliases": new_aliases,
        }
