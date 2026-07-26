from pathlib import Path

import click

from config import UserConfig


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "slopbox"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

CONFIG_FILE = DEFAULT_CONFIG_FILE

@click.group()
@click.option("--config", envvar="SLOPBOX_CONFIG_FILE")
def cli(config: str | None):
    if config is not None:
        global CONFIG_FILE
        CONFIG_FILE = Path(config)


@cli.command()
def init():
    pass


@cli.command()
@click.option("--resolve-presets/--no-resolve-presets", default=True)
def config(resolve_presets: bool):
    c = UserConfig.model_validate_json(CONFIG_FILE.read_text())

    if resolve_presets:
        c.resolve_presets()

    click.echo(c.model_dump_json(indent=2, exclude_unset=True))


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
