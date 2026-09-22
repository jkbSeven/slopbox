import subprocess


def is_tool_available(cmd: list[str]) -> bool:
    try:
        return (
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            != 127
        )
    except FileNotFoundError:
        pass

    return False


def is_docker_available() -> bool:
    return is_tool_available(["docker", "--version"])


def is_rootless_docker() -> int:
    """
    Returns:
        * 0 if docker is not rootless
        * 1 if docker is rootless
        * 2 if unable to check
    """
    ret = subprocess.run(
        ["docker", "info", "--format", "{{ .SecurityOptions }}"], capture_output=True
    )

    if ret.returncode != 0:
        return 2

    clean = ret.stdout.decode(encoding="utf-8").strip("[]")

    if "name=rootless" in clean:
        return 1

    return 0


def can_run() -> bool:
    return is_nix_available() and is_docker_available() and is_rootless_docker() == 1
