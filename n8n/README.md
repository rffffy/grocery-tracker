# n8n workflows

Exported n8n workflows that move receipt JSON from Google Drive into Supabase.

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| [`single-receipt-ingest-polling.json`](workflows/single-receipt-ingest-polling.json) | Google Drive polling (daily at 22:00) | Picks up each new receipt JSON in the inbox folder, runs it through `receipt-loader`, sends a Telegram message for new product aliases, and moves the file to the processed folder |
| [`receipt-backfill.json`](workflows/receipt-backfill.json) | Manual | Processes every file currently in the inbox folder in one run. Used for the initial backfill. |

## Flow

```
Drive trigger / list inbox
  → Download file
  → Write to temp file
  → Run receipt-loader (uv run … < tmp.json)
  → Parse stdout JSON
  → New aliases? ──yes──→ Telegram notification ─┐
                 └─no──────────────────────────────┴→ Move file to /processed
```

## Importing

1. In n8n, go to **Workflows → Import from File** and choose a JSON file from `workflows/`.
2. Create (or select) these credentials on the nodes that need them:
   - **Google Drive OAuth2** for the trigger, download, list and move nodes
   - **Telegram API** for the notification node
3. Replace the placeholders:

| Placeholder | Where | Value |
|-------------|-------|-------|
| `<DRIVE_INBOX_FOLDER_ID>` | Drive trigger / "List Inbox Files" query | ID of your `Receipts/Inbox` folder (the last part of the folder URL) |
| `<DRIVE_PROCESSED_FOLDER_ID>` | "Move To Processed" | ID of your `Receipts/Processed` folder |
| `<TELEGRAM_CHAT_ID>` | "Notify New Aliases" | Your Telegram chat ID |
| `<GOOGLE_DRIVE_CREDENTIAL_ID>`, `<TELEGRAM_CREDENTIAL_ID>` | Credential fields | Pick your own credentials in the UI; n8n replaces these automatically |

The "Run receipt-loader" node expects the Python package at `/home/node/project`, which is where the project's `Dockerfile` puts it.
