import logging
import subprocess
from typing import Annotated

import pydantic


class NixError(Exception):
    pass


class NixFetchTreeResult(pydantic.BaseModel):
    """
    example fetchTree output for github:nixos/nixpkgs/nixos-unstable:
    {
      "lastModified": 1790046670,
      "lastModifiedDate": "20260922031110",
      "narHash": "sha256-MYiI+CzL0tuWgRPjGsKCDHqYs2T3OzMlMQWOYWG0qso=",
      "rev": "6774f7bc253789b113a4f39285dc0fa100abeacc",
      "shortRev": "6774f7b"
    }
    """

    url: str | None = None  # this makes updating trivial, set manually
    last_modified: Annotated[int, pydantic.Field(alias="lastModified")]
    last_modified_date: Annotated[str, pydantic.Field(alias="lastModifiedDate")]
    nar_hash: Annotated[str, pydantic.Field(alias="narHash")]
    rev: str
    shortRev: Annotated[str, pydantic.Field(alias="shortRev")]


class SlopboxLock(pydantic.BaseModel):
    nixpkgs: NixFetchTreeResult
    slopbox: NixFetchTreeResult


class Nix:
    experimental_features = ["fetch-tree", "flakes", "nix-command"]

    @classmethod
    def build_cmd(cls, cmd: list[str]) -> list[str]:
        return [
            "nix",
            "--extra-experimental-features",
            " ".join(cls.experimental_features),
        ] + cmd

    @classmethod
    def version(cls) -> str:
        result = subprocess.run(cls.build_cmd(["--version"]), capture_output=True)

        if result.returncode != 0:
            raise NixError(
                "Unable to check Nix version, "
                "make sure you've installed Nix on your system (https://nixos.org/)"
            )

        # example output: `nix (Nix) 2.34.8`
        # for Determinate Systems: `nix (Determinate Nix ...) 2.34.8`
        return result.stdout.decode(encoding="utf-8").split()[-1]

    @classmethod
    def is_available(cls) -> bool:
        try:
            _ = cls.version()
            ok = True
        except NixError:
            ok = False

        return ok

    @classmethod
    def fetch_tree(cls, url: str) -> NixFetchTreeResult:
        cmd = cls.build_cmd(
            [
                "eval",
                "--json",
                "--impure",
                "--expr",
                f'builtins.removeAttrs (builtins.fetchTree {url}) [ "outPath" ]',
            ]
        )

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            err = result.stderr.decode(encoding="utf-8")
            logging.debug(f"Nix command '{cmd}' failed, stderr: {err}")
            raise NixError(
                f"failed to fetch the '{url}' resource with Nix fetchTree: {err}"
            )

        r = NixFetchTreeResult.model_validate_json(
            result.stdout.decode(encoding="utf-8")
        )
        r.url = url

        return r
