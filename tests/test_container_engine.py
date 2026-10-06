import re

import pytest

from slopbox import container_engine


@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files", "expected"),
    (
        (0o700, ["hello"], False),
        (0o700, ["podman"], True),
        (0o600, ["podman"], False),  # not executable
    ),
)
@pytest.mark.usefixtures("fake_bin")
def test_podman_is_available(expected: bool):
    assert container_engine.Podman.is_available() is expected


@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files", "expected"),
    (
        (0o700, ["hello"], False),
        (0o700, ["docker"], True),
        (0o600, ["docker"], False),  # not executable
    ),
)
@pytest.mark.usefixtures("fake_bin")
def test_docker_is_available(expected: bool):
    assert container_engine.Docker.is_available() is expected


@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files", "expected"),
    (
        (0o700, ["docker"], container_engine.Docker),
        (0o700, ["podman"], container_engine.Podman),
        (0o700, ["podman", "docker"], container_engine.Podman),
    ),
)
@pytest.mark.usefixtures("fake_bin")
def test_get_container_engine_success(expected: container_engine.ContainerEngine):
    assert container_engine.get_container_engine().name == expected.name


@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files"),
    (
        (0o700, ["hello"]),
        (0o600, ["docker"]),  # not executable
        (0o600, ["podman"]),  # not executable
    ),
)
@pytest.mark.usefixtures("fake_bin")
def test_get_container_engine_error():
    with pytest.raises(
        container_engine.ContainerEngineError,
        match=re.escape("neither podman nor docker is installed (not found in $PATH)"),
    ):
        container_engine.get_container_engine()
