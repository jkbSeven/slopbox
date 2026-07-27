from pathlib import Path

import click

from config import UserConfig


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "slopbox"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
CONFIG_FILE = DEFAULT_CONFIG_FILE

DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / "slopbox"
STATE_DIR = DEFAULT_STATE_DIR

EXAMPLE_CONFIG_FILE = Path(__file__).parent / "templates" / "config.json"
assert EXAMPLE_CONFIG_FILE.exists()

@click.group()
@click.option("--config", envvar="SLOPBOX_CONFIG_FILE")
@click.option("--state-dir", envvar="SLOPBOX_STATE_DIR")
def cli(config: str | None, state_dir: str | None):
    if config is not None:
        global CONFIG_FILE
        CONFIG_FILE = Path(config)

    if state_dir is not None:
        global STATE_DIR
        STATE_DIR = Path(state_dir)


@cli.command()
def init():
    if CONFIG_FILE.exists():
        click.echo(f"A slopbox config already exists at {CONFIG_FILE}, not overwriting", err=True)
        return

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    EXAMPLE_CONFIG_FILE.copy(CONFIG_FILE)
    click.echo(f"Wrote an example config to {CONFIG_FILE}")


@cli.command()
@click.option("--resolve-presets/--no-resolve-presets", default=True)
def config(resolve_presets: bool):
    c = UserConfig.model_validate_json(CONFIG_FILE.read_text())

    if resolve_presets:
        c.resolve_presets()

    click.echo(c.model_dump_json(indent=2))


@cli.command()
def build():
    pass


@cli.command()
def run():
    pass


@cli.command()
def health():
    pass


if __name__ == "__main__":
    cli()
