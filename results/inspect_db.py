import sqlite3
import os
import json

db_path = r"backend/instance/crimesense.db"
os.makedirs("results", exist_ok=True)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
table_info = {}
for t in tables:
    name = t[0]
    count = cur.execute(f"SELECT COUNT(*) FROM {name};").fetchone()[0]
    cols = cur.execute(f"PRAGMA table_info({name});").fetchall()
    table_info[name] = {
        "count": count,
        "columns": [col[1] for col in cols]
    }

print("Tables found in backend/instance/crimesense.db:", len(tables))
for t, info in table_info.items():
    print(f"  {t} ({info['count']} rows)")

with open("results/db_audit.json", "w") as f:
    json.dump(table_info, f, indent=2)

conn.close()
