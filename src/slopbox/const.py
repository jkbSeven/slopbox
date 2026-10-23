from pathlib import Path

VERSION = "0.1.0"

PKG_ROOT = Path(__file__).parent.absolute()

NIX_LIB_PATH = PKG_ROOT / "nix" / "lib"

NIXPKGS_FETCH_URL = "github:nixos/nixpkgs/nixos-unstable"
