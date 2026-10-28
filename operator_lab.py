#!/usr/bin/env python3
"""Operator CLI: beacons, tasking (ATT&CK ID bilan), fayllar, hisobot."""

import sqlite3
import time
import readline
from reporting import coverage_report

def db():
    con = sqlite3.connect("c2lab.db")
    con.row_factory = sqlite3.Row
    return con


def beacons(con):
    for r in con.execute("SELECT * FROM beacons ORDER BY last_seen DESC"):
        print(f"{r['bid']:<24}{r['hostname']:<14}{r['ip']:<15}{r['os'][:18]:<20}{r['last_seen']}")


def add_task(con, bid, cmd, attack_id=""):
    con.execute("INSERT INTO tasks(bid,command,attack_id,created) VALUES(?,?,?,?)",
                (bid, cmd, attack_id, time.strftime("%Y-%m-%d %H:%M:%S")))
    con.commit()
    print(f"[+] Task navbatga qo'shildi (ATT&CK: {attack_id or '-'}).")


def results(con, n=10):
    for r in con.execute("""SELECT id,bid,command,attack_id,result FROM tasks
                            WHERE status='done' ORDER BY id DESC LIMIT ?""", (n,)):
        print(f"\n=== #{r['id']} [{r['bid']}] [{r['attack_id'] or '-'}] {r['command']} ===")
        print(r["result"] or "(bo'sh)")


def pending(con):
    for r in con.execute("SELECT id,bid,command,attack_id,status FROM tasks ORDER BY id DESC LIMIT 15"):
        print(f"{r['id']:<6}{r['bid']:<24}{r['attack_id'] or '-':<10}{r['status']:<7}{r['command']}")


def files(con):
    print(f"{'BID':<24}{'YO\'NALISH':<10}{'FAYL':<30}{'O\'LCHAM':<10}VAQT")
    for r in con.execute("SELECT * FROM files ORDER BY id DESC LIMIT 20"):
        print(f"{r['bid']:<24}{r['direction']:<10}{r['filename']:<30}{r['size']:<10}{r['ts']}")


def main():
    con = db()
    current = None
    print("""C2 Lab Operator
Komandalar: beacons | use <bid> | shell <cmd> [-a Txxxx] | download <fayl> |
upload <fayl> | results | pending | files | coverage | back | quit""")
    while True:
        try:
            line = input(f"c2({current})> " if current else "c2> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        parts = line.split(maxsplit=1)
        c = parts[0]
        if c == "quit":
            break
        elif c == "beacons":
            beacons(con)
        elif c == "pending":
            pending(con)
        elif c == "results":
            results(con)
        elif c == "files":
            files(con)
        elif c == "coverage":
            coverage_report(con)
        elif c == "use" and len(parts) == 2:
            current = parts[1]
        elif c == "back":
            current = None
        elif c in ("shell", "download", "upload") and current and len(parts) == 2:
            aid = ""
            arg = parts[1]
            if " -a " in arg:                       # shell <cmd> -a T1059.003
                arg, aid = arg.rsplit(" -a ", 1)
            default = {"download": "T1005", "upload": "T1105"}.get(c, "")
            add_task(con, current, arg, aid or default)
        else:
            print("Noma'lum komanda / 'use' talab qilinadi.")


if __name__ == "__main__":
    main()
