import re
from unittest.mock import MagicMock, patch

import pytest

from slopbox.nix import Nix, NixError

@pytest.mark.parametrize(
    ("fake_bin_mode", "fake_bin_files", "expected"),
    (
        (0o700, ["hello"], False),
        (0o700, ["nix"], True),
        (0o600, ["nix"], False),  # not executable
    )
)
@pytest.mark.usefixtures("fake_bin")
def test_nix_is_available(expected: bool):
    assert Nix.is_available() is expected


@pytest.mark.parametrize(
    ("args", "expected"),
    (
        (
            ["--version"], 
            [
                "nix",
                "--extra-experimental-features",
                "fetch-tree flakes nix-command",
                "--version",
            ]
        ),
        (
            [
                "eval",
                "--json",
                "--impure",
                "--expr",
                'builtins.removeAttrs (builtins.fetchTree URL) [ "outPath" ]',
            ], 
            [
                "nix",
                "--extra-experimental-features",
                "fetch-tree flakes nix-command",
                "eval",
                "--json",
                "--impure",
                "--expr",
                'builtins.removeAttrs (builtins.fetchTree URL) [ "outPath" ]',
            ]
        ),
    )
)
def test_nix_build_cmd_helper(args: list[str], expected: list[str]):
    assert Nix.build_cmd(args) == expected


def test_nix_fetch_tree_output_building():
    data = """{
      "lastModified": 1790046670,
      "lastModifiedDate": "20260922031110",
      "narHash": "sha256-MYiI+CzL0tuWgRPjGsKCDHqYs2T3OzMlMQWOYWG0qso=",
      "rev": "6774f7bc253789b113a4f39285dc0fa100abeacc",
      "shortRev": "6774f7b"
    }"""
    url = "github:nonexistent-owner/nonexistent-repo"

    with patch("slopbox.nix.subprocess") as mock_subprocess:
        result = MagicMock(returncode=0)
        result.stdout.decode.return_value = str(data)
        mock_subprocess.run.return_value = result

        tree = Nix.fetch_tree(url)
        assert tree.last_modified == 1790046670
        assert tree.last_modified_date == "20260922031110"
        assert tree.nar_hash == "sha256-MYiI+CzL0tuWgRPjGsKCDHqYs2T3OzMlMQWOYWG0qso="
        assert tree.rev == "6774f7bc253789b113a4f39285dc0fa100abeacc"
        assert tree.shortRev == "6774f7b"
        assert tree.url == url


def test_nix_fetch_tree_cmd_error():
    url = "github:nonexistent-owner/nonexistent-repo"
    err = "some error"

    with patch("slopbox.nix.subprocess") as mock_subprocess:
        result = MagicMock(returncode=1)
        result.stderr.decode.return_value = err
        mock_subprocess.run.return_value = result

        with pytest.raises(
            NixError,
            match=re.escape(f"failed to fetch the '{url}' resource with Nix fetchTree: {err}")
        ):
            Nix.fetch_tree(url)

def test_nix_version_cmd_error():
    with patch("slopbox.nix.subprocess") as mock_subprocess:
        result = MagicMock(returncode=1)
        result.stderr.decode.return_value = "some error"
        mock_subprocess.run.return_value = result

        with pytest.raises(NixError):
            Nix.version()
