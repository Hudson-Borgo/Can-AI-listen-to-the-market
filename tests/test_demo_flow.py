import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
import pandas as pd

from src.cli import cli
from src.demo_state import load_last_collection_ids, save_last_collection
from src.nlp.analyze import MODEL
from src.nlp.prompts.energy_br import PROMPT_VERSION


class DemoStateTests(unittest.TestCase):
    def test_last_collection_round_trip(self) -> None:
        news = [
            {
                "source": "megawhat",
                "url": "https://example.com/energy-news",
                "title": "Energy news",
            }
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            runtime_dir = Path(temporary_directory)
            state_path = runtime_dir / "last_collection.json"
            with (
                patch("src.demo_state.RUNTIME_DIR", runtime_dir),
                patch("src.demo_state.LAST_COLLECTION_PATH", state_path),
            ):
                saved_ids = save_last_collection(news)
                loaded_ids = load_last_collection_ids()

        self.assertEqual(loaded_ids, saved_ids)
        self.assertEqual(len(loaded_ids), 1)


class StoredAnalysisDemoTests(unittest.TestCase):
    def test_default_analyze_displays_cached_result_without_calling_llm(self) -> None:
        article_id = "article-1"

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            news_path = root / "news.csv"
            scores_path = root / "scores.csv"
            pd.DataFrame(
                [
                    {
                        "article_id": article_id,
                        "source": "megawhat",
                        "title": "Reservatórios sobem no Sudeste",
                        "summary": "Resumo da notícia",
                        "url": "https://example.com/article-1",
                        "published_at": "2026-10-24T12:00:00+00:00",
                        "fetched_at": "2026-10-24T12:01:00+00:00",
                        "category": "energy_br",
                    }
                ]
            ).to_csv(news_path, index=False)
            pd.DataFrame(
                [
                    {
                        "article_id": article_id,
                        "sentiment": "negative",
                        "score": -0.6,
                        "relevance": 0.9,
                        "reason": "Maior oferta hídrica pressiona o preço para baixo.",
                        "model": MODEL,
                        "prompt_version": PROMPT_VERSION,
                        "analyzed_at": "2026-10-24T12:02:00+00:00",
                    }
                ]
            ).to_csv(scores_path, index=False)

            with (
                patch(
                    "src.nlp.process_energy_news.ENERGY_NEWS_PATH",
                    news_path,
                ),
                patch(
                    "src.nlp.process_energy_news.ENERGY_NEWS_SCORES_PATH",
                    scores_path,
                ),
                patch(
                    "src.nlp.process_energy_news.load_last_collection_ids",
                    return_value=[article_id],
                ),
                patch("src.nlp.process_energy_news.time.sleep"),
                patch("src.nlp.process_energy_news.analyze_news") as analyze_news,
            ):
                result = CliRunner().invoke(cli, ["analyze"])

        self.assertEqual(result.exit_code, 0, result.output)
        analyze_news.assert_not_called()
        self.assertIn("Reservatórios sobem no Sudeste", result.output)
        self.assertIn("ANÁLISE COM IA", result.output)
        self.assertIn("Análise concluída", result.output)
        self.assertNotIn("ANÁLISE ARMAZENADA", result.output)
        self.assertNotIn("nenhuma chamada à LLM", result.output)


if __name__ == "__main__":
    unittest.main()
