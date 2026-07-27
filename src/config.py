from pathlib import Path
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, Field, TypeAdapter, field_validator, model_validator

from const import Agent, SlopboxRuntime

import presets as slopbox_presets

type NixPkgName = Annotated[str, Field(min_length=1, pattern="^[a-zA-Z0-9_-]+$")]

GENERIC_NAME_PATTERN = "^[a-zA-Z0-9_-]+$"

SCHEMA_VERSION = 1


def _validate_mount_str(v: str) -> str:
    if len(v) < 1:
        raise ValueError("Mount string length must be greater than zero")

    parts = v.split(":")
    if len(parts) < 2 or len(parts) > 3:
        raise ValueError(
            f"Invalid mount string structure, there must be at least 2 parts and at most 3 parts (host:guest:options), got {parts} parts"
        )

    if len(parts) == 2:
        host, guest = parts
        host = Path(host)
        guest = Path(guest)

    if len(parts) == 3:
        host, guest, options = parts
        host = Path(host)
        guest = Path(guest)

        if len(options) < 1:
            raise ValueError("Mount options missing, remove the trailing colon or add an option")

    return v


type MountConfigStr = Annotated[str, AfterValidator(_validate_mount_str)]
type MountPresetName = Annotated[str, Field(min_length=1, pattern=GENERIC_NAME_PATTERN)]
type Mount = MountConfigStr | MountPresetName


class CustomProxy(BaseModel):
    http_proxy: Annotated[str, Field(min_length=1)]
    https_proxy: Annotated[str, Field(min_length=1)] 
    no_proxy: list[Annotated[str, Field(min_length=1)]]


class Proxy(BaseModel):
    enable: bool = True
    allowlist: Annotated[list[Annotated[str, Field(min_length=1)]], Field(default_factory=list)]
    custom: CustomProxy | None = None


class Profile(BaseModel):
    flake: Path | None = None
    pkgs: list[NixPkgName] | None = None
    use_base_pkgs: bool = True

    agent: Agent
    use_default_agent_mounts: bool = True
    use_default_agent_proxy: bool = True

    workdir: Path = Path("/workspace")
    default_runtime: SlopboxRuntime = SlopboxRuntime.CONTAINER

    # "bool | None" because if not set, then we use the global config option
    auto_read_compose_override: bool | None = None
    compose_override_path: Path | None = None

    mounts: Annotated[list[Mount], Field(default_factory=list)]
    proxy: Annotated[Proxy, Field(default_factory=Proxy)]

    @model_validator(mode="after")
    def _validate_exclusive_flake_and_pkgs(self) -> "Profile":
        if self.flake is not None and self.pkgs is not None:
            raise ValueError(
                "Invalid profile config: 'flake' and 'pkgs' are mutually exclusive. If you use flakes, then all pkgs must be defined there"
            )

        return self

    @model_validator(mode="after")
    def _inject_agent_mounts_and_presets(self) -> "Profile":
        if self.use_default_agent_mounts:
            self.mounts.append(self.agent.value)

        if self.use_default_agent_proxy:
            self.proxy.allowlist.append(self.agent.value)

        return self


type ProfilesDict = dict[Annotated[str, Field(min_length=1, pattern=GENERIC_NAME_PATTERN)], Profile]


class Presets(BaseModel):
    mounts: Annotated[dict[Annotated[str, Field(min_length=1, pattern=GENERIC_NAME_PATTERN)], MountConfigStr | list[MountConfigStr]], Field(default_factory=dict)]
    proxy: Annotated[dict[Annotated[str, Field(min_length=1, pattern=GENERIC_NAME_PATTERN)], str | list[str]], Field(default_factory=dict)]


def resolve_presets(src: list[str], presets: dict[str, str | list[str]]) -> list[str]:
    if len(presets) < 1 or len(src) < 1:
        return src

    resolved = []

    for entry in src:

        if entry not in presets:
            resolved.append(entry)
            continue

        t = presets[entry]
        if isinstance(t, list):
            resolved.extend(t)
        else:
            resolved.append(t)

    return resolved


class UserConfig(BaseModel):
    version: int
    auto_read_compose_override: bool = True
    profiles: ProfilesDict
    presets: Presets = Presets()

    @field_validator("version", mode="before")
    @classmethod
    def _validate_supported_schema_version(cls, value: Any) -> int:
        if not isinstance(value, int):
            raise ValueError("'version' field must be an int")

        if value != SCHEMA_VERSION:
            raise ValueError(f"Schema version of your config (version={value}) is not supported. Your version of slopbox expects version {SCHEMA_VERSION}")

        return value

    @model_validator(mode="after")
    def _add_slopbox_presets_to_presets_obj(self) -> "UserConfig":
        # ordering of unions matters! user presets override the builtin ones
        self.presets.mounts = slopbox_presets.mounts | self.presets.mounts
        self.presets.proxy = slopbox_presets.proxy | self.presets.proxy

        return self

    @model_validator(mode="after")
    def _validate_mount_presets_exist(self) -> "UserConfig":
        for name, profile in self.profiles.items():

            for mount in profile.mounts:

                try:
                    TypeAdapter(MountConfigStr).validate_python(mount)

                except ValueError:
                    if self.presets.mounts is None:
                        raise ValueError(
                                f"Invalid mount '{mount}' in profile '{name}'. "
                                "Your config does not define any presets, "
                                "and the given mount is not a valid 'host:guest:options' mount"
                            )

                    if mount not in self.presets.mounts:
                        raise ValueError(
                                f"Invalid mount '{mount}' in profile '{name}'. "
                                "Preset with such name does not exist in your config, "
                                "and the given mount is not a valid 'host:guest:options' mount"
                            )

        return self

    @model_validator(mode="after")
    def _validate_proxy_presets_exist(self) -> "UserConfig":
        for name, profile in self.profiles.items():

            if profile.proxy.enable is False or profile.proxy.allowlist is None:
                return self

            for entry in profile.proxy.allowlist:

                if "." in entry:
                    continue

                if self.presets.proxy is None:
                    raise ValueError(
                            f"Invalid entry in proxy allowlist '{entry}' in profile '{name}'. "
                            "Your config does not define any presets, "
                            "and the given entry is not a valid domain"
                        )

                if entry not in self.presets.proxy:
                    raise ValueError(
                            f"Invalid entry in proxy allowlist '{entry}' in profile '{name}'. "
                            "Preset with such name does not exist in your conifg, "
                            "and the given entry is not a valid domain"
                        )

        return self

    @model_validator(mode="after")
    def _set_compose_override_in_profiles(self) -> "UserConfig":
        for _, profile in self.profiles.items():

            if profile.auto_read_compose_override is None:
                profile.auto_read_compose_override = self.auto_read_compose_override

        return self

    def resolve_presets(self) -> None:
        for _, profile in self.profiles.items():
            profile.mounts = resolve_presets(profile.mounts, self.presets.mounts)
            profile.proxy.allowlist = resolve_presets(profile.proxy.allowlist, self.presets.proxy)
