import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.repository.news_repository import build_article_id, save_news
from src.signals.aggregate import calculate_daily_signals


class NewsRepositoryTests(unittest.TestCase):
    def test_article_id_is_stable_for_the_same_source_url(self) -> None:
        first = {
            "source": "megawhat",
            "url": "https://example.com/article",
            "title": "Original title",
        }
        updated = {
            "source": "MegaWhat",
            "url": "https://example.com/article",
            "title": "Updated title",
        }

        self.assertEqual(build_article_id(first), build_article_id(updated))

    def test_repository_rejects_non_energy_categories(self) -> None:
        with self.assertRaises(ValueError):
            save_news([{"category": "unsupported"}])


class DailySignalTests(unittest.TestCase):
    def test_zero_total_relevance_produces_neutral_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            news_path = root / "news.csv"
            scores_path = root / "scores.csv"

            pd.DataFrame(
                [
                    {
                        "article_id": "article-1",
                        "source": "megawhat",
                        "title": "Example",
                        "summary": "Example summary",
                        "url": "https://example.com/article-1",
                        "published_at": "2026-01-05T12:00:00+00:00",
                        "fetched_at": "2026-01-05T13:00:00+00:00",
                        "category": "energy_br",
                    }
                ]
            ).to_csv(news_path, index=False)
            pd.DataFrame(
                [
                    {
                        "article_id": "article-1",
                        "sentiment": "neutral",
                        "score": 0.8,
                        "relevance": 0.0,
                        "reason": "No material price impact.",
                        "model": "test-model",
                        "prompt_version": "test-prompt",
                        "analyzed_at": "2026-01-05T13:01:00+00:00",
                    }
                ]
            ).to_csv(scores_path, index=False)

            with (
                patch("src.signals.aggregate.ENERGY_NEWS_PATH", news_path),
                patch(
                    "src.signals.aggregate.ENERGY_NEWS_SCORES_PATH",
                    scores_path,
                ),
            ):
                daily = calculate_daily_signals()

            self.assertEqual(float(daily.iloc[0]["signal"]), 0.0)
            self.assertEqual(daily.iloc[0]["trend"], "NEUTRAL")


if __name__ == "__main__":
    unittest.main()
