import functools
import shutil
import subprocess
from typing import Protocol


class ContainerEngineError(Exception):
    pass


class ContainerEngine(Protocol):
    name: str

    @classmethod
    def is_available(cls, sys_path: str | None = None) -> bool: ...

    @classmethod
    def is_rootless(cls) -> bool: ...


class DockerContainerEngine:
    name = "docker"

    @classmethod
    @functools.lru_cache
    def is_available(cls, sys_path: str | None = None) -> bool:
        return shutil.which("docker", path=sys_path) is not None

    @classmethod
    @functools.lru_cache
    def is_rootless(cls) -> bool:
        if not cls.is_available():
            raise ContainerEngineError("docker is not installed")

        ret = subprocess.run(
            ["docker", "info", "--format", "{{ .SecurityOptions }}"],
            capture_output=True,
        )

        clean = ret.stdout.decode(encoding="utf-8").strip("[]")

        return "name=rootless" in clean


class PodmanContainerEngine:
    name = "podman"

    @classmethod
    @functools.lru_cache
    def is_available(cls, sys_path: str | None = None) -> bool:
        return shutil.which("podman", path=sys_path) is not None

    @classmethod
    @functools.lru_cache
    def is_rootless(cls) -> bool:
        # TODO: check if having non-rootless podman is even possible
        return True


def get_container_engine(sys_path: str | None = None) -> ContainerEngine:
    # in case user has both, we prefer podman
    if PodmanContainerEngine.is_available(sys_path):
        return PodmanContainerEngine()

    if DockerContainerEngine.is_available(sys_path):
        return DockerContainerEngine()

    raise ContainerEngineError(
        "neither podman or docker is installed (not found in $PATH)"
    )
