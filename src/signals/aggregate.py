import pandas as pd

from src import console
from src.paths import (
    ENERGY_NEWS_PATH,
    ENERGY_NEWS_SCORES_PATH,
    ENERGY_NEWS_SIGNAL_PATH,
)


def classify_signal(signal: float) -> str:
    if signal > 0.15:
        return "POSITIVE"
    if signal < -0.15:
        return "NEGATIVE"
    return "NEUTRAL"


def load_scored_energy_news() -> pd.DataFrame:
    """Join normalized news to the latest available analysis per article."""

    if not ENERGY_NEWS_PATH.exists():
        raise FileNotFoundError(f"News dataset not found: {ENERGY_NEWS_PATH}")
    if not ENERGY_NEWS_SCORES_PATH.exists():
        raise FileNotFoundError(
            f"NLP scores dataset not found: {ENERGY_NEWS_SCORES_PATH}"
        )

    news = pd.read_csv(ENERGY_NEWS_PATH)
    scores = pd.read_csv(ENERGY_NEWS_SCORES_PATH)

    scores["_row_order"] = range(len(scores))
    scores["_analyzed_at"] = pd.to_datetime(
        scores["analyzed_at"], utc=True, errors="coerce"
    )
    latest_scores = (
        scores.sort_values(
            ["article_id", "_analyzed_at", "_row_order"],
            na_position="first",
        )
        .drop_duplicates("article_id", keep="last")
        .drop(columns=["_row_order", "_analyzed_at"])
    )

    return news.merge(
        latest_scores,
        on="article_id",
        how="inner",
        validate="one_to_one",
    )


def calculate_daily_signals(persist: bool = False) -> pd.DataFrame:
    """Calculate the daily news signal for Brazilian electricity prices."""

    analyzed = load_scored_energy_news()
    analyzed["score"] = pd.to_numeric(analyzed["score"], errors="coerce")
    analyzed["relevance"] = pd.to_numeric(
        analyzed["relevance"], errors="coerce"
    )
    analyzed["published_at"] = pd.to_datetime(
        analyzed["published_at"], utc=True, errors="coerce"
    )
    analyzed = analyzed.dropna(
        subset=["published_at", "score", "relevance"]
    ).copy()

    if analyzed.empty:
        raise ValueError("No analyzed Brazilian energy news found.")

    analyzed["date"] = analyzed["published_at"].dt.date
    analyzed["weighted_score"] = analyzed["score"] * analyzed["relevance"]

    daily = (
        analyzed.groupby("date")
        .agg(
            articles=("score", "count"),
            weighted_sum=("weighted_score", "sum"),
            total_relevance=("relevance", "sum"),
            average_relevance=("relevance", "mean"),
        )
        .reset_index()
    )
    daily["signal"] = 0.0
    has_relevance = daily["total_relevance"] > 0
    daily.loc[has_relevance, "signal"] = (
        daily.loc[has_relevance, "weighted_sum"]
        / daily.loc[has_relevance, "total_relevance"]
    )
    daily["trend"] = daily["signal"].apply(classify_signal)
    daily["signal"] = daily["signal"].round(3)
    daily["average_relevance"] = daily["average_relevance"].round(3)

    result = daily[
        ["date", "articles", "average_relevance", "signal", "trend"]
    ]

    if persist:
        ENERGY_NEWS_SIGNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = ENERGY_NEWS_SIGNAL_PATH.with_suffix(".csv.tmp")
        result.to_csv(temporary_path, index=False)
        temporary_path.replace(ENERGY_NEWS_SIGNAL_PATH)

    return result


def calculate_and_present(show_header: bool = True) -> pd.DataFrame:
    """Persist and display the recent daily signal history."""

    if show_header:
        console.banner(
            "SENTIR",
            "Consolidação do sinal de notícias",
            "Notícias avaliadas → feature diária para os modelos",
        )

    daily_signals = calculate_daily_signals(persist=True)
    current = daily_signals.iloc[-1]

    console.label("Mercado", "Energia elétrica — BBCE eHub M+1")
    console.label("Fórmula", "Σ(score × relevância) / Σ(relevância)")
    console.label("Destino gold", ENERGY_NEWS_SIGNAL_PATH)
    console.signal_table(daily_signals)
    console.final_signal(current)
    console.success("Sinal de notícias atualizado na camada gold")

    return daily_signals


def main() -> None:
    calculate_and_present()


if __name__ == "__main__":
    main()
