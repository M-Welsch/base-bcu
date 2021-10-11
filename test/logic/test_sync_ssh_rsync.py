from subprocess import Popen, PIPE

import pytest
from pathlib import Path

from base.logic.backup.sync import SshRsync


@pytest.fixture
def ssh_rsync():
    ssh_rsync = SshRsync(local_target_location=Path(), source_location=Path())
    stimulus = [
        'echo',
        '-e',
        'Status Line 1\n\nExit'
    ]
    ssh_rsync._process = Popen(stimulus, stdout=PIPE, stderr=PIPE)
    yield ssh_rsync


class TestSshRsync:
    def test_output_generator(self, ssh_rsync: SshRsync):
        for line in ssh_rsync._output_generator():
            ...
