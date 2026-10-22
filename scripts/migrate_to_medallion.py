"""Migrate the legacy CSV layout to the bronze/silver/gold structure.

The migration is idempotent. It never calls external sources or the LLM.
"""

from pathlib import Path
import shutil

import pandas as pd

from src.nlp.prompts.energy_br import PROMPT_VERSION
from src.paths import (
    BBCE_EHUB_M1_NEWS_FEATURES_PATH,
    BBCE_EHUB_M1_PRICE_PATH,
    ENERGY_NEWS_FEATURES_PATH,
    ENERGY_NEWS_PATH,
    ENERGY_NEWS_SCORES_PATH,
    PROJECT_ROOT,
    ensure_data_directories,
)
from src.repository.news_repository import NEWS_COLUMNS, build_article_id
from src.signals.aggregate import calculate_daily_signals


LEGACY_NEWS_PATH = PROJECT_ROOT / "data" / "processed" / "energy_br.csv"
LEGACY_MARKET_PATH = PROJECT_ROOT / "data" / "market" / "energy_market_daily.csv"
LEGACY_NEWS_FEATURES_PATH = (
    PROJECT_ROOT / "data" / "features" / "energy_news_daily.csv"
)
LEGACY_MODELING_PATH = (
    PROJECT_ROOT / "data" / "features" / "energy_market_news_daily.csv"
)
LEGACY_MODEL = "gpt-5.4-mini"


def write_csv_atomic(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    df.to_csv(temporary_path, index=False)
    temporary_path.replace(path)


def migrate_news() -> None:
    if not LEGACY_NEWS_PATH.exists():
        print("News: legacy dataset already migrated.")
        return

    legacy = pd.read_csv(LEGACY_NEWS_PATH)
    legacy["article_id"] = legacy.apply(
        lambda row: build_article_id(row.to_dict()), axis=1
    )
    legacy["_fetched_at"] = pd.to_datetime(
        legacy["fetched_at"], utc=True, errors="coerce"
    )
    deduplicated = (
        legacy.sort_values(["article_id", "_fetched_at"], na_position="first")
        .drop_duplicates("article_id", keep="last")
        .drop(columns="_fetched_at")
    )

    news = deduplicated.reindex(columns=NEWS_COLUMNS)
    scores = deduplicated[
        ["article_id", "sentiment", "score", "relevance", "reason"]
    ].copy()
    scores = scores.dropna(subset=["sentiment"])
    scores["model"] = LEGACY_MODEL
    scores["prompt_version"] = PROMPT_VERSION
    scores["analyzed_at"] = ""

    write_csv_atomic(news, ENERGY_NEWS_PATH)
    write_csv_atomic(scores, ENERGY_NEWS_SCORES_PATH)

    if len(news) != news["article_id"].nunique():
        raise RuntimeError("Migration produced duplicate article identifiers.")

    LEGACY_NEWS_PATH.unlink()
    print(
        f"News: migrated {len(legacy)} legacy rows to {len(news)} unique articles "
        f"and {len(scores)} scores."
    )


def move_if_needed(source: Path, destination: Path, label: str) -> None:
    if destination.exists():
        print(f"{label}: destination already exists.")
        return
    if not source.exists():
        print(f"{label}: no legacy file found.")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    print(f"{label}: moved to {destination.relative_to(PROJECT_ROOT)}.")


def remove_empty_legacy_directories() -> None:
    for directory in (
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "market",
        PROJECT_ROOT / "data" / "features",
    ):
        if directory.exists() and not any(directory.iterdir()):
            directory.rmdir()


def main() -> None:
    ensure_data_directories()
    migrate_news()
    move_if_needed(
        LEGACY_MARKET_PATH,
        BBCE_EHUB_M1_PRICE_PATH,
        "Market prices",
    )
    move_if_needed(
        LEGACY_NEWS_FEATURES_PATH,
        ENERGY_NEWS_FEATURES_PATH,
        "Daily news features",
    )
    move_if_needed(
        LEGACY_MODELING_PATH,
        BBCE_EHUB_M1_NEWS_FEATURES_PATH,
        "Modeling dataset",
    )
    remove_empty_legacy_directories()

    daily = calculate_daily_signals(persist=True)
    print(f"Daily signal: persisted {len(daily)} rows.")


if __name__ == "__main__":
    main()
