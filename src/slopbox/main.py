import json
import subprocess
from pathlib import Path

import click

from slopbox import config, const, container_engine, environment
from slopbox.nix import Nix, NixError, NixFetchTreeResult


class fmt:
    esc = "\x1b"
    checkmark = "\u2713"

    @staticmethod
    def red(msg: str, **kwargs) -> str:
        return click.style(msg, fg="red", **kwargs)

    @staticmethod
    def green(msg: str, **kwargs) -> str:
        return click.style(msg, fg="green", **kwargs)

    @staticmethod
    def up(count: int, *, goto_beg: bool) -> str:
        return f"{fmt.esc}[{count}A" + ("\r" if goto_beg else "")

    @staticmethod
    def clear_line() -> str:
        return f"{fmt.esc}[2K"


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
@click.version_option(version=const.VERSION, message="%(version)s")
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to a config file (.toml)",
)
@click.pass_context
def cli(ctx: click.Context, config: Path | None):
    """secure-ish environment for running AI agents"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@cli.command("health")
def cli_health():
    """validate runtime health"""
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
@click.option("--profile", "-p", default="default")
@click.option(
    "--runtime",
    "-r",
    default="container",
    type=click.Choice(["container", "vm"]),
)
@click.pass_context
def cli_build(ctx: click.Context, profile: str, runtime: str):
    """build profile"""
    if runtime != "container":
        raise click.ClickException(f"'{runtime}' runtime is not supported yet")

    _err_if_unhealthy()

    c = config.load(ctx.obj["config"])

    env_file, lock_file = c.slopbox_paths

    if not lock_file.exists():
        raise click.ClickException(
            f"You haven't locked slopbox dependencies: {lock_file} does not exist. "
            "Run `slopbox init` first, then rerun this command"
        )

    if not env_file.exists():
        raise click.ClickException(
            "You haven't created a slopbox environment: "
            f"{env_file} does not exist. "
            "Run `slopbox init`, adjust the environment to your needs, "
            "then rerun this command"
        )

    lock = NixFetchTreeResult.model_validate_json(lock_file.read_text(encoding="utf-8"))
    nixpkgs_url = lock.fetch_tree_url()

    click.echo(f"Building profile '{profile}':")

    try:
        profile_data = Nix.profile_data(str(env_file), nixpkgs_url, profile)
    except NixError as err:
        raise click.ClickException(
            f"failed to evaluate profile with nix: {err}"
        ) from err

    engine = container_engine.get_container_engine().name

    def _build(component: str):
        click.echo(f"-> building {component}...")
        try:
            loader_path = Nix.build_container_loader(
                env_path=str(env_file),
                nixpkgs_url=nixpkgs_url,
                profile=profile,
                engine=engine,
                component=component,
            )
        except NixError as err:
            raise click.ClickException(f"build failed: {err}") from err

        result = subprocess.run(f"{loader_path}/bin/loader", capture_output=True)

        if result.returncode != 0:
            raise click.ClickException(
                "failed to load the container image: "
                + result.stderr.decode(encoding="utf-8")
            )

        click.echo(
            fmt.up(1, goto_beg=True)
            + fmt.clear_line()
            + fmt.green(fmt.checkmark)
            + f" built {component} ({profile_data['containers'][component]['image']})"
        )

    _build("runtime")
    if profile_data["profile"]["proxy"]["enable"] is True:
        _build("proxy")


@cli.command("init")
@click.pass_context
def cli_init(ctx: click.Context):
    """initialize slopbox environment (user-wide)"""
    if not Nix.is_available():
        raise click.ClickException(
            "You have to install Nix prior to using slopbox; "
            "Nix main page: https://nixos.org/"
        )

    c = config.load(ctx.obj["config"])

    _init_config_dir(c.slopbox_env_dir)

    env_file, lock_file = c.slopbox_paths

    if not lock_file.exists():
        try:
            nixpkgs_tree = Nix.fetch_tree(const.NIXPKGS_FETCH_URL)
        except NixError as err:
            raise click.ClickException(
                f"failed to fetch and pin nixpkgs revision: {err}"
            ) from err

        lock_file.write_text(
            nixpkgs_tree.model_dump_json(indent=2, by_alias=True),
            encoding="utf-8",
        )

    if not env_file.exists():
        env_file.write_text(environment.EXAMPLE_ENV_CONFIG, encoding="utf-8")


@cli.command("profile")
@click.argument("profile", default="default")
@click.pass_context
def cli_profile(ctx: click.Context, profile: str):
    """print profile data and build metadata"""
    _err_if_unhealthy()

    c = config.load(ctx.obj["config"])

    env_file, lock_file = c.slopbox_paths

    if not lock_file.exists():
        raise click.ClickException(
            f"You haven't locked slopbox dependencies: {lock_file} does not exist. "
            "Run `slopbox init` first, then rerun this command"
        )

    if not env_file.exists():
        raise click.ClickException(
            "You haven't created a slopbox environment: "
            f"{env_file} does not exist. "
            "Run `slopbox init`, adjust the environment to your needs, "
            "then rerun this command"
        )

    lock = NixFetchTreeResult.model_validate_json(lock_file.read_text(encoding="utf-8"))
    try:
        profile_data = Nix.profile_data(str(env_file), lock.fetch_tree_url(), profile)
    except NixError as err:
        raise click.ClickException(
            f"failed to evaluate profile with nix: {err}"
        ) from err

    click.echo(json.dumps(profile_data, indent=2))


@cli.command("run")
@click.option("--profile", "-p", default="default")
@click.option(
    "--runtime",
    "-r",
    default="container",
    type=click.Choice(["container", "vm"]),
)
@click.pass_context
def cli_run(ctx: click.Context, profile: str, runtime: str):
    """run profile"""
    if runtime != "container":
        raise click.ClickException(f"'{runtime}' runtime is not supported yet")

    _err_if_unhealthy()

    c = config.load(ctx.obj["config"])
    env_file, lock_file = c.slopbox_paths

    if not lock_file.exists():
        raise click.ClickException(
            f"You haven't locked slopbox dependencies: {lock_file} does not exist. "
            "Run `slopbox init` first, then rerun this command"
        )

    if not env_file.exists():
        raise click.ClickException(
            "You haven't created a slopbox environment: "
            f"{env_file} does not exist. "
            "Run `slopbox init`, adjust the environment to your needs, "
            "then rerun this command"
        )

    lock = NixFetchTreeResult.model_validate_json(lock_file.read_text(encoding="utf-8"))
    nixpkgs_url = lock.fetch_tree_url()
    engine = container_engine.get_container_engine().name

    runner_path = Nix.build_container_runner(
        str(env_file), nixpkgs_url, profile, engine
    )

    result = subprocess.run(f"{runner_path}/bin/run")

    if result.returncode != 0:
        raise click.ClickException(
            f"error during runtime, please see the {engine} logs above"
        )


@cli.group("config")
def cli_config():
    """manage tool configuration (slopbox CLI)"""


@cli_config.command("show")
@click.pass_context
def cli_config_show(ctx: click.Context):
    """show resolved tool configuration"""
    try:
        c = config.load(ctx.obj["config"])

    except config.ConfigError as err:
        raise click.ClickException(f"error while loading tool config: {err}") from err

    click.echo(c.pretty_print())


@cli_config.command("edit")
@click.pass_context
def cli_config_edit(ctx: click.Context):
    """edit tool configuration in your text editor ($EDITOR)"""
    p = ctx.obj["config"] or config.DEFAULT_CONFIG_PATH
    p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    if p.exists() and not p.is_file():
        raise click.ClickException(
            f"config path exists but does not point to a file: {p}"
        )

    click.edit(filename=str(p))


def main():
    cli()


if __name__ == "__main__":
    main()
