{
  config,
  pkgs,
  lib,
  libSlop,
  ...
}:
let
  loadImage = engine: drv: pkgs.writeShellApplication {
    name = "loader";
    text = ''
      while IFS=':' read -r image_name image_tag; do
        if [ "$image_name" = "${drv.imageName}" ] && [ "$image_tag" = "${drv.imageTag}" ]; then
          printf 'Image %s:%s was already loaded, not loading again\n' "$image_name" "$image_tag"
          exit 0
        fi
      done < <(${engine} image ls --format '{{ printf "%s:%s" .Repository .Tag}}')

      ${engine} load < ${drv}
    '';
  };
in
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
                      container-loader = lib.mkOption {
                        type = lib.types.submodule {
                          options = {
                            docker = lib.mkOption {
                              type = lib.types.package;
                            };
                            podman = lib.mkOption {
                              type = lib.types.package;
                            };
                          };
                        };
                      };
                      vm = lib.mkOption {
                        type = lib.types.package;
                      };
                    };
                  };
                };

                proxy = lib.mkOption {
                  type = lib.types.submodule {
                    options = {
                      container = lib.mkOption {
                        type = lib.types.package;
                      };
                      container-loader = lib.mkOption {
                        type = lib.types.submodule {
                          options = {
                            docker = lib.mkOption {
                              type = lib.types.package;
                            };
                            podman = lib.mkOption {
                              type = lib.types.package;
                            };
                          };
                        };
                      };
                    };
                  };
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
                          if cfg.runHook != null then
                            "${cfg.runHook}\nexec ${pkgs.bash}/bin/bash"
                          else
                            "exec ${pkgs.bash}/bin/bash";
                        bashOptions = [ ];
                      };
                    in
                    [ (lib.getExe entrypointScript) ];
                };
              };
              container-loader = {
                docker = loadImage "docker" cfg.build.runtime.container;
                podman = loadImage "podman" cfg.build.runtime.container;
              };
              vm = throw "vm runtime is not implemented yet!";
            };

            proxy = {
              container = pkgs.dockerTools.buildLayeredImage {
                name = "slopbox-proxy-${name}";
                contents = [ pkgs._3proxy ];
              };
              container-loader = {
                docker = loadImage "docker" cfg.build.proxy.container;
                podman = loadImage "podman" cfg.build.proxy.container;
              };
            };
          };
        }
      )
    );
  };
}
