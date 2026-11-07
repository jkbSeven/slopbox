ENVIRONMENT_SCHEMA_VERSION = 1

EXAMPLE_OPENCODE_ENV_CONFIG = """{
  config,
  pkgs,
  libSlop,
  ...
}:
{
  default = {
    agent = pkgs.opencode;
    workspace = "/workspace";
  };

  profiles = {
    default = {
      pkgs = [
        pkgs.python314
        pkgs.uv
      ];

      runHook = "echo 'Hello, world!'";

      mounts = [
        (libSlop.presets.mounts.opencode config.profiles.default.homeDir)
      ];

      proxy.allowlist = [
        libSlop.presets.proxy.opencode
        libSlop.presets.proxy.python
        "github.com"
        "*.github.com"
      ];
    };
  };

  schemaVersion = @schema@;
}
""".replace("@schema@", str(ENVIRONMENT_SCHEMA_VERSION))
# not using f-strings because all curly braces would need to be escaped

EXAMPLE_CLAUDE_ENV_CONFIG = """{
  pkgs,
  libSlop,
  ...
}:
{
  default = {
    agent = pkgs.claude-code;
    workspace = "/workspace";
  };

  profiles = {
    default = {
      pkgs = [
        pkgs.python314
        pkgs.uv
      ];

      runHook = "echo 'Hello, world!'";

      mounts = [
        (libSlop.presets.mounts.claude config.profiles.default.homeDir)
      ];

      proxy.allowlist = [
        libSlop.presets.proxy.claude
        libSlop.presets.proxy.python
        "github.com"
        "*.github.com"
      ];
    };
  };

  nixpkgs.config.allowUnfreePredicate = pkg: builtins.elem (lib.getName pkg) [ "claude-code" ];

  schemaVersion = @schema@;
}
""".replace("@schema@", str(ENVIRONMENT_SCHEMA_VERSION))  # noqa: E501

EXAMPLE_CODEX_ENV_CONFIG = """{
  pkgs,
  libSlop,
  ...
}:
{
  default = {
    agent = pkgs.codex;
    workspace = "/workspace";
  };

  profiles = {
    default = {
      pkgs = [
        pkgs.python314
        pkgs.uv
      ];

      runHook = "echo 'Hello, world!'";

      mounts = [
        (libSlop.presets.mounts.codex config.profiles.default.homeDir)
      ];

      proxy.allowlist = [
        libSlop.presets.proxy.codex
        libSlop.presets.proxy.python
        "github.com"
        "*.github.com"
      ];
    };
  };

  schemaVersion = @schema@;
}
""".replace("@schema@", str(ENVIRONMENT_SCHEMA_VERSION))

EXAMPLE_ENV_TO_AGENT_MAPPING: dict[str, str] = {
    "opencode": EXAMPLE_OPENCODE_ENV_CONFIG,
    "claude": EXAMPLE_CLAUDE_ENV_CONFIG,
    "codex": EXAMPLE_CODEX_ENV_CONFIG,
}
