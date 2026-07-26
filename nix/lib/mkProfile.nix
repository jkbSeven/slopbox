{ lib }:
{
  meta, # { pkgs = ...; lib = ...; } pkgs and lib from nixpkgs
  runtimePkgs,
  agentPkg,
  useBasePkgs
}:
let
  pkgs = (if useBasePkgs then lib.basePkgs meta.pkgs else [ ]) ++ runtimePkgs ++ agentPkg;
in
{
  container = { name, workdir }: meta.pkgs.dockerTools.buildLayeredImage {
    inherit name;
    contents = pkgs;
    config = {
      WorkingDir = workdir;
      Env = [
        "SSL_CERT_FILE=${meta.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
      ];
      Cmd = [ "${meta.pkgs.bash}/bin/bash" ]; # FIXME: assumes user wants bash in the container, should ask user for Cmd as a param
    };
  };
  vm = {};
}
