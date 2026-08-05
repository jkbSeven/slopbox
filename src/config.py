import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Annotated, Any, cast

import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic import AfterValidator, BaseModel, Field, TypeAdapter, field_validator, model_validator

import presets as slopbox_presets
from const import UNFREE_AGENTS, Agent, SlopboxRuntime

SCHEMA_VERSION = 1
TEMPLATES_PATH = Path(__file__).parent / "templates"

GENERIC_NAME_PATTERN = "^[a-zA-Z0-9_][a-zA-Z0-9][a-zA-Z0-9_-]*$"
type NameStr = Annotated[str, Field(min_length=1, pattern=GENERIC_NAME_PATTERN)]

jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))

logger = logging.getLogger()

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


class ProfileHashes(BaseModel):
    profile: str
    container_image: str


type ProfilesHashes = dict[NameStr, ProfileHashes]


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

    def container_image_hash(self) -> str:
        return hashlib.sha256(
            self.model_dump_json(include=set(["pkgs", "use_base_pkgs", "agent"])).encode(encoding="utf-8")
        ).hexdigest()

    def make_profile_hashes(self) -> ProfileHashes:
        return ProfileHashes(
            profile=self.hash(),
            container_image=self.container_image_hash(),
        )

    def render_proxy_config(self) -> str:
        # TODO: if custom then add redirect in the 3proxy cfg
        # we need to have 3proxy regardless of user's custom proxy
        template = jinja_env.get_template("3proxy.cfg.j2")
        return template.render(allowlist=self.proxy.allowlist)

    def render_compose_config(self) -> str:
        data = yaml.safe_load((TEMPLATES_PATH / "compose.yaml").read_text())

        if len(self.mounts) > 0:
            data["services"]["agent"]["volumes"] = self.mounts

        data["services"]["agent"]["working_dir"] = str(self.workdir)

        data["services"]["agent"]["image"] = f"slopbox:{self.container_image_hash()}"
        data["services"]["proxy"]["image"] = f"slopbox-proxy:{self.hash()}"

        return yaml.safe_dump(data, sort_keys=False)

    def render_flake(self, profile_name: str) -> str:
        if self.flake is not None:
            raise NotImplementedError()

        template = jinja_env.get_template("flake.nix.j2")

        return template.render(
            profile_name=profile_name,
            pkgs=" ".join(self.pkgs),
            agent_pkg=self.agent.value,
            unfree_agent=self.agent in UNFREE_AGENTS,
            use_base_pkgs="true" if self.use_base_pkgs else "false",
            workdir=self.workdir,
            container_tag=self.container_image_hash(),
            proxy_tag=self.hash(),
        )


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
            raise Exception("Profile directory already exists, not overwriting")

        profile_dir.mkdir(parents=True)

        if profile.proxy.enable:
            (profile_dir / "3proxy.cfg").write_text(profile.render_proxy_config())

        compose_path = profile_dir / "compose.yaml"
        compose_path.write_text(profile.render_compose_config())

        flake_path = profile_dir / "flake.nix"
        flake_path.write_text(profile.render_flake(profile_name))

        for image in ("slopbox", "slopbox-proxy"):

            logger.info(f"building the '{image}' image from flake ({flake_path})")
            subprocess.run(
                ["nix", "--extra-experimental-features", "nix-command flakes", "build", f"{flake_path}#{image}"],
                check=True,
                capture_output=True,
            )

            logger.info(f"loading the '{image}' image to docker")
            subprocess.run(
                ["docker", "load", "-i", "result"],
                check=True,
                capture_output=True,
            )

            logger.debug(f"unlinking the nix build result (exists: {Path('result').exists()})")
            Path("result").unlink()

    def run(self, profile_name: str, state_dir: Path, linger: bool) -> None:
        self.resolve_presets()

        # casting to Profile type after profile refs have been resolved
        self.resolve_profile_refs()
        profile = cast(Profile, self.profiles[profile_name])

        profile_hash = profile.hash()
        profile_dir = state_dir / profile_hash

        if not profile_dir.exists():
            raise Exception(
                f"Profile '{profile_name}' has not been built yet (missing dir: {profile_dir}). "
                f"You have to run `slopbox build --profile {profile}` first. "
                f"If you use a custom state dir, pass the `--state-dir <path>` option "
                "or set the SLOPBOX_STATE_DIR env var"
            )

        compose_path = profile_dir / "compose.yaml"
        if not compose_path.exists():
            raise Exception(
                f"Docker compose.yaml file does not exist in the '{profile_name}' profile directory. "
                f"Remove the {profile_dir} directory and rebuild with `slopbox build --profile {profile_name}"
            )

        docker_compose_cmd = ["docker", "compose", "-f", str(compose_path)]
        if profile.auto_read_compose_override:
            override_path = profile.compose_override_path or (profile_dir / "compose.override.yaml")

            if override_path.exists():
                docker_compose_cmd.extend(["-f", str(override_path)])
            else:
                logger.warning(
                    "Config option 'auto_read_compose_override' is set to true, "
                    f"however, the compose override file ({override_path}) does not exist. "
                    f"To disable this warning set 'auto_read_compose_override' to 'false' for profile '{profile_name}'"
                )

        logger.info("spinning up proxy container")
        subprocess.run(
            docker_compose_cmd + ["up", "--detach", "proxy"],
            check=True,
            capture_output=True,
        )

        logger.info("spinning up agent container")
        subprocess.run(
            docker_compose_cmd + ["run", "agent", "bash"],  # FIXME: assumes bash
            check=True,
        )

        if not linger:
            logger.info("stopping containers")
            subprocess.run(
                # need to remove orphans as docker has issues with long container names
                # and we're unable to stop them manually with `docker stop ...`
                docker_compose_cmd + ["down", "--remove-orphans"],
                check=True,
                capture_output=True,
            )
