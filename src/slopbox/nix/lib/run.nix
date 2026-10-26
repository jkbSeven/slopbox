{
  config,
  pkgs,
  lib,
  ...
}:
let
  runContainers =
    {
      name,
      profile,
      engine,
    }:
    let
      mountsStr = (
        if builtins.length profile.mounts > 0 then
          ''
            ${lib.concatMapStringsSep " \\\n" (m: "--volume ${m}") profile.mounts} \
          ''
        else
          ""
      );

      envVarsForProxy = ''
        --env HTTP_PROXY=http://slopbox-proxy-${name}:3128 \
        --env HTTPS_PROXY=http://slopbox-proxy-${name}:3128 \
        --env NO_PROXY=localhost,127.0.0.1 \
      '';

      runtimeImage = "${profile.build.runtime.container.imageName}:${profile.build.runtime.container.imageTag}";
      proxyImage = "${profile.build.proxy.container.imageName}:${profile.build.proxy.container.imageTag}";

      scriptWithProxy = ''
        ${engine} network create slopbox-proxy-${name} >/dev/null
        ${engine} network create --internal slopbox-runtime-${name} >/dev/null

        ${engine} container run \
        --name slopbox-proxy-${name} \
        --network slopbox-proxy-${name} \
        --network slopbox-runtime-${name} \
        --cap-drop ALL \
        --read-only \
        --detach \
        ${proxyImage} >/dev/null

        ${engine} container run \
        --name slopbox-runtime-${name} \
        --network slopbox-runtime-${name} \
        --rm \
        --cap-drop ALL \
        --read-only \
        --interactive \
        --tty \
        --tmpfs ${profile.homeDir} \
        --tmpfs /tmp:exec \
      ''
      + mountsStr
      + envVarsForProxy
      + "${runtimeImage}\n\n"
      + ''
        ${engine} container rm -f slopbox-proxy-${name} >/dev/null
        ${engine} network rm slopbox-proxy-${name} >/dev/null
        ${engine} network rm slopbox-runtime-${name} >/dev/null
      '';

      scriptWithoutProxy = ''
        ${engine} container run \
        --name slopbox-runtime-${name} \
        --rm \
        --cap-drop ALL \
        --read-only \
        --interactive \
        --tty \
        --tmpfs ${profile.homeDir} \
        --tmpfs /tmp:exec \
      ''
      + mountsStr
      + runtimeImage;
    in
    pkgs.writeShellApplication {
      name = "run";
      text = if profile.proxy.enable then scriptWithProxy else scriptWithoutProxy;
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
              docker = runContainers {
                inherit name;
                profile = cfg;
                engine = "docker";
              };
              podman = runContainers {
                inherit name;
                profile = cfg;
                engine = "podman";
              };
            };
            vm = throw "vm runtime is not implemented yet!";
          };
        }
      )
    );
  };
}
