from src import console
from src.collectors.megawhat import collect_and_store
from src.nlp.process_energy_news import process_energy_news
from src.signals.aggregate import calculate_and_present


def run_pipeline(limit: int = 10) -> None:
    """Run the Brazilian electricity news pipeline end to end."""

    console.banner(
        "DEMO AO VIVO",
        "Can AI Listen to the Market?",
        "OUVIR notícias → SENTIR o mercado → PREVER tendências",
    )

    console.section("1/3 · OUVIR", "Coletar e estruturar as notícias")
    collect_and_store(limit=limit, show_header=False)

    console.section("2/3 · SENTIR", "Analisar o impacto com IA")
    process_energy_news(show_header=False)

    console.section("3/3 · PREVER", "Consolidar o sinal diário")
    calculate_and_present(show_header=False)

    console.divider("═", "blue")
    console.success("Pipeline concluída — dashboard pronto para a apresentação")
    console.divider("═", "blue")


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
