let
  callLib = file: import file { inherit lib; };
  lib = {
    basePkgs = pkgs: [
      pkgs.bash
      pkgs.coreutils
      pkgs.git
      pkgs.cacert
      pkgs.curl
      pkgs.gnugrep
      pkgs.gnused
      pkgs.man
      pkgs.less
    ];
    mkProfile = callLib ./mkProfile.nix;
  };
in
lib
