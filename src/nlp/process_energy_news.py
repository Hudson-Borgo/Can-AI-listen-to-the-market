from datetime import datetime, timezone
import time

import pandas as pd

from src import console
from src.nlp.analyze import MODEL, analyze_news
from src.nlp.prompts.energy_br import PROMPT_VERSION, SYSTEM_PROMPT
from src.paths import ENERGY_NEWS_PATH, ENERGY_NEWS_SCORES_PATH


SCORE_COLUMNS = [
    "article_id",
    "sentiment",
    "score",
    "relevance",
    "reason",
    "model",
    "prompt_version",
    "analyzed_at",
]


def _write_scores(scores: pd.DataFrame) -> None:
    ENERGY_NEWS_SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = ENERGY_NEWS_SCORES_PATH.with_suffix(".csv.tmp")
    scores.to_csv(temporary_path, index=False)
    temporary_path.replace(ENERGY_NEWS_SCORES_PATH)


def process_energy_news(show_header: bool = True) -> dict:
    """Analyze news not yet scored by the active model and prompt version."""

    if show_header:
        console.banner(
            "SENTIR",
            "Análise de notícias com IA",
            "Impacto esperado no preço BBCE eHub M+1",
        )

    console.label("Mercado", "Energia elétrica — BBCE eHub M+1")
    console.label("Modelo", MODEL, "bright_cyan")
    console.label("Prompt", PROMPT_VERSION)
    console.label("Notícias", ENERGY_NEWS_PATH)
    console.label("Avaliações", ENERGY_NEWS_SCORES_PATH)

    if not ENERGY_NEWS_PATH.exists():
        console.error("Base silver de notícias não encontrada.")
        return {"processed": 0, "errors": 0, "remaining": 0}

    news = pd.read_csv(ENERGY_NEWS_PATH)

    if ENERGY_NEWS_SCORES_PATH.exists():
        scores = pd.read_csv(ENERGY_NEWS_SCORES_PATH)
    else:
        scores = pd.DataFrame(columns=SCORE_COLUMNS)

    current_scores = scores[
        (scores.get("model") == MODEL)
        & (scores.get("prompt_version") == PROMPT_VERSION)
    ]
    analyzed_ids = set(current_scores["article_id"].dropna().astype(str))
    pending = news[~news["article_id"].astype(str).isin(analyzed_ids)]

    console.divider()
    console.label("Total disponível", len(news))
    console.label("Já analisadas", len(news) - len(pending), "green")
    console.label("Pendentes", len(pending), "yellow")

    if pending.empty:
        console.success("Todas as notícias já foram analisadas nesta versão.")
        return {"processed": 0, "errors": 0, "remaining": 0}

    processed = 0
    errors = 0

    for current, row in enumerate(pending.itertuples(index=False), start=1):
        console.analysis_started(current, len(pending), row.title)

        try:
            result = analyze_news(
                title=row.title,
                summary=row.summary,
                system_prompt=SYSTEM_PROMPT,
            )

            score_record = {
                "article_id": row.article_id,
                "sentiment": result["sentiment"],
                "score": result["score"],
                "relevance": result["relevance"],
                "reason": result["reason"],
                "model": MODEL,
                "prompt_version": PROMPT_VERSION,
                "analyzed_at": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
            }
            scores = pd.concat(
                [scores, pd.DataFrame([score_record])],
                ignore_index=True,
            ).reindex(columns=SCORE_COLUMNS)
            _write_scores(scores)
            processed += 1

            console.analysis_result(result)
            console.success("Avaliação salva na camada silver")

        except Exception as error:
            errors += 1
            console.error(f"Não foi possível analisar: {error}")

    remaining = len(pending) - processed
    console.divider("═", "blue")
    console.success("Análise com IA concluída")
    console.label("Processadas", processed, "green")
    console.label("Erros", errors, "red" if errors else "green")
    console.label("Pendentes", remaining, "yellow" if remaining else "green")
    console.divider("═", "blue")

    return {"processed": processed, "errors": errors, "remaining": remaining}


def replay_energy_news_analysis(limit: int = 5, delay: float = 0.35) -> None:
    """Replay stored AI results for a deterministic, read-only live demo."""

    if not ENERGY_NEWS_PATH.exists() or not ENERGY_NEWS_SCORES_PATH.exists():
        raise FileNotFoundError("Notícias ou avaliações silver não encontradas.")

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
    replay = news.merge(
        latest_scores,
        on="article_id",
        how="inner",
        validate="one_to_one",
    )
    replay["published_at"] = pd.to_datetime(
        replay["published_at"], utc=True, errors="coerce"
    )
    replay = replay.sort_values("published_at", ascending=False).head(limit)

    console.banner(
        "SENTIR · REPLAY",
        "Análise de notícias com IA",
        "Demonstração determinística com avaliações já armazenadas",
    )
    console.warning("Modo replay: nenhuma API será chamada e nenhum dado será alterado.")
    console.label("Notícias exibidas", len(replay))
    console.divider()

    for index, row in enumerate(replay.itertuples(index=False), start=1):
        console.analysis_started(index, len(replay), row.title)
        if delay:
            time.sleep(delay)
        console.analysis_result(
            {
                "sentiment": row.sentiment,
                "score": row.score,
                "relevance": row.relevance,
                "reason": row.reason,
            }
        )
        console.success("Avaliação recuperada da camada silver")

    console.divider("═", "blue")
    console.success("Replay concluído — resultados oficiais preservados")
    console.divider("═", "blue")


if __name__ == "__main__":
    process_energy_news()
