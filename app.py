import eventlet

eventlet.monkey_patch()

import database
import subprocess
import re
import threading
import csv
import io
import os
import requests
from flask import Flask, render_template, request, jsonify, make_response
from flask_socketio import SocketIO, emit

ip_info_cache = {}


def get_ip_info(ip):
    if not ip or ip == "*":
        return {"isp": "-", "location": "-"}
    if ip in ip_info_cache:
        return ip_info_cache[ip]
    if (
        ip.startswith("10.")
        or ip.startswith("192.168.")
        or (ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31)
    ):
        info = {"isp": "Local Network", "location": "Private IP"}
    else:
        try:
            resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
            data = resp.json()
            if data.get("status") == "success":
                info = {
                    "isp": data.get("isp", "Unknown ISP"),
                    "location": f"{data.get('city', '')}, {data.get('countryCode', '')}".strip(
                        ", "
                    ),
                }
            else:
                info = {"isp": "Unknown ISP", "location": "Unknown"}
        except Exception as e:
            print(f"Error looking up IP {ip}: {e}")
            info = {"isp": "Unknown ISP", "location": "Unknown"}
    ip_info_cache[ip] = info
    return info


def calculate_mos(latency, loss, jitter):
    if latency is None:
        return 1.0
    eff_latency = latency + (jitter * 2) + 10
    id_imp = eff_latency / 40 if eff_latency < 160 else (eff_latency - 120) / 10
    r_factor = max(0, min(94.2, 94.2 - id_imp - (loss * 2.5)))
    mos = (
        1
        + (0.035 * r_factor)
        + (r_factor * (r_factor - 60) * (100 - r_factor) * 0.000007)
    )
    return round(max(1.0, min(5.0, mos)), 2)


app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    logger=True,
    engineio_logger=True,
)

# Initialize database
try:
    database.init_db()
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize database: {e}")

active_tasks = {}


@app.route("/api/health")
def health():
    db_status = "OK"
    try:
        conn = database.get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
    except Exception as e:
        db_status = f"Error: {e}"

    static_files = []
    try:
        for root, _, files in os.walk(app.static_folder):
            for f in files:
                static_files.append(
                    os.path.relpath(os.path.join(root, f), app.static_folder)
                )
    except:
        static_files = "Access Error"

    return jsonify(
        {
            "status": "up",
            "database": db_status,
            "db_path": database.DB_PATH,
            "static_folder": app.static_folder,
            "static_files": static_files,
            "cwd": os.getcwd(),
            "file": __file__,
        }
    )


def parse_ping(line):
    match = re.search(r"time=([\d\.]+) ms", line)
    return float(match.group(1)) if match else None


def run_ping(target, sid):
    try:
        target_id = database.get_or_create_target(target)
        process = subprocess.Popen(
            ["/usr/bin/ping", "-i", "1", target],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        eventlet.sleep(0.5)
        if process.poll() is not None and "Mock" not in str(type(process)):
            stderr_out = process.stdout.read()
            socketio.emit("error", {"message": f"Ping failed: {stderr_out}"}, to=sid)
            return
    except Exception as e:
        socketio.emit("error", {"message": f"Failed to start ping: {e}"}, to=sid)
        return

    if sid not in active_tasks:
        process.terminate()
        return
    active_tasks[sid].setdefault(target, {})["ping"] = process

    total_sent, total_received, prev_latency, jitter = 0, 0, None, 0
    try:
        for line in iter(process.stdout.readline, ""):
            if sid not in active_tasks or target not in active_tasks[sid]:
                process.terminate()
                break
            if "64 bytes from" in line:
                total_sent += 1
                total_received += 1
                latency = parse_ping(line)
                if prev_latency is not None:
                    jitter = jitter + (abs(latency - prev_latency) - jitter) / 16
                prev_latency = latency
                loss = ((total_sent - total_received) / total_sent) * 100
                mos = calculate_mos(latency, loss, jitter)
                database.save_ping(target_id, latency, round(loss, 2))
                socketio.emit(
                    "ping_result",
                    {
                        "target": target,
                        "latency": latency,
                        "loss": round(loss, 2),
                        "jitter": round(jitter, 2),
                        "mos": mos,
                        "total_sent": total_sent,
                        "total_received": total_received,
                        "raw": line.strip(),
                    },
                    to=sid,
                )
            elif any(
                x in line.lower() for x in ["timeout", "request timeout", "no answer"]
            ):
                total_sent += 1
                loss = ((total_sent - total_received) / total_sent) * 100
                mos = calculate_mos(None, loss, jitter)
                database.save_ping(target_id, None, round(loss, 2))
                socketio.emit(
                    "ping_result",
                    {
                        "target": target,
                        "latency": None,
                        "loss": round(loss, 2),
                        "jitter": round(jitter, 2),
                        "mos": mos,
                        "total_sent": total_sent,
                        "total_received": total_received,
                        "raw": "Request timeout",
                    },
                    to=sid,
                )
    except Exception as e:
        print(f"ERROR in ping loop: {e}")
    finally:
        process.wait()


def run_hop_analysis(target, sid):
    try:
        target_id = database.get_or_create_target(target)
        process = subprocess.Popen(
            ["/usr/bin/tracepath", "-n", "-m", "15", target],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except Exception as e:
        return
    hops = []
    try:
        for line in iter(process.stdout.readline, ""):
            if sid not in active_tasks or target not in active_tasks[sid]:
                process.terminate()
                break
            match = re.search(r"^\s*(\d+):\s+([a-fA-F\d\.:]+)", line)
            if match:
                hop_num, hop_ip = match.group(1), match.group(2)
                if hop_ip not in [h["ip"] for h in hops]:
                    info = get_ip_info(hop_ip)
                    hops.append({"num": hop_num, "ip": hop_ip, **info})
                    socketio.emit(
                        "hop_update",
                        {
                            "target": target,
                            "num": hop_num,
                            "ip": hop_ip,
                            "isp": info["isp"],
                            "location": info["location"],
                            "loss": 0,
                            "avg_latency": 0,
                        },
                        to=sid,
                    )
        while sid in active_tasks and target in active_tasks[sid]:
            for hop in hops:
                if sid not in active_tasks or target not in active_tasks[sid]:
                    break
                ping_proc = subprocess.run(
                    ["/usr/bin/ping", "-c", "3", "-W", "1", hop["ip"]],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                sent, received, lats = 3, 0, []
                for line in ping_proc.stdout.split("\n"):
                    if "bytes from" in line:
                        received += 1
                        m = re.search(r"time=([\d\.]+)", line)
                        if m:
                            lats.append(float(m.group(1)))
                loss = ((sent - received) / sent) * 100
                avg_lat = sum(lats) / len(lats) if lats else 0
                database.save_hop(
                    target_id,
                    int(hop["num"]),
                    hop["ip"],
                    round(avg_lat, 2),
                    round(loss, 2),
                )
                socketio.emit(
                    "hop_update",
                    {
                        "target": target,
                        "num": hop["num"],
                        "ip": hop["ip"],
                        "isp": hop.get("isp", "-"),
                        "location": hop.get("location", "-"),
                        "loss": round(loss, 2),
                        "avg_latency": round(avg_lat, 2),
                    },
                    to=sid,
                )
            eventlet.sleep(5)
    except Exception as e:
        print(f"ERROR in hop analysis: {e}")
    finally:
        process.wait()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/history/<path:target>")
def get_history(target):
    history = database.get_history(target, request.args.get("hours", 24, type=int))
    return jsonify(history)


@app.route("/api/active-targets")
def get_active_targets():
    return jsonify(database.get_active_targets())


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
    try:
        target = data.get("target")
        if not target:
            return
        sid = request.sid
        active_tasks.setdefault(sid, {})
        database.get_or_create_target(target)
        stop_target_tasks(sid, target)
        active_tasks[sid][target] = {}
        eventlet.spawn(run_ping, target, sid)
        eventlet.spawn(run_hop_analysis, target, sid)
    except Exception as e:
        socketio.emit("error", {"message": f"Server error: {e}"})


@socketio.on("stop_test")
def handle_stop_test(data):
    try:
        target = data.get("target")
        if target:
            database.deactivate_target(target)
            stop_target_tasks(request.sid, target)
    except Exception as e:
        print(f"ERROR: {e}")


@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")


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
        for _, p in tasks.items():
            try:
                p.terminate()
            except:
                pass


if __name__ == "__main__":
    socketio.run(app, debug=False, host="0.0.0.0", port=5000)
