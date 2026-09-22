EXAMPLE_SLOPBOX_CONFIG = """{ pkgs, libSlop, ...}:
  defaults = {
    agent = pkgs.opencode;
  };

  profiles = {
    default = libSlop.mkProfile {
      pkgs = [
        pkgs.python314
        pkgs.uv
      ];

      workspace = "/workspace";
    };
  };
"""
