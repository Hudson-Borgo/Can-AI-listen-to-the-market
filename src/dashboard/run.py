"""Reliable Streamlit launcher that works from any current directory."""

import subprocess
import sys

from src import console
from src.paths import PROJECT_ROOT


DASHBOARD_APP = PROJECT_ROOT / "src" / "dashboard" / "app.py"


def launch_dashboard(
    host: str = "127.0.0.1",
    port: int = 8501,
    headless: bool = False,
) -> int:
    """Start the dashboard using the project's active Python environment."""

    url = f"http://{host}:{port}"
    console.banner(
        "DASHBOARD",
        "Can AI Listen to the Market?",
        "Visualização do sinal e das notícias analisadas",
    )
    console.label("Endereço", url, "bright_cyan")
    console.label("Aplicação", DASHBOARD_APP)
    console.success("Iniciando o dashboard; pressione Ctrl+C para encerrar")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(DASHBOARD_APP),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        str(headless).lower(),
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return completed.returncode
