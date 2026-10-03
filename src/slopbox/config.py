"""
Configuration for slopbox as a CLI tool,
not for runtime container or vm configuration -- for that use environment module
"""

import tomllib
from pathlib import Path

import pydantic

MAX_CONFIG_BYTES = 4096
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "slopbox" / "config.toml"


class ConfigError(Exception):
    pass


class Config(pydantic.BaseModel):
    slopbox_env_dir: Path = Path.home() / ".config" / "slopbox"

    model_config = pydantic.ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    @pydantic.field_validator("slopbox_dir", mode="after")
    @classmethod
    def expand_slopbox_dir(cls, v: Path) -> Path:
        return v.expanduser().resolve()

    @classmethod
    def load(cls, config_path: Path | None = None) -> Config:
        if config_path is None:
            config_path = DEFAULT_CONFIG_PATH

        if not config_path.is_file():
            return cls()

        filesize = config_path.lstat().st_size

        if filesize > MAX_CONFIG_BYTES:
            raise ConfigError(
                f"config file {config_path} has size of {filesize} bytes, "
                f"maximum allowed size is {MAX_CONFIG_BYTES} bytes"
            )

        with config_path.open(mode="rb") as fp:
            try:
                toml_data = tomllib.load(fp)
            except tomllib.TOMLDecodeError as err:
                raise ConfigError(f"failed to load TOML file: {err}") from err

        try:
            c = cls.model_validate(toml_data)

        except pydantic.ValidationError as err:
            errors = err.errors(include_url=False)
            errors_pretty = map(
                lambda e: str({"field": e["loc"][0], "error": e["msg"]}), errors
            )
            raise ConfigError(
                f"invalid configuration:\n{'\n'.join(errors_pretty)}"
            ) from err

        except Exception as err:
            raise ConfigError(f"invalid configuration: {err}") from err

        return c

    def pretty_print(self) -> str:
        # assumes flat config struct
        return "\n".join([f"{k} = {v}" for k, v in self])


load = Config.load
