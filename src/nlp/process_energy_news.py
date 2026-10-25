from datetime import datetime, timezone
import time

import pandas as pd

from src import console
from src.demo_state import load_last_collection_ids
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


def _latest_current_scores(scores: pd.DataFrame) -> pd.DataFrame:
    """Return one current-model/current-prompt score per article."""

    required = {"article_id", "model", "prompt_version"}
    if not required.issubset(scores.columns):
        return pd.DataFrame(columns=SCORE_COLUMNS)

    current = scores[
        (scores["model"] == MODEL)
        & (scores["prompt_version"] == PROMPT_VERSION)
    ].copy()
    if current.empty:
        return current

    current["_row_order"] = range(len(current))
    current["_analyzed_at"] = pd.to_datetime(
        current.get("analyzed_at"), utc=True, errors="coerce"
    )
    return (
        current.sort_values(
            ["article_id", "_analyzed_at", "_row_order"],
            na_position="first",
        )
        .drop_duplicates("article_id", keep="last")
        .drop(columns=["_row_order", "_analyzed_at"])
    )


def _select_stored_analyses(
    news: pd.DataFrame,
    scores: pd.DataFrame,
    limit: int,
    article_ids: list[str] | None = None,
) -> pd.DataFrame:
    latest_scores = _latest_current_scores(scores)
    replay = news.merge(
        latest_scores,
        on="article_id",
        how="inner",
        validate="one_to_one",
    )

    if article_ids:
        demo_order = {
            article_id: index
            for index, article_id in enumerate(article_ids)
        }
        replay = replay[replay["article_id"].astype(str).isin(demo_order)].copy()
        replay["_demo_order"] = replay["article_id"].astype(str).map(demo_order)
        return replay.sort_values("_demo_order").drop(columns="_demo_order").head(limit)

    replay["published_at"] = pd.to_datetime(
        replay["published_at"], utc=True, errors="coerce"
    )
    return replay.sort_values("published_at", ascending=False).head(limit)


def _display_stored_analyses(replay: pd.DataFrame, delay: float = 0.35) -> int:
    total = len(replay)
    if not total:
        console.warning("Nenhuma notícia disponível para análise.")
        return 0

    for index, row in enumerate(replay.itertuples(index=False), start=1):
        console.analysis_started(
            index,
            total,
            row.title,
            status="ANÁLISE COM IA",
        )
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
        console.success("Análise concluída")

    return total


def process_energy_news(
    show_header: bool = True,
    replay_limit: int = 5,
    replay_delay: float = 0.35,
) -> dict:
    """Analyze pending news and replay stored results from the demo batch."""

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
        return {"processed": 0, "cached": 0, "errors": 0, "remaining": 0}

    news = pd.read_csv(ENERGY_NEWS_PATH)

    if ENERGY_NEWS_SCORES_PATH.exists():
        scores = pd.read_csv(ENERGY_NEWS_SCORES_PATH)
    else:
        scores = pd.DataFrame(columns=SCORE_COLUMNS)

    current_scores = _latest_current_scores(scores)
    analyzed_ids = set(current_scores["article_id"].dropna().astype(str))
    pending = news[~news["article_id"].astype(str).isin(analyzed_ids)]
    demo_batch_ids = load_last_collection_ids()

    console.divider()
    console.label("Total disponível", len(news))
    console.label(
        "Lote atual",
        f"{len(demo_batch_ids)} notícias" if demo_batch_ids else "últimas disponíveis",
        "bright_cyan",
    )

    processed = 0
    errors = 0
    processed_ids: set[str] = set()

    for current, row in enumerate(pending.itertuples(index=False), start=1):
        console.analysis_started(
            current,
            len(pending),
            row.title,
            status="ANÁLISE COM IA",
        )

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
            processed_ids.add(str(row.article_id))

            console.analysis_result(result)
            console.success("Análise concluída")

        except Exception as error:
            errors += 1
            console.error(f"Não foi possível analisar: {error}")

    remaining = len(pending) - processed
    cached_ids = [
        article_id
        for article_id in demo_batch_ids
        if article_id not in processed_ids
    ]
    should_fallback_to_latest = not demo_batch_ids and pending.empty
    cached = pd.DataFrame()

    if cached_ids or should_fallback_to_latest:
        console.section(
            "SENTIR",
            "Análise das notícias selecionadas",
        )
        cached = _select_stored_analyses(
            news,
            scores,
            limit=len(cached_ids) if cached_ids else replay_limit,
            article_ids=cached_ids or None,
        )
        _display_stored_analyses(cached, delay=replay_delay)

    console.divider("═", "blue")
    console.success("Análise com IA concluída")
    console.label("Análises exibidas", processed + len(cached), "green")
    console.label("Erros", errors, "red" if errors else "green")
    console.label("Pendentes", remaining, "yellow" if remaining else "green")
    console.divider("═", "blue")

    return {
        "processed": processed,
        "cached": len(cached),
        "errors": errors,
        "remaining": remaining,
    }


def replay_energy_news_analysis(limit: int = 5, delay: float = 0.35) -> int:
    """Replay stored AI results for a deterministic, read-only live demo."""

    if not ENERGY_NEWS_PATH.exists() or not ENERGY_NEWS_SCORES_PATH.exists():
        raise FileNotFoundError("Notícias ou avaliações silver não encontradas.")

    news = pd.read_csv(ENERGY_NEWS_PATH)
    scores = pd.read_csv(ENERGY_NEWS_SCORES_PATH)
    replay = _select_stored_analyses(news, scores, limit=limit)

    console.banner(
        "SENTIR",
        "Análise de notícias com IA",
        "Impacto esperado no preço BBCE eHub M+1",
    )
    console.label("Notícias selecionadas", len(replay))
    console.divider()

    displayed = _display_stored_analyses(replay, delay=delay)

    console.divider("═", "blue")
    console.success("Análise com IA concluída")
    console.divider("═", "blue")
    return displayed


if __name__ == "__main__":
    process_energy_news()
