"""Small, dependency-light terminal presentation helpers for live demos."""

from datetime import datetime
import shutil
import textwrap

import click


def terminal_width() -> int:
    return min(max(shutil.get_terminal_size((92, 20)).columns, 72), 112)


def divider(character: str = "─", color: str = "bright_black") -> None:
    click.secho(character * terminal_width(), fg=color)


def banner(kicker: str, title: str, subtitle: str | None = None) -> None:
    width = terminal_width()
    click.secho("═" * width, fg="blue", bold=True)
    click.secho(f"  {kicker}", fg="bright_cyan", bold=True)
    click.secho(f"  {title}", fg="white", bold=True)
    if subtitle:
        click.secho(f"  {subtitle}", fg="bright_black")
    click.secho("═" * width, fg="blue", bold=True)


def section(step: str, title: str) -> None:
    click.echo()
    click.secho(f"  {step}  ", fg="black", bg="bright_cyan", bold=True, nl=False)
    click.secho(f"  {title}", fg="bright_white", bold=True)
    divider()


def label(name: str, value: object, color: str = "white") -> None:
    click.secho(f"  {name:<18}", fg="bright_black", nl=False)
    click.secho(str(value), fg=color)


def success(message: str) -> None:
    click.secho(f"  ✓ {message}", fg="green", bold=True)


def warning(message: str) -> None:
    click.secho(f"  ! {message}", fg="yellow", bold=True)


def error(message: str) -> None:
    click.secho(f"  ✗ {message}", fg="red", bold=True)


def article_collected(index: int, total: int, article: dict) -> None:
    title = str(article.get("title") or "Sem título")
    published = str(article.get("published_at") or "data desconhecida")
    prefix = f"  [{index:02d}/{total:02d}]"
    available = max(32, terminal_width() - len(prefix) - 3)
    lines = textwrap.wrap(title, width=available) or [title]

    click.secho(prefix, fg="bright_cyan", bold=True, nl=False)
    click.secho(f" {lines[0]}", fg="white")
    for line in lines[1:]:
        click.secho(" " * (len(prefix) + 1) + line, fg="white")
    click.secho(
        " " * (len(prefix) + 1) + f"MegaWhat · {published}",
        fg="bright_black",
    )


def analysis_started(index: int, total: int, title: str) -> None:
    click.echo()
    click.secho(
        f"  [{index:02d}/{total:02d}] ANALISANDO",
        fg="bright_cyan",
        bold=True,
    )
    for line in textwrap.wrap(str(title), width=terminal_width() - 4):
        click.secho(f"    {line}", fg="white", bold=True)


def analysis_result(result: dict) -> None:
    sentiment = str(result["sentiment"]).upper()
    sentiment_color = {
        "POSITIVE": "green",
        "NEGATIVE": "red",
        "NEUTRAL": "yellow",
    }.get(sentiment, "white")

    click.secho("    Resultado      ", fg="bright_black", nl=False)
    click.secho(sentiment, fg=sentiment_color, bold=True, nl=False)
    click.secho(f"  ·  score {float(result['score']):+.2f}", fg="white", nl=False)
    click.secho(
        f"  ·  relevância {float(result['relevance']):.2f}",
        fg="white",
    )
    reason = str(result.get("reason") or "")
    if reason:
        click.secho("    Justificativa  ", fg="bright_black")
        for line in textwrap.wrap(reason, width=terminal_width() - 8):
            click.secho(f"      {line}", fg="bright_black")


def signal_table(daily_signals, rows: int = 5) -> None:
    recent = daily_signals.tail(rows)
    click.echo()
    click.secho(
        "  DATA         NOTÍCIAS   RELEVÂNCIA      SINAL   TENDÊNCIA",
        fg="bright_black",
        bold=True,
    )
    divider()

    for row in recent.itertuples(index=False):
        trend = str(row.trend)
        trend_color = {
            "POSITIVE": "green",
            "NEGATIVE": "red",
            "NEUTRAL": "yellow",
        }.get(trend, "white")
        date_label = (
            row.date.strftime("%Y-%m-%d")
            if isinstance(row.date, datetime)
            else str(row.date)
        )
        click.secho(
            f"  {date_label:<12} {int(row.articles):>8}   "
            f"{float(row.average_relevance):>10.3f}   "
            f"{float(row.signal):>+8.3f}   ",
            fg="white",
            nl=False,
        )
        click.secho(trend, fg=trend_color, bold=True)


def final_signal(current) -> None:
    click.echo()
    trend = str(current["trend"])
    trend_color = {
        "POSITIVE": "green",
        "NEGATIVE": "red",
        "NEUTRAL": "yellow",
    }.get(trend, "white")
    divider("═", "blue")
    click.secho("  SINAL MAIS RECENTE", fg="bright_cyan", bold=True)
    label("Data", current["date"])
    label("Notícias", int(current["articles"]))
    label("Relevância média", f"{float(current['average_relevance']):.3f}")
    label("Sinal", f"{float(current['signal']):+.3f}")
    click.secho(f"  {'Tendência':<16}", fg="bright_black", nl=False)
    click.secho(trend, fg=trend_color, bold=True)
    divider("═", "blue")
