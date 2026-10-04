from pathlib import Path
import re

import pytest

from slopbox import config as c


def test_default_slopbox_env_dir(test_home_dir: Path):
    assert c.load().slopbox_env_dir == test_home_dir / ".config" / "slopbox"


def test_custom_config(config: dict, config_file: Path):
    assert c.load(config_file).slopbox_env_dir == Path(config["slopbox_env_dir"])


@pytest.mark.parametrize("config_overrides", [{"non_declared_opt": "hello!"}])
def test_extra_options_not_allowed(config_file: Path):
    with pytest.raises(
        c.ConfigError,
        match=re.escape(
            "{"
            "'field': 'non_declared_opt', "
            "'error': 'Extra inputs are not permitted'"
            "}"
        ),
    ):
        c.load(config_file)
