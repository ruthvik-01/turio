"""Native startup must fail before creating state when provisioning is absent."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("powershell.exe") is None, reason="Windows launcher")
def test_missing_native_runtime_fails_without_creating_state(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    launcher = scripts / "start-local-stack.ps1"
    source = Path(__file__).resolve().parents[2] / "scripts" / launcher.name
    shutil.copyfile(source, launcher)
    shutil.copyfile(source.with_name("use-d-drive.ps1"), scripts / "use-d-drive.ps1")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(launcher), "-Check"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode != 0
    assert "Native runtime is not provisioned" in result.stdout + result.stderr
    assert not (tmp_path / ".runtime").exists()
