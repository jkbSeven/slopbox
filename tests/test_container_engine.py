import re
from pathlib import Path

import pytest
from slopbox import container_engine


@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files", "expected"),
    (
        (0o700, ["hello"], False),
        (0o700, ["podman"], True),
        (0o600, ["podman"], False),  # not executable
    )
)
def test_podman_is_available(fake_bin: Path, expected: bool):
    assert (
        container_engine
        .PodmanContainerEngine
        .is_available(sys_path=str(fake_bin)) is expected
    )


@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files", "expected"),
    (
        (0o700, ["hello"], False),
        (0o700, ["docker"], True),
        (0o600, ["docker"], False),  # not executable
    )
)
def test_docker_is_available(fake_bin: Path, expected: bool):
    assert (
        container_engine
        .DockerContainerEngine
        .is_available(sys_path=str(fake_bin)) is expected
    )


@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files", "expected"),
    (
        (0o700, ["docker"], container_engine.DockerContainerEngine),
        (0o700, ["podman"], container_engine.PodmanContainerEngine),
        (0o700, ["podman", "docker"], container_engine.PodmanContainerEngine),
    )
)
def test_get_container_engine_success(
    fake_bin: Path,
    expected: container_engine.ContainerEngine,
):
    assert (
        container_engine
        .get_container_engine(sys_path=str(fake_bin))
        .name == expected.name
    )


@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files"),
    (
        (0o700, ["hello"]),
        (0o600, ["docker"]),  # not executable
        (0o600, ["podman"]),  # not executable
    )
)
def test_get_container_engine_error(fake_bin: Path):
    with pytest.raises(
        container_engine.ContainerEngineError,
        match=re.escape(
            "neither podman nor docker is installed (not found in $PATH)"
        ),
    ):
        container_engine.get_container_engine(sys_path=str(fake_bin))
