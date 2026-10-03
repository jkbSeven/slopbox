from pathlib import Path

import click

from slopbox import config, const, container_engine, environment
from slopbox.nix import Lock, Nix, NixError

VERSION = "0.1.0"


class fmt:
    @staticmethod
    def red(msg: str, **kwargs):
        return click.style(msg, fg="red", **kwargs)

    @staticmethod
    def green(msg: str, **kwargs):
        return click.style(msg, fg="green", **kwargs)


def _init_config_dir(config_dir: Path):
    try:
        config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    except (OSError, FileNotFoundError) as err:
        raise click.ClickException(
            f"unable to create or read the config directory ({config_dir}): {err}"
        ) from err


def _err_if_unhealthy() -> None:
    if not Nix.is_available():
        raise click.ClickException(
            "You have to install Nix prior to using slopbox; "
            "Nix main page: https://nixos.org/"
        )

    try:
        cengine = container_engine.get_container_engine()

    except container_engine.ContainerEngineError as err:
        raise click.ClickException(
            f"unable to resolve container engine: {err}"
        ) from err

    if not cengine.is_rootless():
        raise click.ClickException(
            f"{cengine.name} is not running in rootless mode, "
            "this has security implications and slopbox cannot proceed"
        )


@click.group()
def cli():
    """secure-ish environment for running AI agents"""


@cli.command("health")
def cli_health():
    """validate if runtime is healthy"""
    click.echo(f"version: {VERSION}")

    nix_status: str
    if not Nix.is_available():
        nix_status = f"Nix: {fmt.red('NOT INSTALLED', bold=True)}"
    else:
        nix_status = f"Nix: {fmt.green('OK', bold=True)}"
    click.echo(nix_status)

    cengine_status: str
    try:
        cengine = container_engine.get_container_engine()
    except container_engine.ContainerEngineError as err:
        cengine_status = (
            f"Container engine: {fmt.red('MISSING', bold=True)} (err: {err})"
        )
    else:
        rootless_status = (
            "(rootless)" if cengine.is_rootless() else fmt.red("(non-rootless)")
        )
        cengine_status = (
            f"Container engine: {fmt.green(cengine.name, bold=True)} {rootless_status}"
        )
    click.echo(cengine_status)


@cli.command("build")
def cli_build():
    """build all dependencies for a given profile"""
    _err_if_unhealthy()
    click.echo("Hello, World!")


@cli.command("init")
def cli_init():
    """initialize slopbox configuration (user-wide)"""
    if not Nix.is_available():
        raise click.ClickException(
            "You have to install Nix prior to using slopbox; "
            "Nix main page: https://nixos.org/"
        )

    # FIXME: allow user to override with --config /path/to/config.toml
    c = config.load()

    _init_config_dir(c.slopbox_env_dir)

    lock: Lock
    lock_file = c.slopbox_env_dir / "slopbox.lock"

    if not lock_file.exists():
        try:
            nixpkgs_tree = Nix.fetch_tree(const.NIXPKGS_FETCH_URL)
        except NixError as err:
            raise click.ClickException(
                f"failed to fetch and pin nixpkgs revision: {err}"
            ) from err

        try:
            slopbox_tree = Nix.fetch_tree(const.SLOPBOX_FETCH_URL)
        except NixError as err:
            raise click.ClickException(
                f"failed to fetch and pin slopbox revision: {err}"
            ) from err

        lock = Lock(nixpkgs=nixpkgs_tree, slopbox=slopbox_tree)

        lock_file.write_text(
            lock.model_dump_json(indent=2, by_alias=True),
            encoding="utf-8",
        )

    slopbox_file = c.slopbox_env_dir / "slopbox.nix"
    if not slopbox_file.exists():
        slopbox_file.write_text(environment.EXAMPLE_ENV_CONFIG, encoding="utf-8")


@cli.group("config")
def cli_config():
    """manage tool configuration (slopbox CLI)"""


@cli_config.command("show")
def cli_config_show():
    """show resolved tool configuration"""
    try:
        # FIXME: allow user to override with --config /path/to/config.toml
        c = config.load()

    except config.ConfigError as err:
        raise click.ClickException(f"error while loading tool config: {err}") from err

    click.echo(c.pretty_print())


@cli_config.command("edit")
def cli_config_edit():
    """edit tool configuration in your text editor ($EDITOR)"""
    # FIXME: allow user to override with --config /path/to/config.toml
    p = config.DEFAULT_CONFIG_PATH
    p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    click.edit(filename=str(p))


def main():
    cli()


if __name__ == "__main__":
    main()
