from pathlib import Path

import click

from config import UserConfig


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "slopbox"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

CONFIG_FILE = None

@click.group()
@click.option("--config", default=str(DEFAULT_CONFIG_FILE))
def cli(config: str):
    global CONFIG_FILE
    CONFIG_FILE = Path(config)


@cli.command()
def init():
    pass


@cli.command()
def config():
    print(CONFIG_FILE)
    assert CONFIG_FILE
    config_data = CONFIG_FILE.read_text()
    c = UserConfig.model_validate_json(config_data)
    print(c.model_dump_json(indent=2))


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
