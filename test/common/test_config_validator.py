import json
from pathlib import Path
from tempfile import SpooledTemporaryFile
from time import sleep
from typing import Optional, Union

import pytest
from _pytest.tmpdir import tmp_path
from py import path

from base.common.config import BoundConfig, Config
from base.common.config_validator import ConfigValidator


@pytest.mark.parametrize(
    "testkey_value, testkey_datatype, valid",
    [
        (4, "int", True),
        (4.1, "int", False),
        ("4", "int", False),
        (True, "int", False),
        ("s", "str", True),
        (1, "str", False),
        (True, "str", False),
        ("/", "pathlib.Path", True),
        (4, "pathlib.Path", False),
        (True, "pathlib.Path", False),
        (True, "bool", True),
        ("True", "bool", False),
        (1, "bool", False),
        (1.5, "float", True),
        (1, "float", False),
        ("1.5", "float", False),
        (True, "float", False),
    ],
)
def test_check_type_validity(testkey_value: Union[int, str, float, bool], testkey_datatype: str, valid: bool) -> None:
    testkey_name = "test_key"

    test_config = {testkey_name: testkey_value, "config_path": "Needed to Satisfy the invalid_keys error message"}

    template = {testkey_name: {"type": testkey_datatype}}

    cfg = Config(test_config)

    cv = ConfigValidator()
    cv._check_type_validity(testkey_name, template[testkey_name], cfg)
    assert not bool(cv.invalid_keys) == valid


@pytest.mark.parametrize("path, valid", [("valid_path", True), ("bad_p\0th", False)])
def test_check_path_resolve(path: str, valid: bool) -> None:
    testkey_name = "test_key"

    test_config = {testkey_name: path, "config_path": "Needed to Satisfy the invalid_keys error message"}

    cfg = Config(test_config)

    cv = ConfigValidator()
    cv._check_path_resolve(testkey_name, {"type": "pathlib.Path"}, cfg)
    assert not bool(cv.invalid_keys) == valid


@pytest.mark.parametrize("pattern, test_value, valid", [("a", "a", True), ("a", "b", False)])
def test_check_regex(pattern: str, test_value: str, valid: bool) -> None:
    testkey_name = "test_key"

    test_config = {testkey_name: test_value, "config_path": "Needed to Satisfy the invalid_keys error message"}

    cfg = Config(test_config)

    cv = ConfigValidator()
    cv._check_regex(testkey_name, {"valid": pattern}, cfg)
    assert not bool(cv.invalid_keys) == valid


@pytest.mark.parametrize(
    "minimum, maximum, test_value, valid",
    [
        (-1, 1, -1, True),
        (-1, 1, 1, True),
        (-1, 1, -2, False),
        (-1, 1, 2, False),
        (-1.5, 1.5, -1.5, True),
        (-1.5, 1.5, 1.5, True),
        (-1.5, 1.5, -1.51, False),
        (-1.5, 1.5, 1.51, False),
    ],
)
def test_check_range(
    minimum: Union[int, float], maximum: Union[int, float], test_value: Union[int, float], valid: bool
) -> None:
    testkey_name = "test_key"

    test_config = {testkey_name: test_value, "config_path": "Needed to Satisfy the invalid_keys error message"}

    cfg = Config(test_config)

    cv = ConfigValidator()
    cv._check_range(testkey_name, {"valid": {"min": minimum, "max": maximum}}, cfg)
    assert not bool(cv.invalid_keys) == valid


@pytest.mark.parametrize("test_dict, serializable", [("{}", True), ("df=df", False)])
def test_get_template(tmp_path: path.local, test_dict: str, serializable: bool) -> None:
    test_cfg = tmp_path / "test_template.json"
    with open(test_cfg, "w") as f:
        f.write(test_dict)
    if not serializable:
        with pytest.raises(json.JSONDecodeError):
            ConfigValidator.get_template(Path(test_cfg))
    else:
        template = ConfigValidator.get_template(Path(test_cfg))
        assert isinstance(template, dict)


def test_validate_items() -> None:
    ...


# def test_check_type_validity_int(tmp_path: tmp_path, testkey_value: Union[int, str, bool], testkey_datatype: str, valid: bool):
#     test_cfg_dir = tmp_path
#     test_templates_dir = test_cfg_dir / "templates"
#     test_templates_dir.mkdir()
#
#     cfg_filename = "test_type_validator.json"
#     cfg_file = test_cfg_dir / cfg_filename
#     cfg_template_file = test_templates_dir / cfg_filename
#
#     testkey_name = "test_key"
#
#     test_config = {
#         testkey_name: testkey_value
#     }
#     with open(cfg_file, "w") as cf:
#         json.dump(test_config, cf)
#
#     template = {
#         testkey_name: {"type": testkey_datatype}
#     }
#     with open(cfg_template_file, "w") as ctf:
#         json.dump(template, ctf)
#
#     BoundConfig.set_config_base_path(test_cfg_dir)
#     bc = BoundConfig(cfg_filename)
