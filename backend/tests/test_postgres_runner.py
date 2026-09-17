"""Runner safety checks use no database connection."""
import runpy
import sys
from pathlib import Path

import pytest

RUNNER = Path(__file__).with_name("run_postgres_suite.py")


@pytest.mark.parametrize("target", [None, "sqlite:///turio_test_fake.db",
                                   "postgresql+psycopg://fixture@localhost/turio"])
def test_runner_rejects_missing_or_non_test_database(monkeypatch, target):
    if target is None:
        monkeypatch.delenv("TURIO_TEST_DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("TURIO_TEST_DATABASE_URL", target)
    monkeypatch.setattr(pytest, "main", lambda args: pytest.fail("Tests must not start"))
    with pytest.raises(SystemExit, match="turio_test_"):
        runpy.run_path(str(RUNNER), run_name="__main__")


def test_runner_forwards_arguments_without_using_application_database(monkeypatch):
    target = "postgresql+psycopg://fixture@localhost/turio_test_fixture"
    monkeypatch.setenv("TURIO_TEST_DATABASE_URL", target)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://fixture@localhost/do_not_use")
    monkeypatch.setattr(sys, "argv", [str(RUNNER), "tests/test_applications.py", "--collect-only"])
    calls = []
    monkeypatch.setattr(pytest, "main", lambda args: calls.append(args) or 0)
    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(RUNNER), run_name="__main__")
    assert result.value.code == 0
    assert calls[0][-2:] == ["tests/test_applications.py", "--collect-only"]
