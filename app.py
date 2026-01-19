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
active_tasks = {}


def parse_ping(line):
    # Match: 64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=14.5 ms
    match = re.search(r"time=([\d\.]+) ms", line)
    if match:
        return float(match.group(1))
    return None


def run_ping(target, sid):
    # Linux ping: -i interval (seconds)
    process = subprocess.Popen(
        ["ping", "-i", "1", target],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if sid not in active_tasks:
        active_tasks[sid] = {}
    active_tasks[sid]["ping"] = process

    total_sent = 0
    total_received = 0

    for line in iter(process.stdout.readline, ""):
        if sid not in active_tasks:
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
            socketio.emit(
                "ping_result",
                {
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
            socketio.emit(
                "ping_result",
                {
                    "latency": None,
                    "loss": round(loss, 2),
                    "total_sent": total_sent,
                    "total_received": total_received,
                    "raw": "Request timeout",
                },
                room=sid,
            )
        elif "packets transmitted" in line:
            # Stats line at the end, but we are running continuously
            pass

    process.wait()


def run_traceroute(target, sid):
    # Using tracepath command as traceroute is not available
    process = subprocess.Popen(
        ["tracepath", "-n", "-m", "30", target],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if sid not in active_tasks:
        active_tasks[sid] = {}
    active_tasks[sid]["traceroute"] = process

    for line in iter(process.stdout.readline, ""):
        if sid not in active_tasks:
            process.terminate()
            break

        socketio.emit("traceroute_result", {"raw": line.strip()}, room=sid)

    process.wait()


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("start_test")
def handle_start_test(data):
    target = data.get("target")
    if not target:
        return

    sid = request.sid
    # Stop existing tests for this session if any
    stop_sid_tasks(sid)
    active_tasks[sid] = {}

    eventlet.spawn(run_ping, target, sid)
    eventlet.spawn(run_traceroute, target, sid)


@socketio.on("disconnect")
def handle_disconnect():
    stop_sid_tasks(request.sid)


def stop_sid_tasks(sid):
    if sid in active_tasks:
        tasks = active_tasks[sid]
        for task_name in list(tasks.keys()):
            process = tasks.pop(task_name)
            try:
                process.terminate()
            except:
                pass
        del active_tasks[sid]


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
