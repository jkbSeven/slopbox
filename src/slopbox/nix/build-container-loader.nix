{
  nixpkgsUrl,
  slopboxEnvPath,
  profile,
  engine,
  component,
}:
let
  lib = import ./lib;
  cfg = (lib.config.eval { inherit nixpkgsUrl slopboxEnvPath; }).config;
in
cfg.profiles.${profile}.build.${component}.container-loader.${engine}
