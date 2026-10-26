{
  config,
  pkgs,
  lib,
  libSlop,
  ...
}:
let
  runContainers =
    {
      name,
      profile,
      engine,
    }:
    pkgs.writeShellApplication {
      name = "run";
      text = ''
        if [ $# -ne 1 ]; then
          printf 'usage: %s SESSION_ID\n' "$0"
          exit 1
        fi

        SESSION_ID="$1"

        ${engine} network create "slopbox-proxy-${name}-$SESSION_ID"
        ${engine} network create --internal "slopbox-runtime-${name}-$SESSION_ID"

        ${engine} container create \
        --name "slopbox-proxy-${name}-$SESSION_ID" \
        --network "slopbox-proxy-${name}-$SESSION_ID" \
        --network "slopbox-runtime-${name}-$SESSION_ID" \
        --cap-drop ALL \
        --read-only \
        ${profile.build.proxy.container.imageName}:${profile.build.proxy.container.imageTag} \
        3proxy

        ${engine} container start "slopbox-proxy-${name}-$SESSION_ID"
        sleep 3
        ${engine} container run \
        --name "slopbox-runtime-${name}-$SESSION_ID" \
        --network "slopbox-runtime-${name}-$SESSION_ID" \
        --cap-drop ALL \
        --read-only \
        --interactive \
        --tty \
        --tmpfs ${profile.homeDir} \
        --tmpfs /tmp:exec \
        ${lib.concatMapStringsSep "\\\n" (m: "--volume ${m}") profile.mounts} \
        ${profile.build.runtime.container.imageName}:${profile.build.runtime.container.imageTag}
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
        in
        {
          options.run = lib.mkOption {
            readOnly = true;

            type = lib.types.submodule {
              options = {
                container = lib.mkOption {
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

          config.run = {
            container = {
              docker = runContainers { inherit name; profile = cfg; engine = "docker"; };
              podman = runContainers { inherit name; profile = cfg; engine = "podman"; };
            };
            vm = throw "vm runtime is not implemented yet!";
          };
        }
      )
    );
  };
}
