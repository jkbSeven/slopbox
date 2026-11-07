from enum import Enum

ENVIRONMENT_SCHEMA_VERSION = 1


class FeaturedAgent(Enum):
    """agent with dedicated support in slopbox"""

    OPENCODE = "opencode"
    CLAUDE = "claude"
    CODEX = "codex"


def _gen_env_config(
    agent_pkg: str,
    mount_preset: str,
    proxy_preset: str,
    extra_config: str | None,
) -> str:
    extra_config = f"\n  {extra_config}\n" if extra_config is not None else ""

    return f"""{{
  config,
  pkgs,
  lib,
  libSlop,
  ...
}}:
{{
  default = {{
    agent = pkgs.{agent_pkg};
    workspace = "/workspace";
  }};

  profiles = {{
    default = {{
      pkgs = [
        pkgs.python314
        pkgs.uv
      ];

      runHook = "echo 'Hello, world!'";

      mounts = [
        (libSlop.presets.mounts.{mount_preset} config.profiles.default.homeDir)
      ];

      proxy.allowlist = [
        libSlop.presets.proxy.{proxy_preset}
        libSlop.presets.proxy.python
        "github.com"
        "*.github.com"
      ];
    }};
  }};
  {extra_config}
  schemaVersion = {ENVIRONMENT_SCHEMA_VERSION};
}}
"""


EXAMPLE_OPENCODE_ENV_CONFIG = _gen_env_config("opencode", "opencode", "opencode", None)
EXAMPLE_CLAUDE_ENV_CONFIG = _gen_env_config(
    "claude-code",
    "claude",
    "claude",
    "nixpkgs.config.allowUnfreePredicate = "  # concatenated with below
    'pkg: builtins.elem (lib.getName pkg) [ "claude-code" ];',
)
EXAMPLE_CODEX_ENV_CONFIG = _gen_env_config("codex", "codex", "codex", None)

AGENT_TO_EXAMPLE_ENV_MAPPING: dict[FeaturedAgent, str] = {
    FeaturedAgent.OPENCODE: EXAMPLE_OPENCODE_ENV_CONFIG,
    FeaturedAgent.CLAUDE: EXAMPLE_CLAUDE_ENV_CONFIG,
    FeaturedAgent.CODEX: EXAMPLE_CODEX_ENV_CONFIG,
}
