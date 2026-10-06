import os
import tempfile
from pathlib import Path

import pytest

_user = "pytest"
_tmp = tempfile.TemporaryDirectory(prefix="slopbox_pytest")
_home = Path(_tmp.name) / "home" / _user
_home.mkdir(mode=0o700, parents=True, exist_ok=False)

os.environ["USER"] = _user
os.environ["HOME"] = str(_home)


def pytest_unconfigure():
    _tmp.cleanup()


@pytest.fixture(scope="session")
def test_home_dir() -> Path:
    return _home


@pytest.fixture(scope="session")
def test_user() -> str:
    return _user


@pytest.fixture
def fake_bin_mode() -> int:
    return 0o700


@pytest.fixture
def fake_bin_files() -> list[str]:
    return ["hello"]


@pytest.fixture
def fake_bin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_bin_mode: int,
    fake_bin_files: list[str],
) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir(mode=0o700, exist_ok=False)

    for name in fake_bin_files:
        binfile = bindir / name
        binfile.touch(mode=fake_bin_mode, exist_ok=False)
        binfile.write_text("pytest: mocked binary", encoding="utf-8")

    monkeypatch.setenv("PATH", str(bindir))

    return bindir


@pytest.fixture
def config_overrides() -> dict:
    return {}


@pytest.fixture
def config(tmp_path: Path, config_overrides: dict) -> dict:
    return {
        "slopbox_env_dir": str(tmp_path / "env")
    } | config_overrides


@pytest.fixture
def config_file(tmp_path: Path, config: dict) -> Path:
    out = []
    for k, v in config.items():

        if isinstance(v, str):
            out.append(f"{k} = '{v}'")
            continue

        out.append(f"{k} = {v}")

    c_toml = '\n'.join(out)
    config_path = tmp_path / "config.toml"
    config_path.touch(mode=0o600, exist_ok=False)
    config_path.write_text(c_toml)

    return config_path
