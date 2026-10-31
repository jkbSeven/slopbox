let
  callLib = file: import file { inherit lib; };
  lib = {
    basePkgs = pkgs: [
      pkgs.bash
      pkgs.cacert
      pkgs.coreutils
      pkgs.curl
      pkgs.gitMinimal
      pkgs.gnugrep
      pkgs.gnused
      pkgs.less
      pkgs.man
    ];
    config = {
      eval = callLib ./eval.nix;
    };
  };
in
lib
