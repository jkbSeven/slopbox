{
  description = "Flake for running AI agents in a secure-ish environment";

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
        genSlopboxImage =
          {
            imageName ? "slopbox",
            imageTag ? "latest",
            pkgs,
            agentPkg,
            additionalPkgs ? [ ],
          }:
          pkgs.dockerTools.buildLayeredImage {
            name = imageName;
            tag = imageTag;

            contents =
              with pkgs;
              [
                bash
                coreutils
                git
                cacert
                curl
                gnugrep
                gnused
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
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfreePredicate =
              pkg:
              builtins.elem (lib.getName pkg) (
                map lib.getName [
                  pkgs.claude-code
                ]
              );
          };
        in
        {
          slopbox = self.lib.genSlopboxImage {
            pkgs = pkgs;
            agentPkg = pkgs.claude-code;
          };

          slopbox-proxy = pkgs.dockerTools.buildLayeredImage {
            name = "slopbox-proxy";
            tag = "latest";

            contents = [
              pkgs._3proxy
              pkgs.cacert
            ];

            config = {
              Env = [
                "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
              ];
            };

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
