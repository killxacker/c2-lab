#!/usr/bin/env python3
"""ATT&CK coverage: qaysi texnikalar emulyatsiya qilingan, MITRE nav bazasiga havola."""

from collections import Counter

# Lab stsenariylarida ishlatiladigan texnikalar qisqacha bazasi
ATTACK_DB = {
    "T1059":   ("Command and Scripting Interpreter", "shell komandalar"),
    "T1005":   ("Data from Local System", "download / fayl o'qish"),
    "T1105":   ("Ingress Tool Transfer", "upload / C2dan fayl keltirish"),
    "T1087":   ("Account Discovery", "whoami, net user"),
    "T1057":   ("Process Discovery", "ps, tasklist"),
    "T1016":   ("System Network Configuration", "ipconfig, ifconfig"),
    "T1082":   ("System Information Discovery", "uname, systeminfo"),
    "T1071.001": ("Application Layer Protocol: Web", "HTTP C2 beacon"),
    "T1027":   ("Obfuscated Files or Information", "Fernet shifrlash"),
    "T1070":   ("Indicator Removal", "log tozalash mashqlari"),
}


def coverage_report(con):
    rows = con.execute("SELECT attack_id, command FROM tasks WHERE attack_id != ''").fetchall()
    used = Counter(r["attack_id"].split(".")[0] for r in rows)
    print("\n=== MITRE ATT&CK COVERAGE ===")
    print(f"{'TEXNIKA':<12}{'NOMI':<42}{'SONI':<6}HOROLA")
    for tid, (name, _) in ATTACK_DB.items():
        cnt = used.get(tid, 0) + sum(v for k, v in used.items() if k.startswith(tid + "."))
        mark = "█" * cnt if cnt else "·"
        print(f"{tid:<12}{name[:40]:<42}{cnt:<6}{mark}")
    print("\nIsm va havolalar: https://attack.mitre.org/techniques/<ID>/")
    done = set(r["attack_id"] for r in rows)
    print(f"Jami noyob texnikalar: {len(done)}")
