{
  config,
  pkgs,
  lib,
  libSlop,
  ...
}:
{
  options.profiles = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule (
        { name, ... }:
        let
          cfg = config.profiles.${name};

          basePkgs = libSlop.basePkgs pkgs;
        in
        {
          options.build = lib.mkOption {
            readOnly = true;

            type = lib.types.submodule {
              options = {
                runtime = lib.mkOption {
                  type = lib.types.submodule {
                    options = {
                      container = lib.mkOption {
                        type = lib.types.package;
                      };
                      vm = lib.mkOption {
                        type = lib.types.package;
                      };
                    };
                  };
                };

                proxy = lib.mkOption {
                  type = lib.types.package;
                };
              };
            };
          };

          config.build = {
            runtime = {
              container = pkgs.dockerTools.buildLayeredImage {
                name = "slopbox-runtime-${name}";
                contents = cfg.pkgs ++ (if cfg.useBasePkgs then basePkgs else [ ]);
                config = {
                  Env = map (entry: "${entry.name}=${entry.value}") (lib.attrsToList cfg.env);
                  WorkingDir = cfg.workspace;
                  Entrypoint =
                    let
                      entrypointScript = pkgs.writeShellApplication {
                        name = "entrypoint";
                        text =
                          if cfg.runHook != "" then
                            "${cfg.runHook}\nexec ${pkgs.bash}/bin/bash"
                          else
                            "exec ${pkgs.bash}/bin/bash";
                        bashOptions = [ ];
                      };
                    in
                    [ (lib.getExe entrypointScript) ];
                };
              };
              vm = throw "vm runtime is not implemented yet!";
            };

            proxy = pkgs.dockerTools.buildLayeredImage {
              name = "slopbox-proxy-${name}";
              contents = [ pkgs._3proxy ];
            };
          };
        }
      )
    );
  };
}
