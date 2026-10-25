import sqlite3

DB_PATH = r"C:\Users\sruth\crime analysis\backend\instance\crimesense.db"
conn = sqlite3.connect(DB_PATH)

total = conn.execute("SELECT COUNT(*) FROM crimes").fetchone()[0]
print(f"Total records: {total}")

by_type = conn.execute("SELECT crime_type, COUNT(*) FROM crimes GROUP BY crime_type").fetchall()
print(f"\nBy crime type:")
for ct, count in by_type:
    print(f"  {ct}: {count}")

print(f"\nBy district:")
for dist, count in by_district:
    print(f"  {dist}: {count}")

print(f"\nTop localities:")
by_district = conn.execute("SELECT district, COUNT(*) FROM crimes GROUP BY district").fetchall()
print(f"\nBy district:")
for dist, count in by_district:
for dist, count by_district:
    print(f"  {dist}: {count}")

by_locality = conn.execute("SELECT locality, COUNT(*) FROM crimes GROUP BY locality ORDER BY COUNT(*) DESC LIMIT 15").fetchall()
print(f"\nTop localities:")
for loc, count in by_locality:
    print(f"  {loc}: {count}")

conn.close()
