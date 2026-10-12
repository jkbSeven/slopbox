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
  _pkgs = if pkgs != null then pkgs else (import (builtins.fetchTree nixpkgsUrl) { system = "x86_64-linux"; });
  _slopboxEnv = if slopboxEnv != null then slopboxEnv else (import slopboxEnvPath);
in
_pkgs.lib.evalModules {
  modules = [
    ({ config, ... }: { config._module.args = { pkgs = _pkgs; }; })
    ./schema.nix
    ./minimal.nix
    _slopboxEnv
  ];
}
