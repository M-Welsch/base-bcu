from pathlib import Path
from test.utils import patch_multiple_configs
from typing import List, Optional

import pytest
from pytest_mock import MockFixture

import base.logic.backup.synchronisation.rsync_command
from base.logic.backup.synchronisation.rsync_command import RsyncCommand

local_target_location = Path("/local/target")
source_location = Path("/source/")


@pytest.mark.parametrize("dry, dry_command", [(True, True), (False, False), (None, False)])
def test_compose_rsync_command(mocker: MockFixture, dry: Optional[bool], dry_command: bool) -> None:
    patch_multiple_configs(
        class_=RsyncCommand,
        config_content={
            "sync.json": {},
            "nas.json": {},
        },
    )
    rc = RsyncCommand()
    prot_specific = ["protocol", "specific"]
    dry_run = ["dry"]
    mocked_protocol_specific = mocker.patch(
        "base.logic.backup.synchronisation.rsync_command.RsyncCommand._protocol_specific", return_value=prot_specific
    )
    mocked_dry_run = mocker.patch(
        "base.logic.backup.synchronisation.rsync_command.RsyncCommand._dry_run", return_value=dry_run
    )
    source = Path()
    target = Path()
    if dry:
        cmd = rc.compose(source, target, dry)
    else:
        cmd = rc.compose(source, target)
    assert cmd == [*"sudo rsync -avH --outbuf=N --info=progress2".split(), *prot_specific, *dry_run]
    assert mocked_protocol_specific.called_once_with(source, target)
    assert mocked_dry_run.called_once_with(dry_command)


@pytest.mark.parametrize(
    "sync_cfg, nas_cfg, command",
    [
        (
            {"protocol": "smb", "ssh_keyfile_path": ""},
            {"ssh_host": "", "ssh_user": ""},
            [f"{source_location}/", str(local_target_location)],
        ),
        (
            {"protocol": "ssh", "ssh_keyfile_path": "/path/to/keyfile"},
            {"ssh_host": "myhost", "ssh_user": "myuser"},
            ["-e", f"ssh -i /path/to/keyfile", f"myuser@myhost:{source_location}/", f"{local_target_location}"],
        ),
    ],
)
def test_protocol_specific(sync_cfg: dict, nas_cfg: dict, command: List[str]) -> None:
    patch_multiple_configs(
        class_=RsyncCommand,
        config_content={
            "sync.json": sync_cfg,
            "nas.json": nas_cfg,
        },
    )
    rc = RsyncCommand()

    cmd = rc._protocol_specific(local_target_location, source_location)
    assert isinstance(cmd, list)
    assert cmd == command


@pytest.mark.parametrize("dry, command", [(True, ["--dry-run"]), (False, [""])])
def test_dry_run(dry: bool, command: List[str]) -> None:
    assert RsyncCommand._dry_run(dry) == command
