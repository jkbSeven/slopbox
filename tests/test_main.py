from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from slopbox import config, const, container_engine, environment, nix
from slopbox.main import cli

NIXPKGS_TREE = nix.NixFetchTreeResult(
    **{
        "url": "github:nixos/nixpkgs/nixos-unstable",
        "lastModified": 1790822859,
        "lastModifiedDate": "20261001024739",
        "narHash": "sha256-69xHQhAeMAD2wDXO7T2pcOZIF9Sga2W+JkmY2a11Ops=",
        "rev": "c59305bab2065cfecc4944690d9eedbb56f3a9fa",
        "shortRev": "c59305b",
    }
)

FETCH_TREE_MAPPING = {
    const.NIXPKGS_FETCH_URL: NIXPKGS_TREE,
}


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def empty_sys_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    This fixture has been created to make sure that none of the tests use host binaries,
    which would result in flaky test results.
    Instead each test case declares what tools it wants available or missing.
    Actual slopbox build/run behavior must be verified in integration tests.
    """
    monkeypatch.setenv("PATH", "")


@pytest.fixture
def tools_nix_available():
    with patch("slopbox.main.Nix.is_available", MagicMock(return_value=True)):
        yield


@pytest.fixture
def tools_nix_not_available():
    with patch("slopbox.main.Nix.is_available", MagicMock(return_value=False)):
        yield


@pytest.fixture
def tools_cengine_available_non_rootless():
    mock_docker = MagicMock()
    mock_docker.name = "docker"
    mock_docker.is_rootless.return_value = False

    with patch("slopbox.main.container_engine.get_container_engine") as mock_get_engine:
        mock_get_engine.return_value = mock_docker
        yield


@pytest.fixture
def tools_cengine_available():
    mock_docker = MagicMock()
    mock_docker.name = "docker"
    mock_docker.is_rootless.return_value = True

    with patch("slopbox.main.container_engine.get_container_engine") as mock_get_engine:
        mock_get_engine.return_value = mock_docker
        yield


@pytest.fixture
def tools_cengine_not_available():
    err = "error from fixture"

    with patch(
        "slopbox.main.container_engine.get_container_engine",
        MagicMock(side_effect=container_engine.ContainerEngineError(err)),
    ):
        yield


@pytest.fixture
def tools_all_available(tools_cengine_available, tools_nix_available):
    pass


@pytest.mark.usefixtures("tools_all_available")
def test_cli_health_when_nix_is_available_and_cengine_ok(runner: CliRunner):
    result = runner.invoke(cli, ["health"])

    assert result.exit_code == 0
    assert "Nix: OK\n" in result.stdout
    assert "Container engine: docker (rootless)\n" in result.stdout


@pytest.mark.usefixtures("tools_nix_available", "tools_cengine_not_available")
def test_cli_health_when_nix_available_and_cengine_not_available(runner: CliRunner):
    result = runner.invoke(cli, ["health"])

    assert result.exit_code == 1
    assert "Nix: OK\n" in result.stdout
    assert "Container engine: MISSING (err: error from fixture)\n" in result.stdout


@pytest.mark.usefixtures("tools_nix_available", "tools_cengine_available_non_rootless")
def test_cli_health_when_nix_available_and_cengine_non_rootless(runner: CliRunner):
    result = runner.invoke(cli, ["health"])

    assert result.exit_code == 1
    assert "Nix: OK\n" in result.stdout
    assert "Container engine: docker (non-rootless)\n" in result.stdout


@pytest.mark.usefixtures("tools_nix_not_available", "tools_cengine_available")
def test_cli_health_when_nix_not_available_and_cengine_ok(runner: CliRunner):
    result = runner.invoke(cli, ["health"])

    assert result.exit_code == 1
    assert "Nix: NOT INSTALLED\n" in result.stdout
    assert "Container engine: docker (rootless)\n" in result.stdout


@pytest.mark.usefixtures("tools_nix_not_available", "tools_cengine_not_available")
def test_cli_health_when_nix_not_available_and_cengine_not_available(runner: CliRunner):
    result = runner.invoke(cli, ["health"])

    assert result.exit_code == 1
    assert "Nix: NOT INSTALLED\n" in result.stdout
    assert "Container engine: MISSING (err: error from fixture)\n" in result.stdout


@pytest.mark.parametrize(
    ("rootless", "rootless_text"),
    (
        (False, "non-rootless"),
        (True, "rootless"),
    ),
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
        assert "Container engine: podman (rootless)" in result.stdout


def _mock_nix_fetch(url: str, _debug):
    if url == const.NIXPKGS_FETCH_URL:
        return NIXPKGS_TREE

    raise RuntimeError(
        f"test err: mock got url {url}, expected {const.NIXPKGS_FETCH_URL}"
    )


@pytest.mark.usefixtures("tools_nix_not_available")
def test_cli_init_with_nix_not_available(runner: CliRunner):
    result = runner.invoke(cli, ["init"])

    assert result.exit_code == 1
    assert (
        "You have to install Nix prior to using slopbox; "
        "Nix main page: https://nixos.org/" in result.stderr
    )


@pytest.mark.usefixtures("tools_nix_available")
def test_cli_init(runner: CliRunner, config_file: Path):
    c = config.load(config_file)
    env_file, lock_file = c.slopbox_paths

    assert c.slopbox_env_dir.exists() is False
    assert lock_file.exists() is False
    assert env_file.exists() is False

    with patch("slopbox.main.Nix.fetch_tree", MagicMock(side_effect=_mock_nix_fetch)):
        result = runner.invoke(cli, ["--config", str(config_file), "init"])

    assert result.exit_code == 0

    assert c.slopbox_env_dir.exists()
    assert lock_file.exists()
    assert env_file.exists()

    lock = nix.NixFetchTreeResult.model_validate_json(
        lock_file.read_text(encoding="utf-8")
    )
    assert lock == NIXPKGS_TREE

    # opencode is the default init template
    assert (
        env_file.read_text(encoding="utf-8") == environment.EXAMPLE_OPENCODE_ENV_CONFIG
    )


@pytest.mark.usefixtures("tools_nix_available")
def test_cli_init_for_claude(runner: CliRunner, config_file: Path):
    c = config.load(config_file)
    env_file, lock_file = c.slopbox_paths

    assert c.slopbox_env_dir.exists() is False
    assert lock_file.exists() is False
    assert env_file.exists() is False

    with patch("slopbox.main.Nix.fetch_tree", MagicMock(side_effect=_mock_nix_fetch)):
        result = runner.invoke(
            cli,
            ["--config", str(config_file), "init", "-t", "claude"],
        )

    assert result.exit_code == 0

    assert c.slopbox_env_dir.exists()
    assert lock_file.exists()
    assert env_file.exists()

    lock = nix.NixFetchTreeResult.model_validate_json(
        lock_file.read_text(encoding="utf-8")
    )
    assert lock == NIXPKGS_TREE

    assert env_file.read_text(encoding="utf-8") == environment.EXAMPLE_CLAUDE_ENV_CONFIG


@pytest.mark.usefixtures("tools_nix_available")
def test_cli_init_for_codex(runner: CliRunner, config_file: Path):
    c = config.load(config_file)
    env_file, lock_file = c.slopbox_paths

    assert c.slopbox_env_dir.exists() is False
    assert lock_file.exists() is False
    assert env_file.exists() is False

    with patch("slopbox.main.Nix.fetch_tree", MagicMock(side_effect=_mock_nix_fetch)):
        result = runner.invoke(
            cli,
            ["--config", str(config_file), "init", "-t", "codex"],
        )

    assert result.exit_code == 0

    assert c.slopbox_env_dir.exists()
    assert lock_file.exists()
    assert env_file.exists()

    lock = nix.NixFetchTreeResult.model_validate_json(
        lock_file.read_text(encoding="utf-8")
    )
    assert lock == NIXPKGS_TREE

    assert env_file.read_text(encoding="utf-8") == environment.EXAMPLE_CODEX_ENV_CONFIG


@pytest.mark.usefixtures("tools_nix_available")
def test_cli_init_when_lockfile_exists(runner: CliRunner, config_file: Path):
    c = config.load(config_file)
    env_file, lock_file = c.slopbox_paths

    assert c.slopbox_env_dir.exists() is False
    assert lock_file.exists() is False
    assert env_file.exists() is False

    # simulating pre-existing lock file
    c.slopbox_env_dir.mkdir()
    lock_file.touch()

    with patch("slopbox.main.Nix.fetch_tree") as mock_fetch:
        result = runner.invoke(cli, ["--config", str(config_file), "init"])
        mock_fetch.assert_not_called()

    assert result.exit_code == 0

    # we created empty file by hand, making sure it was not overwritten
    assert lock_file.stat().st_size == 0

    assert env_file.exists()
    # opencode is the default init template
    assert (
        env_file.read_text(encoding="utf-8") == environment.EXAMPLE_OPENCODE_ENV_CONFIG
    )


@pytest.mark.usefixtures("tools_nix_available")
def test_cli_init_when_envfile_exists(runner: CliRunner, config_file: Path):
    c = config.load(config_file)
    env_file, lock_file = c.slopbox_paths

    assert c.slopbox_env_dir.exists() is False
    assert lock_file.exists() is False
    assert env_file.exists() is False

    # simulating pre-existing env file
    c.slopbox_env_dir.mkdir()
    env_file.touch()

    with patch("slopbox.main.Nix.fetch_tree", MagicMock(side_effect=_mock_nix_fetch)):
        result = runner.invoke(cli, ["--config", str(config_file), "init"])

    assert result.exit_code == 0

    assert lock_file.exists()
    lock = nix.NixFetchTreeResult.model_validate_json(
        lock_file.read_text(encoding="utf-8")
    )
    assert lock == NIXPKGS_TREE

    # we created empty file by hand, making sure it was not overwritten
    assert env_file.exists()
    assert env_file.stat().st_size == 0
