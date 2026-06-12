"""Characterization tests for scripts/sync_shared.py.

The script resolves the repo root from its own __file__, so each test copies it
into a throwaway repo layout under tmp_path and runs it there via subprocess.
Locked-in policies:
- only files that ALREADY EXIST in a bundle are overwritten (no auto-add)
- --check never mutates and exits 1 on drift, 0 when clean
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SYNC_SCRIPT = Path(__file__).parent.parent / "scripts" / "sync_shared.py"


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    shutil.copy2(SYNC_SCRIPT, tmp_path / "scripts" / "sync_shared.py")
    (tmp_path / "shared").mkdir()
    (tmp_path / "shared-reference").mkdir()
    bundle = tmp_path / "skills" / "qa-demo"
    (bundle / "scripts").mkdir(parents=True)
    (bundle / "reference").mkdir()
    return tmp_path


def _run_sync(repo: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(repo / "scripts" / "sync_shared.py"), *flags],
        capture_output=True, text=True,
    )


class TestApplyMode:
    def test_overwrites_existing_drifted_file(self, fake_repo: Path):
        (fake_repo / "shared" / "tool.py").write_text("v2")
        bundled = fake_repo / "skills" / "qa-demo" / "scripts" / "tool.py"
        bundled.write_text("v1")

        result = _run_sync(fake_repo)

        assert result.returncode == 0
        assert bundled.read_text() == "v2"
        assert "updated: skills/qa-demo/scripts/tool.py" in result.stdout

    def test_does_not_add_new_shared_file_to_bundle(self, fake_repo: Path):
        (fake_repo / "shared" / "new_tool.py").write_text("v1")

        result = _run_sync(fake_repo)

        assert result.returncode == 0
        assert not (fake_repo / "skills" / "qa-demo" / "scripts" / "new_tool.py").exists()

    def test_empty_placeholder_opts_bundle_in(self, fake_repo: Path):
        (fake_repo / "shared" / "tool.py").write_text("real content")
        bundled = fake_repo / "skills" / "qa-demo" / "scripts" / "tool.py"
        bundled.write_text("")

        _run_sync(fake_repo)

        assert bundled.read_text() == "real content"

    def test_reference_dir_synced_from_shared_reference(self, fake_repo: Path):
        (fake_repo / "shared-reference" / "policy.md").write_text("v2")
        bundled = fake_repo / "skills" / "qa-demo" / "reference" / "policy.md"
        bundled.write_text("v1")

        _run_sync(fake_repo)

        assert bundled.read_text() == "v2"


class TestCheckMode:
    def test_drift_exits_1_without_mutating(self, fake_repo: Path):
        (fake_repo / "shared" / "tool.py").write_text("v2")
        bundled = fake_repo / "skills" / "qa-demo" / "scripts" / "tool.py"
        bundled.write_text("v1")

        result = _run_sync(fake_repo, "--check")

        assert result.returncode == 1
        assert bundled.read_text() == "v1"
        assert "would-update: skills/qa-demo/scripts/tool.py" in result.stdout

    def test_clean_repo_exits_0(self, fake_repo: Path):
        (fake_repo / "shared" / "tool.py").write_text("same")
        (fake_repo / "skills" / "qa-demo" / "scripts" / "tool.py").write_text("same")

        result = _run_sync(fake_repo, "--check")

        assert result.returncode == 0
        assert "unchanged: skills/qa-demo/scripts/tool.py" in result.stdout

    def test_new_shared_file_is_not_drift(self, fake_repo: Path):
        (fake_repo / "shared" / "new_tool.py").write_text("v1")

        result = _run_sync(fake_repo, "--check")

        assert result.returncode == 0
