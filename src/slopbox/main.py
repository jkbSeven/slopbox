from pathlib import Path

import click

from slopbox.checks import (
    can_run,
    is_docker_available,
    is_rootless_docker,
)
from slopbox.config import EXAMPLE_SLOPBOX_CONFIG
from slopbox.nix import Nix, NixError, SlopboxLock

VERSION = "0.1.0"

HOME_DIR = Path.home().resolve()
CONFIG_DIR = HOME_DIR / ".config" / "slopbox"


class fmt:
    @staticmethod
    def red(msg: str):
        return click.style(msg, fg="red")

    @staticmethod
    def green(msg: str):
        return click.style(msg, fg="green")


def _init_config_dir():
    if not HOME_DIR.exists():
        raise click.ClickException(
            f"user's home directory ({HOME_DIR}) does not exist, cannot proceed"
        )

    try:
        CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    except (OSError, FileNotFoundError) as err:
        raise click.ClickException(
            f"unable to create or read the config directory ({CONFIG_DIR}): {err}"
        ) from err


def _err_if_unhealthy() -> None:
    if not can_run():
        raise click.ClickException(
            "slopbox health check failed, "
            "please run `slopbox health` and fix reported issues"
        )


@click.group()
def cli():
    """secure-ish environment for running AI agents"""


@cli.command()
def health():
    """validate if runtime is healthy"""
    click.echo(f"version: {VERSION}")

    try:
        nix_version = Nix.version()
        click.echo(f"nix: {fmt.green('OK')} ({nix_version})")
    except NixError:
        click.echo("nix: " + fmt.red("MISSING"))

    if not is_docker_available():
        click.echo("docker: " + fmt.red("MISSING"))
    else:
        click.echo("docker: " + fmt.green("INSTALLED"))
        click.echo(" - rootless: ", nl=False)

        rootless = is_rootless_docker()
        if rootless == 0:
            click.echo(fmt.red("NO"))
        elif rootless == 1:
            click.echo(fmt.green("YES"))
        else:
            click.echo(fmt.red("UNABLE TO CHECK"))


@cli.command()
def build():
    """build all dependencies for a given profile"""
    _err_if_unhealthy()
    click.echo("Hello, World!")


@cli.command()
def init():
    """initialize slopbox configuration (user-wide)"""
    if not Nix.is_available():
        raise click.ClickException(
            "You have to install Nix prior to using slopbox, more info: https://nixos.org/"
        )

    _init_config_dir()

    lock: SlopboxLock
    lock_file = CONFIG_DIR / "slopbox.lock"

    if not lock_file.exists():
        try:
            nixpkgs_tree = Nix.fetch_tree("github:nixos/nixpkgs/nixos-unstable")
        except NixError as err:
            raise click.ClickException(
                f"failed to fetch and pin nixpkgs revision: {err}"
            ) from err

        try:
            slopbox_tree = Nix.fetch_tree("github:jkbSeven/slopbox")
        except NixError as err:
            raise click.ClickException(
                f"failed to fetch and pin slopbox revision: {err}"
            ) from err

        lock = SlopboxLock(nixpkgs=nixpkgs_tree, slopbox=slopbox_tree)

        lock_file.write_text(
            lock.model_dump_json(indent=2, by_alias=True),
            encoding="utf-8",
        )

    else:
        lock = SlopboxLock.model_validate_json(lock_file.read_text(encoding="utf-8"))

    slopbox_file = CONFIG_DIR / "slopbox.nix"
    if not slopbox_file.exists():
        slopbox_file.write_text(EXAMPLE_SLOPBOX_CONFIG, encoding="utf-8")


def main():
    cli()


if __name__ == "__main__":
    main()
