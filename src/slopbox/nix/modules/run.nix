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
      # `mounts` is a list of: strings or lists of strings (to accomodate for libSlop.presets)
      finalMounts = lib.lists.flatten profile.mounts;
      finalMountsFormatted = map (
        m:
        let
          opts = if m.opts != null then ":" + (lib.concatStringsSep "," m.opts) else "";
        in
        "${m.from}:${m.to}" + opts
      ) finalMounts;

      mountsStr = (
        if builtins.length profile.mounts > 0 then
          ''
            ${lib.concatMapStringsSep " \\\n" (m: "--volume ${m}") finalMountsFormatted} \
          ''
        else
          ""
      );

      mountsSetup = lib.concatMapStringsSep "\n\n" (
        m:
        if m.type == "dir" then
          ''
            if [ ! -d ${m.from} ]; then
              autocreate=${builtins.toString m.autocreate.enable}
              if [ "$autocreate" -eq 1 ]; then
                printf 'INFO: directory ${m.from} does not exist on the host system, creating...\n'
                mkdir ${m.from} || exit 1
              else
                printf 'ERROR: directory ${m.from} does not exist on the host system\n'
                exit 1
              fi
            fi
          ''
        else
          ''
            if [ ! -f ${m.from} ]; then
              autocreate=${builtins.toString m.autocreate.enable}
              if [ "$autocreate" -eq 1 ]; then
                printf 'INFO: file ${m.from} does not exist on the host system, creating...\n'
                cat > ${m.from} << EOF || exit $?
            ${m.autocreate.payload}
            EOF
              else
                printf 'ERROR: file ${m.from} does not exist on the host system\n'
                exit 1
              fi
            fi
          ''
      ) finalMounts;

      envVarsForProxy = ''
        --env HTTP_PROXY=http://slopbox-proxy-${name}:3128 \
        --env HTTPS_PROXY=http://slopbox-proxy-${name}:3128 \
        --env NO_PROXY=localhost,127.0.0.1 \
      '';

      runtimeImage = "${profile.build.runtime.container.imageName}:${profile.build.runtime.container.imageTag}";
      proxyImage = "${profile.build.proxy.container.imageName}:${profile.build.proxy.container.imageTag}";

      isWorkspaceInMountList =
        builtins.length (
          builtins.filter (m: (builtins.match "^${profile.workspace}$" m.to) != null) finalMounts
        ) > 0;
      workspaceTmpfs = if isWorkspaceInMountList then "" else "--tmpfs ${profile.workspace}:exec \\\n";

      scriptWithProxy = mountsSetup + ''
        cleanup() {
          local oid
          local ok
          ok=1

          for c in slopbox-proxy-${name} slopbox-runtime-${name}; do
            oid=$(${engine} container ls --quiet --filter "name=$c")
            [ -z "$oid" ] && continue

            if ! ${engine} container rm --force "$oid" > /dev/null; then
              printf 'failed to remove container "%s" with id %s, manual intervention required\n' "$c" "$oid"
              ok=0
            fi
          done

          for n in slopbox-proxy-${name} slopbox-runtime-${name}; do
            oid=$(${engine} network ls --quiet --filter "name=$n")
            [ -z "$oid" ] && continue

            if ! ${engine} network rm "$oid" > /dev/null; then
              printf 'failed to remove network "%s" with id %s, manual intervention required\n' "$n" "$oid"
              ok=0
            fi
          done

          [ "$ok" -eq 0 ] && exit 1
          exit 0
        }

        trap 'cleanup' EXIT

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
      + workspaceTmpfs
      + mountsStr
      + envVarsForProxy
      + runtimeImage;

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
      + workspaceTmpfs
      + mountsStr
      + runtimeImage
      + ''
        if [ $? -ne 0 ]; then
          container_id=$(${engine} container ls --quiet --filter 'name=slopbox-runtime-${name}')

          [ -z "$container_id" ] && exit 0

          printf 'failed to remove container upon exit, retrying\n'
          if ! ${engine} container rm --force "$container_id" > /dev/null; then
            printf 'manual intervention required, failed to remove container "slopbox-runtime-${name}" with id %s\n' "$container_id"
            exit 1
          fi
        fi
      '';
    in
    pkgs.writeShellApplication {
      name = "run";
      text = if profile.proxy.enable then scriptWithProxy else scriptWithoutProxy;
      bashOptions = [ ];
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
