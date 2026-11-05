{ lib }:
{
  pkgs ? null,
  nixpkgsUrl ? null,
  slopboxEnvPath ? null,
  slopboxEnv ? null,
}:
assert
  (pkgs != null || nixpkgsUrl != null) || throw "you must pass one of 'nixpkgs' or 'nixpkgsUrl'";
assert
  (slopboxEnv != null || slopboxEnvPath != null)
  || throw "you must pass one of 'slopboxEnv' or 'slopboxEnvPath'";

let
  _pkgs = if pkgs != null then pkgs else (import (builtins.fetchTree nixpkgsUrl) { });
  _slopboxEnv = if slopboxEnv != null then slopboxEnv else (import slopboxEnvPath);
  libSlop = lib;
in
_pkgs.lib.evalModules {
  modules = [
    ({ config, lib, ... }: {
      config._module.args = {
        inherit libSlop;
        pkgs = lib.mkDefault _pkgs;
        pkgsPath = _pkgs.path;
      };
    })
    ./nixpkgs.nix
    ./schema.nix
    ./minimal.nix
    ./build.nix
    ./run.nix
    _slopboxEnv
  ];
}
