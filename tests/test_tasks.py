import pytest
import io
from app import run_ping, active_tasks, run_hop_analysis
import database


def test_run_ping_logic(mocker):
    target = "8.8.8.8"
    sid = "test_sid"
    active_tasks[sid] = {target: {}}

    # Mock database
    mocker.patch("database.get_or_create_target", return_value=1)
    mock_save = mocker.patch("database.save_ping")

    # Mock socketio.emit
    mock_emit = mocker.patch("app.socketio.emit")

    # Mock subprocess.Popen
    mock_process = mocker.Mock()
    # Simulate one successful ping and then termination
    mock_process.stdout.readline.side_effect = [
        "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=14.5 ms",
        "",  # End of stream
    ]
    mocker.patch("subprocess.Popen", return_value=mock_process)

    run_ping(target, sid)

    assert mock_save.called
    assert mock_emit.called
    assert active_tasks[sid][target]["ping"] == mock_process


def test_run_ping_timeout(mocker):
    target = "8.8.8.8"
    sid = "test_sid"
    active_tasks[sid] = {target: {}}

    mocker.patch("database.get_or_create_target", return_value=1)
    mock_save = mocker.patch("database.save_ping")
    mock_emit = mocker.patch("app.socketio.emit")

    mock_process = mocker.Mock()
    mock_process.stdout.readline.side_effect = ["Request timeout for icmp_seq 1", ""]
    mocker.patch("subprocess.Popen", return_value=mock_process)

    run_ping(target, sid)

    assert mock_save.called
    # Check that latency was None (first arg of save_ping is target_id=1, second is latency)
    args, _ = mock_save.call_args
    assert args[1] is None


def test_run_hop_analysis_logic(mocker):
    target = "8.8.8.8"
    sid = "test_sid"
    active_tasks[sid] = {target: {}}

    mocker.patch("database.get_or_create_target", return_value=1)
    mock_save_hop = mocker.patch("database.save_hop")
    mock_emit = mocker.patch("app.socketio.emit")
    mocker.patch("eventlet.sleep")  # Don't actually sleep

    # Mock tracepath process
    mock_tracepath = mocker.Mock()
    mock_tracepath.stdout.readline.side_effect = [" 1: 192.168.1.1", ""]
    mocker.patch("subprocess.Popen", return_value=mock_tracepath)

    # Mock ping process for the hop
    mock_ping_result = mocker.Mock()
    mock_ping_result.stdout = (
        "64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=1.23 ms"
    )

    # Use a side effect to stop the loop after one iteration
    def run_side_effect(*args, **kwargs):
        if sid in active_tasks:
            del active_tasks[sid]
        return mock_ping_result

    mocker.patch("subprocess.run", side_effect=run_side_effect)

    run_hop_analysis(target, sid)

    assert mock_save_hop.called
    assert mock_emit.called


def test_run_ping_aborted(mocker):
    # Test case where sid is removed before ping starts
    target = "8.8.8.8"
    sid = "test_sid"
    # active_tasks[sid] is NOT present

    mocker.patch("database.get_or_create_target", return_value=1)
    mock_process = mocker.Mock()
    mocker.patch("subprocess.Popen", return_value=mock_process)

    run_ping(target, sid)
    assert mock_process.terminate.called


def test_run_ping_stop_midway(mocker):
    target = "8.8.8.8"
    sid = "test_sid"
    active_tasks[sid] = {target: {}}

    mocker.patch("database.get_or_create_target", return_value=1)
    mock_process = mocker.Mock()

    # We want the loop to run twice.
    # 1st call: returns a line, loop body runs, sid is present.
    # 2nd call: returns a line, loop body runs, sid is GONE.

    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 2:
            if sid in active_tasks:
                del active_tasks[sid]
            return "some line"
        if call_count[0] == 1:
            return "64 bytes from 8.8.8.8: time=10ms"
        return ""

    mock_process.stdout.readline.side_effect = side_effect
    mocker.patch("subprocess.Popen", return_value=mock_process)
    mocker.patch("database.save_ping")
    mocker.patch("app.socketio.emit")

    run_ping(target, sid)
    assert mock_process.terminate.called


def test_run_hop_analysis_stop_tracepath(mocker):
    target = "8.8.8.8"
    sid = "test_sid"
    active_tasks[sid] = {target: {}}

    mocker.patch("database.get_or_create_target", return_value=1)
    mock_tracepath = mocker.Mock()

    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            del active_tasks[sid]
        return " 1: 192.168.1.1"

    mock_tracepath.stdout.readline.side_effect = side_effect
    mocker.patch("subprocess.Popen", return_value=mock_tracepath)

    run_hop_analysis(target, sid)
    assert mock_tracepath.terminate.called


def test_stop_target_tasks_exception(mocker):
    from app import stop_target_tasks

    sid = "test_sid"
    target = "test_target"
    mock_proc = mocker.Mock()
    mock_proc.terminate.side_effect = Exception("error")

    active_tasks[sid] = {target: {"ping": mock_proc}}

    # Should not raise exception
    stop_target_tasks(sid, target)
    assert mock_proc.terminate.called
    assert target not in active_tasks[sid]


def test_run_ping_init_target_dict(mocker):
    # Test line 47: if target not in active_tasks[sid]: active_tasks[sid][target] = {}
    target = "8.8.8.8"
    sid = "test_sid"
    active_tasks[sid] = {}  # sid exists but target dict doesn't

    mocker.patch("database.get_or_create_target", return_value=1)
    mock_process = mocker.Mock()
    mock_process.stdout.readline.return_value = ""
    mocker.patch("subprocess.Popen", return_value=mock_process)

    run_ping(target, sid)
    assert target in active_tasks[sid]
    assert "ping" in active_tasks[sid][target]
