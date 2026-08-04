import hashlib
from pathlib import Path
from typing import Annotated, Any, cast

from jinja2 import Environment, FileSystemLoader
from pydantic import AfterValidator, BaseModel, Field, TypeAdapter, field_validator, model_validator

import presets as slopbox_presets
from const import Agent, SlopboxRuntime

GENERIC_NAME_PATTERN = "^[a-zA-Z0-9_][a-zA-Z0-9][a-zA-Z0-9_-]*$"

SCHEMA_VERSION = 1

type NameStr = Annotated[str, Field(min_length=1, pattern=GENERIC_NAME_PATTERN)]

jinja_env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))


def _validate_mount_str(v: str) -> str:
    if len(v) < 1:
        raise ValueError("Mount string length must be greater than zero")

    parts = v.split(":")
    if len(parts) < 2 or len(parts) > 3 or any(map(lambda p: p == "", parts)):
        raise ValueError(
            "Invalid mount string structure, "
            "there must be at least 2 parts and at most 3 parts (host:guest:options) "
            f"with non-empty values, got {len(parts)} parts: {parts}"
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
type MountPresetName = NameStr
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
    pkgs: list[NameStr] | None = None
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
    def _validate_exclusive_flake_and_pkgs(self) -> Profile:
        if self.flake is not None and self.pkgs is not None:
            raise ValueError(
                "Invalid profile config: 'flake' and 'pkgs' are mutually exclusive. "
                "If you use flakes, then all pkgs must be defined there"
            )

        return self

    @model_validator(mode="after")
    def _inject_agent_mounts_and_presets(self) -> Profile:
        if self.use_default_agent_mounts:
            self.mounts.append(self.agent.value)

        if self.use_default_agent_proxy:
            self.proxy.allowlist.append(self.agent.value)

        return self

    def hash(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode(encoding="utf-8")).hexdigest()

    def render_proxy_config(self) -> str:
        template = jinja_env.get_template("3proxy.cfg.j2")
        return template.render(allowlist=self.proxy.allowlist)


type ProfilesDict = dict[NameStr, Profile | NameStr]


class Presets(BaseModel):
    mounts: Annotated[dict[NameStr, MountConfigStr | list[MountConfigStr]], Field(default_factory=dict)]
    proxy: Annotated[dict[NameStr, str | list[str]], Field(default_factory=dict)]


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
            raise ValueError(
                f"Schema version of your config (version={value}) is not supported. "
                f"Current slopbox release expects version {SCHEMA_VERSION}"
            )

        return value

    @model_validator(mode="after")
    def _add_slopbox_presets_to_presets_obj(self) -> UserConfig:
        # ordering of unions matters! user presets override the builtin ones
        self.presets.mounts = slopbox_presets.mounts | self.presets.mounts
        self.presets.proxy = slopbox_presets.proxy | self.presets.proxy

        return self

    @model_validator(mode="after")
    def _validate_referenced_profiles_exist(self) -> UserConfig:
        for name, profile in self.profiles.items():

            # regular Profile obj
            if isinstance(profile, Profile):
                continue

            # referenced profile is present in profiles dict
            if profile in self.profiles:
                continue

            raise ValueError(f"Profile '{name}' references a nonexistent profile '{profile}'")

        return self

    @model_validator(mode="after")
    def _validate_mount_presets_exist(self) -> UserConfig:
        for name, profile in self.profiles.items():

            # in case of profile reference
            if not isinstance(profile, Profile):
                continue

            for mount in profile.mounts:
                try:
                    TypeAdapter(MountConfigStr).validate_python(mount)

                except ValueError as err:
                    if self.presets.mounts is None:
                        raise ValueError(
                            f"Invalid mount '{mount}' in profile '{name}'. "
                            "Your config does not define any presets, "
                            "and the given mount is not a valid 'host:guest:options' mount"
                        ) from err

                    if mount not in self.presets.mounts:
                        raise ValueError(
                            f"Invalid mount '{mount}' in profile '{name}'. "
                            "Preset with such name does not exist in your config, "
                            "and the given mount is not a valid 'host:guest:options' mount"
                        ) from err

        return self

    @model_validator(mode="after")
    def _validate_proxy_presets_exist(self) -> UserConfig:
        for name, profile in self.profiles.items():

            # in case of profile reference
            if not isinstance(profile, Profile):
                continue

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
    def _set_compose_override_in_profiles(self) -> UserConfig:
        for _, profile in self.profiles.items():

            # in case of profile reference
            if not isinstance(profile, Profile):
                continue

            if profile.auto_read_compose_override is None:
                profile.auto_read_compose_override = self.auto_read_compose_override

        return self

    def resolve_presets(self) -> None:
        for _, profile in self.profiles.items():

            # in case of profile reference
            if not isinstance(profile, Profile):
                continue

            profile.mounts = resolve_presets(profile.mounts, self.presets.mounts)
            profile.proxy.allowlist = resolve_presets(profile.proxy.allowlist, self.presets.proxy)

    def resolve_profile_refs(self) -> None:
        resolved: dict[NameStr, NameStr] = {}  # profile name -> name of the last node that's an actual profile type
        visiting = set()
        refs = {name: profile for name, profile in self.profiles.items() if not isinstance(profile, Profile)}

        def _resolve(v: str) -> NameStr:
            if v in visiting:
                raise Exception(f"Detected a reference cycle for profile '{v}'")

            if v in resolved:
                return resolved[v]

            visiting.add(v)
            ref = refs[v]

            if ref in refs:
                n = _resolve(ref)

                resolved[v] = n
                visiting.remove(v)

                return n

            else:
                resolved[v] = ref
                visiting.remove(v)

                return ref

        for v in refs:
            self.profiles[v] = self.profiles[_resolve(v)]


    def build(self, profile_name: str, state_dir: Path) -> None:
        self.resolve_presets()

        # casting to Profile type after profile refs have been resolved
        self.resolve_profile_refs()
        profile = cast(Profile, self.profiles[profile_name])

        profile_hash = profile.hash()
        profile_dir = state_dir / profile_hash

        if profile_dir.is_dir():
            raise Exception("Profile build exists already")

        profile_dir.mkdir(parents=True)
