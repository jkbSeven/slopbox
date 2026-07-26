from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, TypeAdapter, model_validator

from const import Agent, SlopboxRuntime

type UserConfigVersion = Annotated[int, Field(ge=1)]
type NixPkgName = Annotated[str, Field(min_length=1, pattern="[a-zA-Z0-9_-]+")]


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
type MountPresetName = Annotated[str, Field(min_length=1, pattern="[a-zA-Z0-9_-]+")]
type Mount = MountConfigStr | MountPresetName


class CustomProxy(BaseModel):
    http_proxy: Annotated[str, Field(min_length=1)]
    https_proxy: Annotated[str, Field(min_length=1)] 
    no_proxy: list[Annotated[str, Field(min_length=1)]]


class Proxy(BaseModel):
    enable: bool = True
    allowlist: list[Annotated[str, Field(min_length=1)]] | None = None
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

    mounts: list[Mount] | None = None
    proxy: Proxy = Proxy()

    @model_validator(mode="after")
    def _validate_exclusive_flake_and_pkgs(self) -> "Profile":
        if self.flake is not None and self.pkgs is not None:
            raise ValueError(
                "Invalid profile config: 'flake' and 'pkgs' are mutually exclusive. If you use flakes, then all pkgs must be defined there"
            )

        return self


type ProfilesDict = dict[Annotated[str, Field(min_length=1, pattern="[a-zA-Z0-9_-]")], Profile]


class Presets(BaseModel):
    mounts: dict[Annotated[str, Field(min_length=1, pattern="[a-zA-Z0-9_-]")], MountConfigStr | list[MountConfigStr]] | None = None
    proxy: dict[Annotated[str, Field(min_length=1, pattern="[a-zA-Z0-9_-]")], str | list[str]] | None = None


class UserConfig(BaseModel):
    version: UserConfigVersion
    auto_read_compose_override: bool = True
    profiles: ProfilesDict
    presets: Presets = Presets()

    @model_validator(mode="after")
    def _validate_mount_presets_exist(self) -> "UserConfig":
        for name, profile in self.profiles.items():

            if profile.mounts is None:
                return self

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

            if profile.mounts is not None and self.presets.mounts is not None:

                resolved_mounts = []
                for mount in profile.mounts:

                    if mount not in self.presets.mounts:
                        resolved_mounts.append(mount)
                        continue

                    t = self.presets.mounts[mount]
                    if isinstance(t, list):
                        resolved_mounts.extend(t)
                    else:
                        resolved_mounts.append(t)

                profile.mounts = resolved_mounts

            if profile.proxy.allowlist is not None and self.presets.proxy is not None:

                resolved_entries = []
                for entry in profile.proxy.allowlist:

                    if entry not in self.presets.proxy:
                        resolved_entries.append(entry)
                        continue

                    t = self.presets.proxy[entry]
                    if isinstance(t, list):
                        resolved_entries.extend(t)
                    else:
                        resolved_entries.append(t)

                profile.proxy.allowlist = resolved_entries
