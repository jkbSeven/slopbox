"""
Runtime configuration for slopbox as a CLI tool,
not for runtime container or vm configuration
"""

import tomllib
from pathlib import Path
from typing import Any

import pydantic

MAX_CONFIG_BYTES = 4096


class RuntimeConfigError(Exception):
    pass


def _walk_dict_keys(d: dict[str, Any], level: int = 1) -> str:
    if level > 3:
        raise RuntimeConfigError(
            "runtime configuration is too nested, maximum allowed depth is 3"
        )

    out = ""

    for key, value in d.items():
        out = key

        if isinstance(value, dict):
            out += f".{_walk_dict_keys(value, level + 1)}"

    return out


class Config(pydantic.BaseModel):
    config_path: str = "~/.config/slopbox"

    model_config = pydantic.ConfigDict(extra="forbid")

    @classmethod
    def load(cls, runtime_config_path: Path) -> Config:
        filesize = runtime_config_path.lstat().st_size

        if filesize > MAX_CONFIG_BYTES:
            raise RuntimeConfigError(
                f"config file {runtime_config_path} has size of {filesize} bytes, "
                f"maximum allowed is {MAX_CONFIG_BYTES} bytes"
            )

        with runtime_config_path.open(mode="rb") as fp:
            try:
                config = tomllib.load(fp)
            except tomllib.TOMLDecodeError as err:
                raise RuntimeConfigError(f"failed to parse TOML file: {err}") from err

        try:
            c = cls.model_validate(config)

        except pydantic.ValidationError as err:
            _err = err.errors(include_url=False)[0]

            _err_msg = err
            if _err["type"] == "extra_forbidden":
                base = str(_err["loc"][0])

                remaining: str | None = None
                if isinstance(_err["input"], dict):
                    remaining = _walk_dict_keys(_err["input"])

                final = f"{base}.{remaining}" if remaining else base

                _err_msg = (
                    "following config option was set but has no effect "
                    f"(check for typos): {final}"
                )

            raise RuntimeConfigError(
                f"invalid runtime configuration: {_err_msg}"
            ) from err

        return c
