from pathlib import Path

import pytest


@pytest.fixture
def fake_bin_mode() -> int:
    return 0o700


@pytest.fixture
def fake_bin_files() -> list[str]:
    return ["hello"]


@pytest.fixture
def fake_bin(tmp_path: Path, fake_bin_mode: int, fake_bin_files: list[str]):
    bindir = tmp_path / "bin"
    bindir.mkdir()

    for name in fake_bin_files:
        binfile = bindir / name
        binfile.touch(mode=fake_bin_mode, exist_ok=False)
        binfile.write_text("pytest: mocked binary", encoding="utf-8")

    return bindir
