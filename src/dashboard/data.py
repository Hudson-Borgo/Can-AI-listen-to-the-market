import pandas as pd

from src.paths import ENERGY_NEWS_SIGNAL_PATH
from src.signals.aggregate import load_scored_energy_news


def load_energy_news() -> pd.DataFrame:
    """Load normalized news joined to its latest LLM analysis."""

    news = load_scored_energy_news()
    news["score"] = pd.to_numeric(news["score"], errors="coerce")
    news["relevance"] = pd.to_numeric(news["relevance"], errors="coerce")
    news["published_at"] = pd.to_datetime(
        news["published_at"], utc=True, errors="coerce"
    )
    return news


def load_daily_signals() -> pd.DataFrame:
    """Load the persisted gold daily signal dataset."""

    if not ENERGY_NEWS_SIGNAL_PATH.exists():
        raise FileNotFoundError(
            f"Daily signal dataset not found: {ENERGY_NEWS_SIGNAL_PATH}. "
            "Run `python -m src.signals.aggregate` first."
        )

    signals = pd.read_csv(ENERGY_NEWS_SIGNAL_PATH)
    signals["date"] = pd.to_datetime(signals["date"], errors="coerce").dt.date
    return signals
