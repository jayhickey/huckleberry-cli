import subprocess
import sys


def test_help():
    result = subprocess.run(
        [sys.executable, "-m", "huckleberry_cli.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Huckleberry baby tracker CLI" in result.stdout
