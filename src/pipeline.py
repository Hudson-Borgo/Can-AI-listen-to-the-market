from src.collectors.megawhat import collect_news
from src.nlp.analyze import MODEL
from src.nlp.process_energy_news import process_energy_news
from src.normalization.megawhat import normalize_news
from src.repository.news_repository import save_news, save_raw_news
from src.signals.aggregate import calculate_daily_signals


def main() -> None:
    """Run the Brazilian electricity news pipeline end to end."""

    print("\n" + "=" * 70)
    print("  BRAZILIAN ELECTRICITY MARKET INTELLIGENCE")
    print("  Target: BBCE eHub M+1 daily closing price")
    print("=" * 70)

    print("\n[1/6] COLLECTING MEGAWHAT NEWS")
    raw_news = collect_news()
    print(f"      Collected : {len(raw_news)}")

    print("\n[2/6] SAVING BRONZE SOURCE RECORDS")
    bronze_result = save_raw_news(raw_news)
    print(f"      New        : {bronze_result['inserted']}")
    print(f"      Duplicates : {bronze_result['duplicates']}")
    print(f"      Total      : {bronze_result['total']}")

    print("\n[3/6] NORMALIZING NEWS")
    normalized_news = [normalize_news(item) for item in raw_news]
    print(f"      Normalized : {len(normalized_news)}")

    print("\n[4/6] UPDATING SILVER NEWS DATASET")
    silver_result = save_news(normalized_news)
    print(f"      New        : {silver_result['inserted']}")
    print(f"      Duplicates : {silver_result['duplicates']}")
    print(f"      Total      : {silver_result['total']}")

    print("\n[5/6] ANALYZING IMPACT ON THE M+1 PRICE")
    print(f"      Model      : {MODEL}")
    process_energy_news(show_header=False)

    print("\n[6/6] PERSISTING GOLD DAILY SIGNAL")
    daily_signals = calculate_daily_signals(persist=True)
    current = daily_signals.iloc[-1]
    print(f"      Date       : {current['date']}")
    print(f"      Articles   : {current['articles']}")
    print(f"      Signal     : {current['signal']:+.3f}")
    print(f"      Trend      : {current['trend']}")

    print("\n" + "=" * 70)
    print("  ✓ PIPELINE COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
