import sqlite3, time

SCHEMA = """
CREATE TABLE IF NOT EXISTS beacons (
    bid TEXT PRIMARY KEY, hostname TEXT, user TEXT, os TEXT,
    first_seen TEXT, last_seen TEXT, ip TEXT, sleep REAL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, bid TEXT, command TEXT,
    attack_id TEXT DEFAULT '',
    status TEXT DEFAULT 'queued',
    created TEXT, sent TEXT, result TEXT
);
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT, bid TEXT, direction TEXT,
    filename TEXT, size INTEGER, ts TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, bid TEXT, kind TEXT, detail TEXT
);
"""

def db(path="c2lab.db"):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con

def log(con, bid, kind, detail=""):
    con.execute("INSERT INTO events(ts,bid,kind,detail) VALUES(?,?,?,?)",
                (time.strftime("%Y-%m-%d %H:%M:%S"), bid, kind, detail))
    con.commit()
