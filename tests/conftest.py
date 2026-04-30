"""Shared pytest fixtures."""
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def minimal_master_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "master_v117_minimal.xlsx"


@pytest.fixture
def sample_prd_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_prd.md"
