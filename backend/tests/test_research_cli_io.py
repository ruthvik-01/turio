"""Serialization tests only: no human benchmark is frozen or evaluated."""
import json
import runpy
import sys
from pathlib import Path

from app.ml import benchmark


def test_freeze_cli_preserves_utf8_on_non_utf8_host(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[2] / "scripts" / "freeze_benchmark.py"
    source, output = tmp_path / "input.json", tmp_path / "output.json"
    data = {"candidates": [{"text": "履歴書 — café"}]}
    source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    read_text, write_text = Path.read_text, Path.write_text

    def platform_read(path, *args, **kwargs):
        kwargs.setdefault("encoding", "cp1252")
        return read_text(path, *args, **kwargs)

    def platform_write(path, content, *args, **kwargs):
        kwargs.setdefault("encoding", "cp1252")
        return write_text(path, content, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", platform_read)
    monkeypatch.setattr(Path, "write_text", platform_write)
    # Stub the freeze operation; this test exercises file encoding only.
    received = []

    def serialization_only(value, config):
        received.append(value)
        return {"manifest_sha256": "serialization-test-only", "candidates": value["candidates"]}

    monkeypatch.setattr(benchmark, "freeze", serialization_only)
    monkeypatch.setattr(sys, "argv", [str(script), str(source), "--output", str(output)])
    runpy.run_path(str(script), run_name="__main__")
    assert received == [data]
    assert json.loads(output.read_text(encoding="utf-8"))["candidates"] == data["candidates"]
