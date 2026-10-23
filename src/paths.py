"""Canonical project and data paths.

All paths are resolved from the repository root so commands do not depend on
the caller's current working directory.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

BRONZE_DIR = DATA_DIR / "bronze"
BRONZE_NEWS_DIR = BRONZE_DIR / "news"
MEGAWHAT_RAW_NEWS_PATH = BRONZE_NEWS_DIR / "megawhat_news.csv"

SILVER_DIR = DATA_DIR / "silver"
SILVER_NEWS_DIR = SILVER_DIR / "news"
SILVER_NLP_DIR = SILVER_DIR / "nlp"
SILVER_MARKET_DIR = SILVER_DIR / "market"
ENERGY_NEWS_PATH = SILVER_NEWS_DIR / "br_energy_news.csv"
ENERGY_NEWS_SCORES_PATH = SILVER_NLP_DIR / "br_energy_news_scores.csv"
BBCE_EHUB_M1_PRICE_PATH = (
    SILVER_MARKET_DIR / "bbce_ehub_m1_closing_price_daily.csv"
)

GOLD_DIR = DATA_DIR / "gold"
GOLD_SIGNALS_DIR = GOLD_DIR / "signals"
GOLD_FEATURES_DIR = GOLD_DIR / "features"
GOLD_MODELING_DIR = GOLD_DIR / "modeling"
ENERGY_NEWS_SIGNAL_PATH = (
    GOLD_SIGNALS_DIR / "br_energy_news_signal_daily.csv"
)
ENERGY_NEWS_FEATURES_PATH = (
    GOLD_FEATURES_DIR / "br_energy_news_features_daily.csv"
)
BBCE_EHUB_M1_NEWS_FEATURES_PATH = (
    GOLD_MODELING_DIR / "bbce_ehub_m1_news_features_daily.csv"
)


def ensure_data_directories() -> None:
    """Create every data-layer directory used by the application."""

    for directory in (
        BRONZE_NEWS_DIR,
        SILVER_NEWS_DIR,
        SILVER_NLP_DIR,
        SILVER_MARKET_DIR,
        GOLD_SIGNALS_DIR,
        GOLD_FEATURES_DIR,
        GOLD_MODELING_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
