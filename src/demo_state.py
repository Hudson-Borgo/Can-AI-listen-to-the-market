"""Small local state used to connect separate live-demo commands."""

from datetime import datetime, timezone
import json

from src.paths import PROJECT_ROOT
from src.repository.news_repository import build_article_id


RUNTIME_DIR = PROJECT_ROOT / ".runtime"
LAST_COLLECTION_PATH = RUNTIME_DIR / "last_collection.json"


def save_last_collection(news: list[dict]) -> list[str]:
    """Remember the most recently displayed collector batch."""

    article_ids = [build_article_id(item) for item in news]
    payload = {
        "article_ids": article_ids,
        "saved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = LAST_COLLECTION_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(LAST_COLLECTION_PATH)
    return article_ids


def load_last_collection_ids() -> list[str]:
    """Load the last collector batch, returning an empty list if unavailable."""

    if not LAST_COLLECTION_PATH.exists():
        return []

    try:
        payload = json.loads(LAST_COLLECTION_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    article_ids = payload.get("article_ids", [])
    if not isinstance(article_ids, list):
        return []
    return [str(article_id) for article_id in article_ids if article_id]
