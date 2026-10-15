"""Tests for the autopilot: agent triggering, config, lifecycle."""

import asyncio
import sys

import pytest

from remarkable_mcp.workflows.live import autopilot


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Never read or write the real ~/.local/state from tests."""
    monkeypatch.setenv("REMARKABLE_WORKFLOW_STATE", str(tmp_path))


ATT = {
    "attention": [
        {
            "kind": "review",
            "id": "example-article",
            "title": "A Sample Project Guide · v1",
            "status": "annotated",
        },
        {"kind": "form", "id": "q1", "title": "Question: Ship it?", "status": "annotated"},
        {"kind": "inbox", "id": "default", "title": "Agent Inbox", "status": "annotated"},
    ],
    "waiting": 2,
}
QUIET = {"attention": [], "waiting": 3}


def test_without_an_agent_the_daemon_exits(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("REMARKABLE_AUTOPILOT_CONFIG", str(tmp_path / "none.json"))

    def must_not_run(self):
        raise AssertionError("the watcher must not start without an agent")

    monkeypatch.setattr(autopilot.Autopilot, "run", must_not_run)
    with caplog.at_level("INFO", logger="remarkable_autopilot"):
        autopilot.main([])
    assert "nothing to do" in caplog.text


def test_agent_runs_once_per_state(tmp_path, monkeypatch):
    monkeypatch.setenv("REMARKABLE_WORKFLOW_STATE", str(tmp_path))
    marker = tmp_path / "ran.txt"
    cfg = {
        **autopilot.DEFAULTS,
        "agent_command": [
            sys.executable,
            "-c",
            f"open({str(marker)!r}, 'a').write('x')",
            "{prompt}",
        ],
        "min_agent_interval_seconds": 0,
    }
    pilot = autopilot.Autopilot(cfg)
    assert asyncio.run(pilot.maybe_run_agent(ATT)) == 0
    assert asyncio.run(pilot.maybe_run_agent(ATT)) is None  # same state: not again
    assert asyncio.run(pilot.maybe_run_agent(QUIET)) is None  # nothing to do
    changed = {"attention": ATT["attention"][:1]}
    assert asyncio.run(pilot.maybe_run_agent(changed)) == 0
    assert marker.read_text() == "xx"
    assert "agent run" in (tmp_path / "autopilot.log").read_text()


def test_agent_off_by_default():
    pilot = autopilot.Autopilot(dict(autopilot.DEFAULTS))
    assert pilot.agent_argv() is None
    assert asyncio.run(pilot.maybe_run_agent(ATT)) is None


def test_prompt_is_substituted():
    pilot = autopilot.Autopilot(
        {**autopilot.DEFAULTS, "agent_command": ["claude", "-p", "{prompt}"]}
    )
    argv = pilot.agent_argv()
    assert argv[:2] == ["claude", "-p"] and "remarkable_whats_new" in argv[2]


def test_missing_agent_command_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.setenv("REMARKABLE_WORKFLOW_STATE", str(tmp_path))
    cfg = {
        **autopilot.DEFAULTS,
        "agent_command": ["/nonexistent/claude", "{prompt}"],
        "min_agent_interval_seconds": 0,
    }
    pilot = autopilot.Autopilot(cfg)
    assert asyncio.run(pilot.maybe_run_agent(ATT)) == -2
    assert pilot.last_agent_signature is None  # not marked handled: retried later
    assert "could not start" in (tmp_path / "autopilot.log").read_text()


def test_hung_agent_is_killed_with_its_children(tmp_path, monkeypatch):
    import os

    monkeypatch.setenv("REMARKABLE_WORKFLOW_STATE", str(tmp_path))
    pidfile = tmp_path / "child.pid"
    script = (
        "import subprocess, sys, time;"
        f"p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']);"
        f"open({str(pidfile)!r}, 'w').write(str(p.pid));"
        "time.sleep(60)"
    )
    cfg = {
        **autopilot.DEFAULTS,
        "agent_command": [sys.executable, "-c", script],
        "agent_timeout_seconds": 1.5,
        "min_agent_interval_seconds": 0,
    }
    pilot = autopilot.Autopilot(cfg)
    assert asyncio.run(pilot.maybe_run_agent(ATT)) == -1
    child = int(pidfile.read_text())
    import time as _t

    for _ in range(50):
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            break
        _t.sleep(0.1)
    else:
        raise AssertionError("grandchild survived the timeout")


def test_check_never_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("REMARKABLE_WORKFLOW_STATE", str(tmp_path))
    pilot = autopilot.Autopilot(dict(autopilot.DEFAULTS))

    async def broken():
        raise RuntimeError("state unreadable")

    monkeypatch.setattr(pilot, "overview", broken)
    assert "_error" in asyncio.run(pilot.check())

    async def fine():
        return ATT

    async def agent_boom(ov):
        raise TimeoutError("agent start timed out")

    monkeypatch.setattr(pilot, "overview", fine)
    monkeypatch.setattr(pilot, "maybe_run_agent", agent_boom)
    assert asyncio.run(pilot.check()) == ATT


def test_unit_file_is_sane():
    from pathlib import Path

    unit = (Path(__file__).parent.parent / "contrib" / "remarkable-autopilot.service").read_text()
    assert "Environment=PATH=%h/.local/bin" in unit
    assert "StartLimitBurst" in unit and "Restart=on-failure" in unit
    assert "@main" not in unit  # pinned, not tracking a branch


def test_sigterm_stops_the_daemon_cleanly(tmp_path):
    """systemd stops the service with SIGTERM: exit 0 and say so, not a crash."""
    import os
    import signal
    import subprocess
    import time

    # The real run loop, with a watcher whose shutdown needs an await (like
    # closing the notification socket) and a check that needs no network.
    script = (
        "import asyncio\n"
        "from remarkable_mcp.workflows.live import autopilot as a, watcher as live\n"
        "class FakeWatcher:\n"
        "    def __init__(self, **kw): self.q = asyncio.Queue()\n"
        "    def subscribe(self): return self.q\n"
        "    async def run(self):\n"
        "        try:\n"
        "            await asyncio.sleep(3600)\n"
        "        finally:\n"
        "            await asyncio.sleep(0.2)\n"
        "            print('watcher closed', flush=True)\n"
        "live.Watcher = FakeWatcher\n"
        "async def check(self):\n"
        "    print('ready', flush=True)\n"
        "a.Autopilot.check = check\n"
        "a.main([])\n"
    )
    cfg = tmp_path / "autopilot.json"
    cfg.write_text('{"agent_command": ["true"]}')  # without an agent it would just exit
    env = dict(os.environ, REMARKABLE_AUTOPILOT_CONFIG=str(cfg))
    proc = subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert proc.stdout.readline().strip() == "ready"
        time.sleep(0.2)
        proc.send_signal(signal.SIGTERM)
        out, err = proc.communicate(timeout=20)
    finally:
        proc.kill()
    assert proc.returncode == 0, err
    assert "autopilot stopped" in err
    assert "Traceback" not in err and "destroyed but it is pending" not in err
    assert "watcher closed" in out


def test_new_ink_in_same_inbox_runs_after_quiet_and_restart(monkeypatch):
    from unittest.mock import AsyncMock, Mock

    cfg = {
        **autopilot.DEFAULTS,
        "agent_command": ["unused"],
        "prompt": "test",
        "min_agent_interval_seconds": 0,
    }
    run = Mock(return_value=0)
    monkeypatch.setattr(autopilot, "_run_agent", run)
    monkeypatch.setattr(autopilot.Autopilot, "overview", AsyncMock(return_value=QUIET))
    first = {
        "attention": [
            {"kind": "inbox", "id": "default", "status": "annotated", "revision": "ink-1"}
        ]
    }
    second = {"attention": [{**first["attention"][0], "revision": "ink-2"}]}
    pilot = autopilot.Autopilot(cfg)
    assert asyncio.run(pilot.maybe_run_agent(first)) == 0
    assert asyncio.run(pilot.maybe_run_agent(QUIET)) is None
    restarted = autopilot.Autopilot(cfg)
    assert asyncio.run(restarted.maybe_run_agent(first)) is None
    assert asyncio.run(restarted.maybe_run_agent(second)) == 0
    assert run.call_count == 2


def test_successful_exit_with_unacknowledged_work_remains_retryable(monkeypatch):
    from unittest.mock import AsyncMock, Mock

    run = Mock(return_value=0)
    monkeypatch.setattr(autopilot, "_run_agent", run)
    monkeypatch.setattr(autopilot.Autopilot, "overview", AsyncMock(return_value=ATT))
    cfg = {
        **autopilot.DEFAULTS,
        "agent_command": ["unused"],
        "prompt": "test",
        "min_agent_interval_seconds": 0,
    }
    pilot = autopilot.Autopilot(cfg)
    assert asyncio.run(pilot.maybe_run_agent(ATT)) == 0
    assert pilot.last_agent_signature is None
    assert asyncio.run(autopilot.Autopilot(cfg).maybe_run_agent(ATT)) == 0
    assert run.call_count == 2


def test_agent_failure_cooldown_survives_restart(monkeypatch):
    from unittest.mock import Mock

    run = Mock(return_value=1)
    monkeypatch.setattr(autopilot, "_run_agent", run)
    cfg = {
        **autopilot.DEFAULTS,
        "agent_command": ["unused"],
        "prompt": "test",
        "min_agent_interval_seconds": 300,
    }
    assert asyncio.run(autopilot.Autopilot(cfg).maybe_run_agent(ATT)) == 1
    assert asyncio.run(autopilot.Autopilot(cfg).maybe_run_agent(ATT)) is None
    assert run.call_count == 1


def test_pending_delivery_does_not_start_agent_and_dry_run_does_not_send(monkeypatch):
    from unittest.mock import AsyncMock, Mock

    from remarkable_mcp.workflows.inbox import delivery

    retry = Mock()
    run = Mock()
    monkeypatch.setattr(delivery, "retry_all", retry)
    monkeypatch.setattr(autopilot, "_run_agent", run)
    ov = {
        "attention": [
            {"kind": "reply", "id": "default", "status": "reply_pending", "revision": "batch"}
        ]
    }
    monkeypatch.setattr(autopilot.Autopilot, "overview", AsyncMock(return_value=ov))
    cfg = {**autopilot.DEFAULTS, "agent_command": ["unused"], "prompt": "test"}
    asyncio.run(autopilot.Autopilot(cfg, dry_run=True).check())
    retry.assert_not_called()
    asyncio.run(autopilot.Autopilot(cfg).check())
    retry.assert_called_once()
    run.assert_not_called()
