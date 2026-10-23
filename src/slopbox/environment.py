EXAMPLE_ENV_CONFIG = """{
  pkgs,
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
    };
  };

  schemaVersion = 1;
}
"""
