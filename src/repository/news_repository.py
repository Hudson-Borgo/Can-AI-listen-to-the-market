from datetime import datetime, timezone
import hashlib
from pathlib import Path

import pandas as pd

from src.paths import ENERGY_NEWS_PATH, MEGAWHAT_RAW_NEWS_PATH


NEWS_COLUMNS = [
    "article_id",
    "source",
    "title",
    "summary",
    "url",
    "published_at",
    "fetched_at",
    "category",
]


def build_article_id(item: dict) -> str:
    """Build a stable identifier, preferring the source URL."""

    source = str(item.get("source", "")).strip().lower()
    url = str(item.get("url", "")).strip()

    if url:
        identity = f"{source}|{url}"
    else:
        title = str(item.get("title", "")).strip()
        published_at = str(item.get("published_at", "")).strip()
        identity = f"{source}|{title}|{published_at}"

    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _write_csv_atomic(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    df.to_csv(temporary_path, index=False)
    temporary_path.replace(path)


def _append_unique(
    new_df: pd.DataFrame,
    path: Path,
    key: str,
) -> tuple[int, int]:
    if path.exists():
        current_df = pd.read_csv(path)
        existing_keys = set(current_df[key].fillna("").astype(str))
        new_df = new_df[
            ~new_df[key].fillna("").astype(str).isin(existing_keys)
        ]
        final_df = pd.concat([current_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    _write_csv_atomic(final_df, path)
    return len(new_df), len(final_df)


def save_raw_news(news: list[dict]) -> dict:
    """Append source records to the immutable bronze news dataset."""

    received = len(news)
    if not news:
        return {"received": 0, "inserted": 0, "duplicates": 0, "total": 0}

    ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    records = []

    for item in news:
        record = dict(item)
        record["raw_id"] = build_article_id(item)
        record["ingested_at"] = ingested_at
        records.append(record)

    raw_df = pd.DataFrame(records)
    ordered_columns = [
        "raw_id",
        "source",
        "title",
        "summary",
        "url",
        "published_at",
        "category",
        "ingested_at",
    ]
    raw_df = raw_df.reindex(columns=ordered_columns)
    inserted, total = _append_unique(raw_df, MEGAWHAT_RAW_NEWS_PATH, "raw_id")

    return {
        "received": received,
        "inserted": inserted,
        "duplicates": received - inserted,
        "total": total,
    }


def save_news(news: list[dict]) -> dict:
    """Persist normalized Brazilian energy news in the silver layer."""

    received = len(news)
    if not news:
        return {"received": 0, "inserted": 0, "duplicates": 0, "total": 0}

    categories = {str(item.get("category", "")).strip() for item in news}
    if categories != {"energy_br"}:
        raise ValueError(
            "The energy pipeline only accepts records in category 'energy_br'."
        )

    records = []
    for item in news:
        record = dict(item)
        record["article_id"] = build_article_id(item)
        records.append(record)

    news_df = pd.DataFrame(records).reindex(columns=NEWS_COLUMNS)
    inserted, total = _append_unique(news_df, ENERGY_NEWS_PATH, "article_id")

    return {
        "received": received,
        "inserted": inserted,
        "duplicates": received - inserted,
        "total": total,
    }
