import unittest
from unittest.mock import patch

from click.testing import CliRunner

from src.cli import cli


class DemoCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_help_lists_every_demo_component(self) -> None:
        result = self.runner.invoke(cli, ["--help"])

        self.assertEqual(result.exit_code, 0)
        for command in ("collect", "analyze", "signal", "run", "dashboard"):
            self.assertIn(command, result.output)

    @patch("src.cli.collect_and_store")
    def test_collect_forwards_the_requested_limit(self, collect_and_store) -> None:
        result = self.runner.invoke(cli, ["collect", "--limit", "5"])

        self.assertEqual(result.exit_code, 0)
        collect_and_store.assert_called_once_with(limit=5)

    @patch("src.cli.run_pipeline")
    def test_run_forwards_the_requested_limit(self, run_pipeline) -> None:
        result = self.runner.invoke(cli, ["run", "--limit", "3"])

        self.assertEqual(result.exit_code, 0)
        run_pipeline.assert_called_once_with(limit=3)

    @patch("src.cli.replay_energy_news_analysis")
    @patch("src.cli.process_energy_news")
    def test_analyze_replay_does_not_run_live_analysis(
        self,
        process_energy_news,
        replay_energy_news_analysis,
    ) -> None:
        result = self.runner.invoke(cli, ["analyze", "--replay", "4"])

        self.assertEqual(result.exit_code, 0)
        replay_energy_news_analysis.assert_called_once_with(limit=4)
        process_energy_news.assert_not_called()


if __name__ == "__main__":
    unittest.main()
