{
  config,
  lib,
  ...
}:
let
  t = lib.types;
  nullableOption =
    type:
    lib.mkOption {
      type = t.nullOr type;
      default = null;
    };
  cfg = config;
in
{
  options = {

    default = lib.mkOption {
      type = t.submodule {
        options = {
          agent = nullableOption t.package;
          workspace = nullableOption t.externalPath;
          useBasePkgs = nullableOption t.bool;
        };
      };
    };

    profiles = lib.mkOption {
      type = t.attrsOf (
        t.submodule (
          { name, config, ... }: {
            options = {
              agent = lib.mkOption {
                type = t.package;
                default = cfg.default.agent;
              };

              workspace = lib.mkOption {
                type = t.externalPath;
                default = cfg.default.workspace;
              };

              useBasePkgs = lib.mkOption {
                type = t.bool;
                default = cfg.default.useBasePkgs or true; # 'true' is a sane default if user has not set otherwise
              };

              pkgs = lib.mkOption {
                type = t.listOf t.package;
                default = [ ];
              };

              defaultRuntime = lib.mkOption {
                type = t.enum [
                  "container"
                  "vm"
                ];
                default = "container";
              };

              runHook = lib.mkOption {
                type = t.nullOr t.str;
                default = null;
              };

              user = lib.mkOption {
                type = t.nonEmptyStr;
                default = "agent";
              };

              homeDir = lib.mkOption {
                type = t.externalPath;
                default = "/home/agent";
              };

              env = lib.mkOption {
                type = t.attrsOf t.str;
                default = { };
              };

              mounts = lib.mkOption {
                type = t.listOf t.nonEmptyStr;
                default = [ ];
              };

              proxy = lib.mkOption {
                type = t.submodule {
                  options = {
                    enable = lib.mkOption {
                      type = t.bool;
                      default = true;
                    };

                    allowlist = lib.mkOption {
                      type = t.listOf t.nonEmptyStr;
                      default = [ ];
                    };

                    addr = lib.mkOption {
                      type = t.nullOr t.nonEmptyStr;
                      default = null;
                    };
                  };
                };
              };
            };
          }
        )
      );
    };

    schemaVersion = lib.mkOption {
      type = t.ints.positive;
    };
  };
}
