import eventlet

eventlet.monkey_patch()

import subprocess
import re
import threading
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Shared state to manage active processes
# Structure: active_tasks[sid][target] = {'ping': proc, 'traceroute': proc}
active_tasks = {}


def parse_ping(line):
    # Match: 64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=14.5 ms
    match = re.search(r"time=([\d\.]+) ms", line)
    if match:
        return float(match.group(1))
    return None


def run_ping(target, sid):
    print(f"Starting ping for {target} (sid: {sid})")
    process = subprocess.Popen(
        ["ping", "-i", "1", target],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if sid not in active_tasks:
        print(f"SID {sid} not in active_tasks, aborting ping")
        process.terminate()
        return
    if target not in active_tasks[sid]:
        active_tasks[sid][target] = {}
    active_tasks[sid][target]["ping"] = process

    total_sent = 0
    total_received = 0

    for line in iter(process.stdout.readline, ""):
        if sid not in active_tasks or target not in active_tasks[sid]:
            print(f"Task for {target} stopped, terminating process")
            process.terminate()
            break

        if "64 bytes from" in line:
            total_sent += 1
            total_received += 1
            latency = parse_ping(line)
            loss = (
                0
                if total_sent == 0
                else ((total_sent - total_received) / total_sent) * 100
            )
            print(f"Ping result for {target}: {latency}ms")
            socketio.emit(
                "ping_result",
                {
                    "target": target,
                    "latency": latency,
                    "loss": round(loss, 2),
                    "total_sent": total_sent,
                    "total_received": total_received,
                    "raw": line.strip(),
                },
                room=sid,
            )
        elif (
            "Request timeout" in line
            or "no answer" in line
            or "timeout" in line.lower()
        ):
            total_sent += 1
            loss = ((total_sent - total_received) / total_sent) * 100
            print(f"Ping timeout for {target}")
            socketio.emit(
                "ping_result",
                {
                    "target": target,
                    "latency": None,
                    "loss": round(loss, 2),
                    "total_sent": total_sent,
                    "total_received": total_received,
                    "raw": "Request timeout",
                },
                room=sid,
            )

    process.wait()
    print(f"Ping process for {target} finished")


def run_traceroute(target, sid):
    print(f"Starting traceroute for {target}")
    process = subprocess.Popen(
        ["tracepath", "-n", "-m", "30", target],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if sid not in active_tasks:
        process.terminate()
        return
    if target not in active_tasks[sid]:
        active_tasks[sid][target] = {}
    active_tasks[sid][target]["traceroute"] = process

    for line in iter(process.stdout.readline, ""):
        if sid not in active_tasks or target not in active_tasks[sid]:
            process.terminate()
            break

        socketio.emit(
            "traceroute_result", {"target": target, "raw": line.strip()}, room=sid
        )

    process.wait()
    print(f"Traceroute for {target} finished")


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("start_test")
def handle_start_test(data):
    target = data.get("target")
    if not target:
        return

    sid = request.sid
    if sid not in active_tasks:
        active_tasks[sid] = {}

    # If already running for this target, stop it first to restart
    stop_target_tasks(sid, target)
    active_tasks[sid][target] = {}

    eventlet.spawn(run_ping, target, sid)
    eventlet.spawn(run_traceroute, target, sid)


@socketio.on("stop_test")
def handle_stop_test(data):
    target = data.get("target")
    if target:
        stop_target_tasks(request.sid, target)


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    if sid in active_tasks:
        for target in list(active_tasks[sid].keys()):
            stop_target_tasks(sid, target)
        del active_tasks[sid]


def stop_target_tasks(sid, target):
    if sid in active_tasks and target in active_tasks[sid]:
        tasks = active_tasks[sid].pop(target)
        for task_name, process in tasks.items():
            try:
                process.terminate()
            except:
                pass


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
