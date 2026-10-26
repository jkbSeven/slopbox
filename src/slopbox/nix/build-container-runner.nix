{
  nixpkgsUrl,
  slopboxEnvPath,
  profile,
  engine,
}:
let
  lib = import ./lib;
  cfg = (lib.config.eval { inherit nixpkgsUrl slopboxEnvPath; }).config;
in
cfg.profiles.${profile}.run.container.${engine}
