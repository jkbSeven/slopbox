{
  nixpkgsUrl,
  slopboxEnvPath,
  profile,
}:
let
  lib = import ./lib;
  cfg = (lib.config.eval { inherit nixpkgsUrl slopboxEnvPath; }).config;
  plainProfile = cfg.profiles.${profile};
  strippedProfile = removeAttrs plainProfile [ "build" ];
  containerImagesMetadata = {
    runtime = {
      image = "${plainProfile.build.runtime.container.imageName}:${plainProfile.build.runtime.container.imageTag}";
      storePath = "${plainProfile.build.runtime.container}";
    };
    proxy =
      if !plainProfile.proxy.enable then
        null
      else
        {
          image = "${plainProfile.build.proxy.container.imageName}:${plainProfile.build.proxy.container.imageTag}";
          storePath = "${plainProfile.build.proxy.container}";
        };
  };
in
{
  # wrapped in attr set as otherwise I'm unable to read the value from `nix eval --file ...`
  out = builtins.toJSON {
    profile = strippedProfile;
    containers = containerImagesMetadata;
  };
}
