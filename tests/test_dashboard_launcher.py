import subprocess
import sys
import unittest
from unittest.mock import patch

from src.dashboard.run import DASHBOARD_APP, launch_dashboard
from src.paths import PROJECT_ROOT


class DashboardLauncherTests(unittest.TestCase):
    @patch("src.dashboard.run.subprocess.run")
    def test_launcher_uses_cross_platform_argument_list(self, run) -> None:
        run.return_value = subprocess.CompletedProcess([], 0)

        exit_code = launch_dashboard(host="127.0.0.1", port=8765, headless=True)

        self.assertEqual(exit_code, 0)
        run.assert_called_once_with(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(DASHBOARD_APP),
                "--server.address",
                "127.0.0.1",
                "--server.port",
                "8765",
                "--server.headless",
                "true",
            ],
            cwd=PROJECT_ROOT,
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
