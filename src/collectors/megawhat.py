from collections.abc import Callable

import click
import feedparser
import requests
import yaml

from src import console
from src.normalization.megawhat import normalize_news
from src.paths import PROJECT_ROOT
from src.repository.news_repository import save_news, save_raw_news


CONFIG_PATH = PROJECT_ROOT / "config" / "sites" / "megawhat.yaml"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    cfg = yaml.safe_load(file)

RSS_URL = cfg["url"]
ArticleCallback = Callable[[int, int, dict], None]


def collect_news(
    limit: int = 10,
    on_article: ArticleCallback | None = None,
) -> list[dict]:
    """Collect the most recent articles from the MegaWhat RSS feed."""

    response = requests.get(
        RSS_URL,
        timeout=30,
        headers={"User-Agent": "Can-AI-Listen-to-the-Market/0.1"},
    )
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    entries = list(feed.entries[:limit])

    if not entries:
        detail = getattr(feed, "bozo_exception", "RSS feed returned no entries")
        raise RuntimeError(f"MegaWhat RSS could not be read: {detail}")

    news = []
    total = len(entries)

    for index, entry in enumerate(entries, start=1):
        item = {
            "source": cfg["site"],
            "title": entry.get("title", ""),
            "summary": entry.get("summary", ""),
            "url": entry.get("link", ""),
            "published_at": entry.get("published", ""),
            "category": cfg["category"],
        }
        news.append(item)
        if on_article:
            on_article(index, total, item)

    return news


def collect_and_store(limit: int = 10, show_header: bool = True) -> dict:
    """Collect, display, normalize and persist the most recent articles."""

    if show_header:
        console.banner(
            "OUVIR",
            "Coleta de notícias",
            "MegaWhat → bronze → silver",
        )

    console.label("Fonte", "MegaWhat")
    console.label("Feed", RSS_URL, "bright_cyan")
    console.label("Limite", limit)
    console.divider()

    try:
        raw_news = collect_news(limit=limit, on_article=console.article_collected)
    except Exception as exc:
        console.error(f"Falha na coleta: {exc}")
        raise

    bronze_result = save_raw_news(raw_news)
    normalized_news = [normalize_news(item) for item in raw_news]
    silver_result = save_news(normalized_news)

    console.divider()
    console.success(f"{len(raw_news)} notícias recebidas do feed")
    console.label("Novas na bronze", bronze_result["inserted"], "green")
    console.label("Novas na silver", silver_result["inserted"], "green")
    console.label("Duplicadas", silver_result["duplicates"], "yellow")
    console.label("Total silver", silver_result["total"])

    return {
        "raw_news": raw_news,
        "bronze": bronze_result,
        "silver": silver_result,
    }


@click.command()
@click.option(
    "--limit",
    default=10,
    show_default=True,
    type=click.IntRange(min=1),
    help="Quantidade máxima de notícias recentes.",
)
def main(limit: int) -> None:
    """Collect and persist MegaWhat news."""

    collect_and_store(limit=limit)


if __name__ == "__main__":
    main()
