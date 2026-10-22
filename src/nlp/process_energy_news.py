from datetime import datetime, timezone

import pandas as pd

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
        print("\n" + "=" * 70)
        print("  AI ENERGY PRICE ANALYSIS")
        print("=" * 70)

    print("\nMarket   : Brazilian electricity — BBCE eHub M+1")
    print(f"News     : {ENERGY_NEWS_PATH}")
    print(f"Scores   : {ENERGY_NEWS_SCORES_PATH}")
    print(f"Model    : {MODEL}")
    print(f"Prompt   : {PROMPT_VERSION}")

    if not ENERGY_NEWS_PATH.exists():
        print("\n✗ Silver news dataset not found.")
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

    print(f"Articles : {len(news)}")
    print(f"Pending  : {len(pending)}")

    if pending.empty:
        print("\n✓ All articles already analyzed for this model and prompt.")
        return {"processed": 0, "errors": 0, "remaining": 0}

    processed = 0
    errors = 0

    for current, row in enumerate(pending.itertuples(index=False), start=1):
        print("-" * 70)
        print(f"[{current}/{len(pending)}] {row.title}")

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

            print(
                f"Result    : {result['sentiment'].upper()} "
                f"({result['score']})"
            )
            print(f"Relevance : {result['relevance']}")
            print("Saved     : ✓")

        except Exception as error:
            errors += 1
            print(f"✗ Error: {error}")

    remaining = len(pending) - processed
    print("\n" + "=" * 70)
    print("  ✓ AI ANALYSIS COMPLETED")
    print(f"  Processed : {processed}")
    print(f"  Errors    : {errors}")
    print(f"  Remaining : {remaining}")
    print("=" * 70 + "\n")

    return {"processed": processed, "errors": errors, "remaining": remaining}


if __name__ == "__main__":
    process_energy_news()
