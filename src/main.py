import json
import logging
from pathlib import Path

import click

from config import UserConfig

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s: %(message)s",
)
logger = logging.getLogger()

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "slopbox"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
CONFIG_FILE = DEFAULT_CONFIG_FILE

DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / "slopbox"
STATE_DIR = DEFAULT_STATE_DIR

EXAMPLE_CONFIG_FILE = Path(__file__).parent / "templates" / "config.json"
assert EXAMPLE_CONFIG_FILE.exists()


def _read_user_config() -> UserConfig:
    logger.debug(f"reading user config from path {CONFIG_FILE}")
    if not CONFIG_FILE.exists():
        raise click.ClickException(
            f"Config file does not exist at the default path ({CONFIG_FILE}). "
            "You must either create it with `slopbox init`, "
            "or provide a path to existing config through the `--config` option, "
            "e.g. `slopbox --config /path/to/config.json run`"
        )

    try:
        c = UserConfig.model_validate_json(CONFIG_FILE.read_text())

    except OSError as err:
        logger.debug(err)
        raise click.ClickException(
            f"OS error: errno={err.errno}, msg='{err.strerror}', filename='{err.filename}'"
        ) from err

    return c


def _validate_state_dir_exists(create: bool = False) -> bool:
    if STATE_DIR.exists():
        logger.debug(f"verified that state dir ({STATE_DIR}) exists")
        return True

    if create:
        logger.debug(f"state dir ({STATE_DIR}) does not exist, creating it")
        STATE_DIR.mkdir(parents=True)
        return True

    raise RuntimeError(
        f"Directory for storing slopbox profiles ({STATE_DIR}) does not exist"
    )


@click.group()
@click.option("--config", envvar="SLOPBOX_CONFIG_FILE")
@click.option("--state-dir", envvar="SLOPBOX_STATE_DIR")
@click.option("--verbose", "-v", "verbosity", count=True)
def cli(config: str | None, state_dir: str | None, verbosity: int):
    if verbosity == 1:
        logger.setLevel(logging.INFO)
    if verbosity > 1:
        logger.setLevel(logging.DEBUG)

    if config is not None:
        global CONFIG_FILE
        CONFIG_FILE = Path(config)
        logger.info(f"set config path to {CONFIG_FILE}")

    if state_dir is not None:
        global STATE_DIR
        STATE_DIR = Path(state_dir)
        logger.info(f"set state dir to {STATE_DIR}")


@cli.command()
@click.argument("path", default=DEFAULT_CONFIG_FILE, type=click.Path(path_type=Path))
def init(path: Path):
    # in case user provided a directory
    if path.suffix == "":
        raise RuntimeError("Provide a full path, it must end with '.json' file extension")

    if path.exists():
        click.echo(f"A slopbox config already exists at {path}, not overwriting", err=True)
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    EXAMPLE_CONFIG_FILE.copy(path)
    click.echo(f"Wrote an example config to {path}")


@cli.command()
@click.option("--resolve-presets/--no-resolve-presets", default=True)
@click.option("--profile-hashes/--no-profile-hashes", default=False)
def config(resolve_presets: bool, profile_hashes: bool):
    c = _read_user_config()

    if resolve_presets or profile_hashes:
        c.resolve_presets()

    if profile_hashes:
        mapping = {name: profile.hash() for name, profile in c.profiles.items()}
        click.echo(json.dumps(mapping, indent=2))
        return

    click.echo(c.model_dump_json(indent=2))


@cli.command()
@click.option("--profile", "-p", default="default")
def build(profile: str):
    _validate_state_dir_exists(create=True)
    cfg = _read_user_config()

    if profile not in cfg.profiles:

        # extra handling to let user know they can set "default" = "<some_existing_profile_name>"
        if profile == "default":
            raise click.ClickException(
                "Profile 'default' does not exist. "
                f"You can create this profile in your config ({CONFIG_FILE}) following the structure from the docs, "
                "or you can reference an existing profile, "
                "i.e. set {\"profiles\": {\"default\": \"<name_of_existing_profile>\"}}. "
                "Alternatively you can choose a profile through the `--profile/-p` option, "
                "e.g. slopbox build --profile claude-python"
            )

        raise click.ClickException(
            f"Profile '{profile}' does not exist in your config ({CONFIG_FILE})"
        )


@cli.command()
def run():
    pass


@cli.command()
def health():
    pass


if __name__ == "__main__":
    cli()
