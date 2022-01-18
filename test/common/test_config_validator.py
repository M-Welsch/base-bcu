import json
from pathlib import Path
from tempfile import SpooledTemporaryFile
from time import sleep
from typing import Optional, Union

import pytest
from _pytest.tmpdir import tmp_path
from py import path
from pytest_mock import MockFixture

import base.common.config_validator
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


def test_validate_items(mocker: MockFixture) -> None:
    mocked_validate_item = mocker.patch("base.common.config_validator.ConfigValidator._validate_item")
    template = {"a": 1, "b": 2}
    ConfigValidator()._validate_items(template, config=Config({}))
    assert mocked_validate_item.call_count == len(template)


@pytest.mark.parametrize("datatype", ["str", "pathlib.Path", "int", "float", "bool"])
def test_validate_item(mocker: MockFixture, datatype: str) -> None:
    mocked_check_required = mocker.patch(
        "base.common.config_validator.ConfigValidator._check_validation_required", return_value=True
    )
    mocked_check_type_validity = mocker.patch("base.common.config_validator.ConfigValidator._check_type_validity")
    mocked_check_regex = mocker.patch("base.common.config_validator.ConfigValidator._check_regex")
    mocked_check_range = mocker.patch("base.common.config_validator.ConfigValidator._check_range")
    mocked_check_path_resolve = mocker.patch("base.common.config_validator.ConfigValidator._check_path_resolve")
    config = Config({})
    cv = ConfigValidator()
    template_key = "any key"
    template_data = {"type": datatype}
    cv._validate_item(config=config, template_key=template_key, template_data=template_data)
    assert mocked_check_required.called_once_with(config, template_key, template_data)
    if "_check_type_validity" in cv.validation_pipeline_map[datatype]:
        assert mocked_check_type_validity.called_once_with(template_key, template_data, config)
    if "_check_regex" in cv.validation_pipeline_map[datatype]:
        assert mocked_check_regex.called_once_with(template_key, template_data, config)
    if "_check_range" in cv.validation_pipeline_map[datatype]:
        assert mocked_check_range.called_once_with(template_key, template_data, config)
    if "_check_path_resolve" in cv.validation_pipeline_map[datatype]:
        assert mocked_check_path_resolve.called_once_with(template_key, template_data, config)


@pytest.mark.parametrize(
    "key_available, optional, validation_required, invalid_keys_entry",
    [
        (True, True, True, False),  # if available, but optional => check anyway, no entry in invalid_keys
        (False, True, False, False),  # if UNavailable and optional => skip further checking, no entry in invalid_keys
        (
            False,
            False,
            False,
            True,
        ),  # if UNavailable, but NOT optional => skip further checking, but leave enty in invalid_keys
    ],
)
def test_check_validation_required(
    mocker: MockFixture, key_available: bool, optional: bool, validation_required: bool, invalid_keys_entry: bool
) -> None:
    mocked_check_optional = mocker.patch(
        "base.common.config_validator.ConfigValidator._check_optional", return_value=optional
    )
    mocked_check_key_avaliable = mocker.patch(
        "base.common.config_validator.ConfigValidator._check_key_available", return_value=key_available
    )
    config = Config({"unimportant_content": 0, "config_path": "Needed to Satisfy the invalid_keys error message"})
    cv = ConfigValidator()
    testkey = "any_testkey"
    template_data = {"unimportant_testdata": 0}
    assert (
        cv._check_validation_required(config=config, template_key=testkey, template_data={"unimportant_testdata": 0})
        == validation_required
    )
    assert mocked_check_optional.called_once_with(template_data)
    assert mocked_check_key_avaliable.called_once_with(config, testkey)
    assert bool(cv.invalid_keys) == invalid_keys_entry


@pytest.mark.parametrize(
    "template_data, optional", [({"optional": True}, True), ({"optional": False}, False), ({}, False)]
)
def test_check_optional(template_data: dict, optional: bool) -> None:
    assert ConfigValidator._check_optional(template_data) == optional


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
