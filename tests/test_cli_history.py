"""CLI history command tests."""

from __future__ import annotations

import contextlib
import importlib
import io
import sys
import types


class FakeAPI:
    def get_sleep_intervals(self, child_uid, start_ts, end_ts):
        return [{"start": start_ts, "duration": 1200}]

    def get_feed_intervals(self, child_uid, start_ts, end_ts):
        return [{"start": start_ts, "leftDuration": 954.0, "rightDuration": 3229.0}]

    def get_diaper_intervals(self, child_uid, start_ts, end_ts):
        return [{"start": start_ts, "mode": "pee"}]

    def get_health_entries(self, child_uid, start_ts, end_ts):
        return [{"start": start_ts, "weight": 5.2}]

    def get_solids_intervals(self, child_uid, start_ts, end_ts):
        return [{"start": start_ts, "mode": "solids", "foods": {
            "abc-123": {"id": "abc-123", "source": "custom", "created_name": "banana"},
            "def-456": {"id": "def-456", "source": "custom", "created_name": "rice"},
        }}]

    def log_solids(self, child_uid, foods, notes="", reaction=""):
        pass


def load_cli_module():
    """Load the CLI module with a stubbed huckleberry_api dependency."""
    fake_module = types.ModuleType("huckleberry_api")
    fake_module.HuckleberryAPI = FakeAPI
    sys.modules["huckleberry_api"] = fake_module
    sys.modules.pop("huckleberry_cli.cli", None)
    return importlib.import_module("huckleberry_cli.cli")


def run_main(cli_module, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = 0

    old_argv = sys.argv[:]
    sys.argv = ["huckleberry"] + argv
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            cli_module.main()
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.argv = old_argv

    return exit_code, stdout.getvalue(), stderr.getvalue()


def test_entity_history_commands():
    cli = load_cli_module()
    cli.get_api = lambda: FakeAPI()
    cli.get_child_uid = lambda api, child=None: "child_1"

    commands = [
        ["sleep", "history", "--days", "2"],
        ["feed", "history", "--days", "2"],
        ["diaper", "history", "--days", "2"],
        ["growth", "history", "--days", "2"],
        ["solids", "history", "--days", "2"],
    ]

    for argv in commands:
        code, out, err = run_main(cli, argv)
        assert code == 0, f"Unexpected failure for {argv}: {err}"
        assert "History" in out


def test_feed_history_durations_are_converted_from_seconds():
    cli = load_cli_module()
    cli.get_api = lambda: FakeAPI()
    cli.get_child_uid = lambda api, child=None: "child_1"

    code, out, err = run_main(cli, ["feed", "history", "--days", "2"])
    assert code == 0, f"Unexpected failure: {err}"
    assert "L:15m R:53m" in out


def test_solids_history_shows_foods():
    cli = load_cli_module()
    cli.get_api = lambda: FakeAPI()
    cli.get_child_uid = lambda api, child=None: "child_1"

    code, out, err = run_main(cli, ["solids", "history", "--days", "2"])
    assert code == 0, f"Unexpected failure: {err}"
    assert "banana" in out
    assert "rice" in out
    assert "Solids" in out


def test_solids_log():
    cli = load_cli_module()
    cli.get_api = lambda: FakeAPI()
    cli.get_child_uid = lambda api, child=None: "child_1"

    code, out, err = run_main(cli, ["solids", "log", "apple,banana", "--notes", "morning snack", "--reaction", "LOVED"])
    assert code == 0, f"Unexpected failure: {err}"
    assert "Solids logged" in out
