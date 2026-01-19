import eventlet

eventlet.monkey_patch()

import subprocess
import re
import threading
import csv
import io
from flask import Flask, render_template, request, jsonify, make_response
from flask_socketio import SocketIO, emit
import database

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Initialize database
database.init_db()

# Shared state to manage active processes
active_tasks = {}


def parse_ping(line):
    # Match: 64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=14.5 ms
    match = re.search(r"time=([\d\.]+) ms", line)
    if match:
        return float(match.group(1))
    return None


def run_ping(target, sid):
    print(f"Starting ping for {target} (sid: {sid})")
    target_id = database.get_or_create_target(target)

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

            # Save to database
            database.save_ping(target_id, latency, round(loss, 2))

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

            # Save to database (None for latency on timeout)
            database.save_ping(target_id, None, round(loss, 2))

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


def run_hop_analysis(target, sid):
    print(f"Starting hop analysis for {target}")
    target_id = database.get_or_create_target(target)

    # We'll use a loop to ping each hop found by tracepath
    # First, get the hops
    hops = []
    process = subprocess.Popen(
        ["tracepath", "-n", "-m", "15", target],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in iter(process.stdout.readline, ""):
        if sid not in active_tasks or target not in active_tasks[sid]:
            process.terminate()
            break

        match = re.search(r"\s+(\d+):\s+([\d\.]+)", line)
        if match:
            hop_num = match.group(1)
            hop_ip = match.group(2)
            if hop_ip not in [h["ip"] for h in hops]:
                hops.append({"num": hop_num, "ip": hop_ip})
                socketio.emit(
                    "hop_update",
                    {
                        "target": target,
                        "num": hop_num,
                        "ip": hop_ip,
                        "loss": 0,
                        "avg_latency": 0,
                    },
                    room=sid,
                )

    # Now continuously monitor identified hops for loss
    while sid in active_tasks and target in active_tasks[sid]:
        for hop in hops:
            if sid not in active_tasks or target not in active_tasks[sid]:
                break

            # Ping this hop specifically
            ping_proc = subprocess.run(
                ["ping", "-c", "3", "-W", "1", hop["ip"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            sent = 3
            received = 0
            latencies = []

            for line in ping_proc.stdout.split("\n"):
                if "bytes from" in line:
                    received += 1
                    l_match = re.search(r"time=([\d\.]+)", line)
                    if l_match:
                        latencies.append(float(l_match.group(1)))

            loss = ((sent - received) / sent) * 100
            avg_lat = sum(latencies) / len(latencies) if latencies else 0

            # Save hop result to database
            database.save_hop(
                target_id, int(hop["num"]), hop["ip"], round(avg_lat, 2), round(loss, 2)
            )

            socketio.emit(
                "hop_update",
                {
                    "target": target,
                    "num": hop["num"],
                    "ip": hop["ip"],
                    "loss": round(loss, 2),
                    "avg_latency": round(avg_lat, 2),
                },
                room=sid,
            )

        eventlet.sleep(2)  # Interval between hop scans


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/history/<path:target>")
def get_history(target):
    hours = request.args.get("hours", 24, type=int)
    history = database.get_history(target, hours)
    return jsonify(history)


@app.route("/api/active-targets")
def get_active_targets():
    targets = database.get_active_targets()
    return jsonify(targets)


@app.route("/api/clear-history/<path:target>", methods=["POST"])
def clear_history(target):
    database.clear_target_history(target)
    return jsonify({"status": "success"})


@app.route("/api/export-csv/<path:target>")
def export_csv(target):
    data = database.get_raw_data(target)
    if not data:
        return "No data found", 404

    si = io.StringIO()
    cw = csv.DictWriter(si, fieldnames=["timestamp", "latency", "loss"])
    cw.writeheader()
    cw.writerows(data)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = (
        f"attachment; filename={target}_network_data.csv"
    )
    output.headers["Content-type"] = "text/csv"
    return output


@socketio.on("start_test")
def handle_start_test(data):
    target = data.get("target")
    if not target:
        return

    sid = request.sid
    if sid not in active_tasks:
        active_tasks[sid] = {}

    # Update database status
    database.get_or_create_target(target)

    # If already running for this target, stop it first to restart
    stop_target_tasks(sid, target)
    active_tasks[sid][target] = {}

    eventlet.spawn(run_ping, target, sid)
    eventlet.spawn(run_hop_analysis, target, sid)


@socketio.on("stop_test")
def handle_stop_test(data):
    target = data.get("target")
    if target:
        database.deactivate_target(target)
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
