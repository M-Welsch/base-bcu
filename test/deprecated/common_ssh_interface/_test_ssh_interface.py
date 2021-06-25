import os
import sys

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path_to_module)

from base.common.ssh_interface import SSHInterface


def test_nasfinder_with_cm(command):
    global sshi, response
    with SSHInterface() as sshi:
        if sshi.connect("192.168.0.100", "root") == "Established":
            response_stdout, response_stderr = sshi.run(command)
            print_result_to_console(response_stderr, response_stdout)


def print_result_to_console(response_stderr, response_stdout):
    if response_stdout:
        print("STDOUT:")
        print(response_stdout)
    if response_stderr:
        print("STDERR")
        print(response_stderr)


def test_nasfinder_without_cm(command):
    global sshi, response
    sshi = SSHInterface()
    if sshi.connect("192.168.0.100", "root") == "Established":
        response_stdout, response_stderr = sshi.run(command)
        print_result_to_console(response_stderr, response_stdout)


if __name__ == "__main__":
    cm = True
    correct_command = "ls -a"
    incorrect_command = "ls- a"
    print(f"Testing correctly written command {correct_command}")
    if cm:
        test_nasfinder_with_cm(correct_command)
    else:
        test_nasfinder_without_cm(correct_command)
    print(f"Testing incorrectly written command {incorrect_command}")
    if cm:
        test_nasfinder_with_cm(incorrect_command)
    else:
        test_nasfinder_without_cm(incorrect_command)
