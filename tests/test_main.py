from unittest.mock import MagicMock, patch
import pytest
from click.testing import CliRunner

from slopbox import container_engine
from slopbox.main import cli


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
