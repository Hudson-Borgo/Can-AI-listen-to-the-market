"""Command-line entry point for the live demonstration."""

import click

from src.collectors.megawhat import collect_and_store
from src.dashboard.run import launch_dashboard
from src.nlp.process_energy_news import (
    process_energy_news,
    replay_energy_news_analysis,
)
from src.pipeline import run_pipeline
from src.signals.aggregate import calculate_and_present


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """OUVIR, SENTIR e PREVER o mercado brasileiro de energia."""


@cli.command()
@click.option(
    "--limit",
    default=10,
    show_default=True,
    type=click.IntRange(min=1),
    help="Quantidade máxima de notícias recentes.",
)
def collect(limit: int) -> None:
    """Coletar notícias e atualizar as camadas bronze e silver."""

    collect_and_store(limit=limit)


@cli.command()
@click.option(
    "--replay",
    type=click.IntRange(min=1),
    metavar="N",
    help="Reexibir N análises salvas, sem chamar a API ou alterar dados.",
)
def analyze(replay: int | None) -> None:
    """Analisar com IA somente as notícias ainda pendentes."""

    if replay:
        replay_energy_news_analysis(limit=replay)
    else:
        process_energy_news()


@cli.command()
def signal() -> None:
    """Calcular e persistir o sinal diário na camada gold."""

    calculate_and_present()


@cli.command(name="run")
@click.option(
    "--limit",
    default=10,
    show_default=True,
    type=click.IntRange(min=1),
    help="Quantidade máxima de notícias recentes.",
)
def run_all(limit: int) -> None:
    """Executar a pipeline completa: coletar, analisar e calcular."""

    run_pipeline(limit=limit)


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option(
    "--port",
    default=8501,
    show_default=True,
    type=click.IntRange(1, 65535),
)
@click.option(
    "--headless",
    is_flag=True,
    help="Não abrir o navegador automaticamente.",
)
def dashboard(host: str, port: int, headless: bool) -> None:
    """Abrir o dashboard Streamlit sem configurar PYTHONPATH."""

    raise SystemExit(launch_dashboard(host=host, port=port, headless=headless))
