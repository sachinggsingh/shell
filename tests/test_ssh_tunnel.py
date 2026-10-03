from dev_shell.monitoring.ssh_tunnel import SSHTunnel
from dev_shell.utils.ports import find_free_local_port


def test_ssh_command_construction():
    tunnel = SSHTunnel(
        host="203.0.113.10",
        username="devshell",
        remote_port=9477,
        identity_file="~/.ssh/id_ed25519",
        ssh_port=2222,
        local_port=19477,
    )
    command = tunnel.build_command()
    assert command[0] == "ssh"
    assert "-N" in command
    assert "-L" in command
    assert "19477:127.0.0.1:9477" in command
    assert "-o" in command
    assert "BatchMode=yes" in command
    assert "ExitOnForwardFailure=yes" in command
    assert "StrictHostKeyChecking=no" not in command
    assert "-p" in command
    assert "2222" in command
    assert "-i" in command
    assert "devshell@203.0.113.10" in command


def test_free_port_allocation():
    port = find_free_local_port()
    assert 1 <= port <= 65535
