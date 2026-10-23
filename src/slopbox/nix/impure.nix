{
  nixpkgsUrl,
  slopboxEnvPath,
  profile,
  engine
}:
let
  lib = import ./lib;
in
(lib.config.eval { inherit nixpkgsUrl slopboxEnvPath; }).config.profiles.${profile}.build.runtime.container-loader.${engine}
