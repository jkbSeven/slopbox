{
  description = "Flake for running AI agents in a secure-ish environemnt";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;
    in
    {
      lib = {
        genImage =
          {
            pkgs,
            agentPkg,
            additionalPkgs ? [ ],
          }:
          pkgs.dockerTools.buildLayeredImage {
            name = "agentic-dev-env";
            tag = "latest";

            contents =
              with pkgs;
              [
                bash
                coreutils
                git
                cacert
                agentPkg
              ]
              ++ additionalPkgs;

            config = {
              WorkingDir = "/workspace";
              Env = [
                "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
              ];
              Cmd = [ "${pkgs.bash}/bin/bash" ];
            };

          };
      };

      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          image = self.lib.genImage {
            pkgs = pkgs;
            agentPkg = pkgs.opencode;
          };
        }
      );

      formatter = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        pkgs.nixfmt
      );
    };
}
