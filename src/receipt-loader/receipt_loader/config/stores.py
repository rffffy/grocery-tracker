STORE_ALIASES: dict[str, str] = {
    "rewe": "REWE",
    "lidl": "Lidl",
    "edeka": "Edeka",
    "aldi": "Aldi",
    "penny": "Penny",
    "kaufland": "Kaufland",
    "dm": "dm",
    "rossmann": "Rossmann",
    "netto": "Netto",
    "watan": "Watan",
    "bamayan": "Bamayan",
    "go india": "Go India",
}


def normalize_store(raw: str) -> str:
    canonical = STORE_ALIASES.get(raw.strip().lower())
    if not canonical:
        raise ValueError(f"Unknown store: {raw!r}. Add it to STORE_ALIASES in config/stores.py.")
    return canonical
