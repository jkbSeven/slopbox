/*
  Inspired by home-manager nixpkgs.nix module
  https://github.com/nix-community/home-manager/blob/b787c48e2ec57a9d098f5c2721882a3bc1e16f97/modules/misc/nixpkgs.nix
*/
{
  config,
  lib,
  pkgsPath,
  ...
}:
let
  overlayType = lib.mkOptionType {
    name = "nixpkgs-overlay";
    description = "nixpkgs overlay";
    check = lib.isFunction;
    merge = lib.mergeOneOption;
  };
in
{
  options.nixpkgs = {
    config = lib.mkOption {
      type = lib.types.nullOr lib.types.attrs;
      default = null;
    };

    overlays = lib.mkOption {
      type = lib.types.nullOr (lib.types.listOf overlayType);
      default = null;
    };
  };

  config._module.args = {
    pkgs = lib.mkOverride lib.modules.defaultOverridePriority (
      import pkgsPath (lib.filterAttrs (n: v: v != null) config.nixpkgs)
    );
  };
}
