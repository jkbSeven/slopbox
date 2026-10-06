import shutil
import subprocess
from typing import Protocol


class ContainerEngineError(Exception):
    pass


class ContainerEngine(Protocol):
    name: str

    @classmethod
    def is_available(cls) -> bool: ...

    @classmethod
    def is_rootless(cls) -> bool: ...


class Docker:
    name = "docker"

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("docker") is not None

    @classmethod
    def is_rootless(cls) -> bool:
        if not cls.is_available():
            raise ContainerEngineError("docker is not installed")

        ret = subprocess.run(
            ["docker", "info", "--format", "{{ .SecurityOptions }}"],
            capture_output=True,
        )

        if ret.returncode != 0:
            raise ContainerEngineError(
                "error while checking if docker is rootless: "
                "command 'docker info' failed: "
                f"{ret.stderr.decode(encoding='utf-8')}"
            )

        clean = ret.stdout.decode(encoding="utf-8").strip("[]")

        return "name=rootless" in clean


class Podman:
    name = "podman"

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("podman") is not None

    @classmethod
    def is_rootless(cls) -> bool:
        if not cls.is_available():
            raise ContainerEngineError("podman is not installed")

        # TODO: check if having non-rootless podman is even possible
        return True


def get_container_engine() -> ContainerEngine:
    # in case user has both, we prefer podman
    if Podman.is_available():
        return Podman()

    if Docker.is_available():
        return Docker()

    raise ContainerEngineError(
        "neither podman nor docker is installed (not found in $PATH)"
    )
