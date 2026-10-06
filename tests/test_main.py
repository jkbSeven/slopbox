from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from click.testing import CliRunner

from slopbox import config, const, container_engine, environment, nix
from slopbox.main import cli


NIXPKGS_TREE = nix.NixFetchTreeResult(**{
    "url": "github:nixos/nixpkgs/nixos-unstable",
    "lastModified": 1790822859,
    "lastModifiedDate": "20261001024739",
    "narHash": "sha256-69xHQhAeMAD2wDXO7T2pcOZIF9Sga2W+JkmY2a11Ops=",
    "rev": "c59305bab2065cfecc4944690d9eedbb56f3a9fa",
    "shortRev": "c59305b"
  }
)

SLOPBOX_TREE = nix.NixFetchTreeResult(**{
    "url": "github:jkbSeven/slopbox",
    "lastModified": 1785955512,
    "lastModifiedDate": "20260805184512",
    "narHash": "sha256-V+ZWAlt2TPjvozaQA7ERe7JRJyxf4OEPVP22o2xbfEA=",
    "rev": "1007a7f3ebdfaf153bae13a3356f3e6e08ea5913",
    "shortRev": "1007a7f"
  }
)

FETCH_TREE_MAPPING = {
    const.NIXPKGS_FETCH_URL: NIXPKGS_TREE,
    const.SLOPBOX_FETCH_URL: SLOPBOX_TREE,
}


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@patch("slopbox.main.Nix.is_available", MagicMock(return_value=False))
def test_cli_health_when_nix_not_available(runner: CliRunner):
    result = runner.invoke(cli, ["health"])
    assert "Nix: NOT INSTALLED\n" in result.stdout


@patch("slopbox.main.Nix.is_available", MagicMock(return_value=True))
def test_cli_health_when_nix_is_available(runner: CliRunner):
    result = runner.invoke(cli, ["health"])
    assert "Nix: OK\n" in result.stdout


@patch(
    "slopbox.main.container_engine.get_container_engine",
    MagicMock(side_effect=container_engine.ContainerEngineError("some err"))
)
def test_cli_health_when_container_engine_not_available(runner: CliRunner):
    result = runner.invoke(cli, ["health"])
    assert "Container engine: MISSING (err: some err)" in result.stdout


@pytest.mark.parametrize(
    ("rootless", "rootless_text"),
    (
        (False, "non-rootless"),
        (True, "rootless"),
    )

)
def test_cli_health_with_docker(
    runner: CliRunner,
    rootless: bool,
    rootless_text: str,
):
    mock_docker = MagicMock()
    mock_docker.name = "docker"
    mock_docker.is_rootless.return_value = rootless

    with patch(
        "slopbox.main.container_engine.get_container_engine"
    ) as mock_get_cengine:
        mock_get_cengine.return_value = mock_docker

        result = runner.invoke(cli, ["health"])
        assert f"Container engine: docker ({rootless_text})" in result.stdout


def test_cli_health_with_podman(runner: CliRunner):
    mock_podman = MagicMock()
    mock_podman.name = "podman"
    mock_podman.is_rootless.return_value = True

    with patch(
        "slopbox.main.container_engine.get_container_engine"
    ) as mock_get_cengine:
        mock_get_cengine.return_value = mock_podman

        result = runner.invoke(cli, ["health"])
        assert f"Container engine: podman (rootless)" in result.stdout


@patch("slopbox.main.Nix.is_available", MagicMock(return_value=True))
def test_cli_init(runner: CliRunner, config_file: Path):
    c = config.load(config_file)
    lock_file = c.slopbox_env_dir / "slopbox.lock"
    env_file = c.slopbox_env_dir / "slopbox.nix"

    assert c.slopbox_env_dir.exists() is False
    assert lock_file.exists() is False
    assert env_file.exists() is False

    def _mock_fetch(url: str):
        return FETCH_TREE_MAPPING[url]

    with patch("slopbox.main.Nix.fetch_tree", MagicMock(side_effect=_mock_fetch)):
        runner.invoke(cli, ["--config", str(config_file), "init"])

    assert c.slopbox_env_dir.exists()
    assert lock_file.exists()
    assert env_file.exists()

    lock = nix.Lock.model_validate_json(lock_file.read_text(encoding="utf-8"))
    assert lock.nixpkgs == NIXPKGS_TREE
    assert lock.slopbox == SLOPBOX_TREE

    assert env_file.read_text(encoding="utf-8") == environment.EXAMPLE_ENV_CONFIG


@patch("slopbox.main.Nix.is_available", MagicMock(return_value=True))
def test_cli_init_when_lockfile_exists(runner: CliRunner, config_file: Path):
    c = config.load(config_file)
    lock_file = c.slopbox_env_dir / "slopbox.lock"
    env_file = c.slopbox_env_dir / "slopbox.nix"

    assert c.slopbox_env_dir.exists() is False
    assert lock_file.exists() is False
    assert env_file.exists() is False

    c.slopbox_env_dir.mkdir()
    lock_file.touch()

    with patch("slopbox.main.Nix.fetch_tree") as mock_fetch:
        runner.invoke(cli, ["--config", str(config_file), "init"])
        mock_fetch.assert_not_called()

    # we created empty file by hand, making sure it was not overwritten
    assert lock_file.stat().st_size == 0

    assert env_file.exists()
    assert env_file.read_text(encoding="utf-8") == environment.EXAMPLE_ENV_CONFIG
