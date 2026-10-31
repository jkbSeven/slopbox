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
          { name, ... }: {
            options = {
              agent = lib.mkOption {
                type = t.package;
                default = config.default.agent;
              };

              workspace = lib.mkOption {
                type = t.externalPath;
                default = config.default.workspace;
              };

              useBasePkgs = lib.mkOption {
                type = t.bool;
                default = if config.default.useBasePkgs != null then config.default.useBasePkgs else true;
              };

              pkgs = lib.mkOption {
                type = t.listOf t.package;
                default = [ ];
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
                default = "/home/${config.profiles.${name}.user}";
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
