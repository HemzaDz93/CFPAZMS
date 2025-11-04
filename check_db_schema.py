#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('instance/cfpa_zms.db')
cursor = conn.cursor()

# Get all tables
print("=== All tables in database ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  {table[0]}")

# Check if meal_records exists
print("\n=== Checking meal_records table ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meal_records'")
result = cursor.fetchone()
if result:
    print("  meal_records table EXISTS")
    cursor.execute("PRAGMA table_info(meal_records)")
    cols = cursor.fetchall()
    for col in cols:
        print(f"    {col[1]} ({col[2]})")
else:
    print("  meal_records table DOES NOT EXIST")

conn.close()