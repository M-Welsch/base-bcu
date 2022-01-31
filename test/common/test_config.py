import json
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
from py import path
from pytest_mock import MockFixture

from base.common.config import BoundConfig, Config
from base.common.exceptions import ConfigValidationError


@pytest.fixture()
def config_path(tmpdir: path.local) -> Generator[Path, None, None]:
    config_path = Path(tmpdir)
    BoundConfig.set_config_base_path(config_path)
    yield config_path


def write_test_file(content: Dict[str, Any], file_path: Path) -> None:
    with open(file_path, "w") as jf:
        json.dump(content, jf, indent=4)


def test_config_read_key(config_path: Path) -> None:
    config = Config({"key": "value"})
    assert config.key == "value"


def test_config_read_property(config_path: Path) -> None:
    config = Config({})
    assert config._initialized


def test_config_read_error(config_path: Path) -> None:
    config = Config({})
    with pytest.raises(AttributeError):
        assert config.key == "value"


def test_config_read_only(config_path: Path) -> None:
    config = Config({})
    assert config.is_read_only


def test_config_not_read_only(config_path: Path) -> None:
    config = Config({}, read_only=False)
    assert not config.is_read_only


def test_config_write_key(config_path: Path) -> None:
    config = Config({"key": "value"}, read_only=False)
    config.key = "new_value"
    assert config.key == "new_value"


def test_config_write_key_read_only_error(config_path: Path) -> None:
    config = Config({"key": "value"})
    with pytest.raises(RuntimeError):
        config.key = "new_value"


def test_config_write_key_non_existing_error(config_path: Path) -> None:
    config = Config({"key": "value"}, read_only=False)
    with pytest.raises(AttributeError):
        config.no_key = "other_value"


def test_bound_config_set_base_path() -> None:
    test_path = Path("/test/path")
    BoundConfig.set_config_base_path(test_path)
    assert BoundConfig.base_path == test_path


def test_bound_config_assert_keys(config_path: Path) -> None:
    config_file_name = "test_json"
    write_test_file(content={"key": "value"}, file_path=config_path / config_file_name)
    config = BoundConfig(config_file_name)
    config.assert_keys({"key"})


def test_bound_config_assert_keys_error(config_path: Path) -> None:
    config_file_name = "test_json"
    write_test_file(content={"key": "value"}, file_path=config_path / config_file_name)
    config = BoundConfig(config_file_name)
    with pytest.raises(ConfigValidationError):
        config.assert_keys({"no_key"})


def test_bound_config_read_key(config_path: Path) -> None:
    config_file_name = "test_json"
    write_test_file(content={"key": "value"}, file_path=config_path / config_file_name)
    config = BoundConfig(config_file_name)
    assert config.key == "value"


def test_bound_config_read_only(config_path: Path) -> None:
    config_file_name = "test_json"
    write_test_file(content={}, file_path=config_path / config_file_name)
    config = BoundConfig(config_file_name)
    assert config.is_read_only


def test_bound_config_not_read_only(config_path: Path) -> None:
    config_file_name = "test_json"
    write_test_file(content={}, file_path=config_path / config_file_name)
    config = BoundConfig(config_file_name, read_only=False)
    assert not config.is_read_only


def test_bound_config_write_key(config_path: Path) -> None:
    config_file_name = "test_json"
    write_test_file(content={"key": "value"}, file_path=config_path / config_file_name)
    config = BoundConfig(config_file_name, read_only=False)
    config.key = "new_value"
    assert config.key == "new_value"


def test_bound_config_save(config_path: Path) -> None:
    config_file_name = "test_json"
    write_test_file(content={"key": "value"}, file_path=config_path / config_file_name)
    config = BoundConfig(config_file_name, read_only=False)
    config.key = "new_value"
    config.save()
    with open(config_path / config_file_name, "r") as jf:
        json_object = json.load(jf)
        assert json_object["key"] == "new_value"


def test_bound_config_reload(config_path: Path) -> None:
    config_file_name = "test_json"
    write_test_file(content={"key": "value"}, file_path=config_path / config_file_name)
    config = BoundConfig(config_file_name, read_only=False)
    with open(config_path / config_file_name, "w") as jf:
        json.dump({"key": "new_value"}, jf)
    config.reload()
    assert config.key == "new_value"


def test_bound_config_reload_all(config_path: Path, mocker: MockFixture) -> None:
    patched_reload = mocker.patch("base.common.config.BoundConfig.reload")
    config_file_names = ["test_a.json", "test_b.json"]
    for file_name in config_file_names:
        write_test_file(content={}, file_path=config_path / file_name)
    configs = [BoundConfig(file_name) for file_name in config_file_names]
    patched_reload.reset_mock()
    BoundConfig.reload_all()
    assert patched_reload.call_count == len(configs)
