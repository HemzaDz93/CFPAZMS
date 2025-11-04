#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('instance/cfpa_zms.db')
cursor = conn.cursor()

# Get sample meal records
print("=== Sample meal_records ===")
cursor.execute("SELECT id, record_date, meal_type, recipe_id, servings, expected_cost FROM meal_records LIMIT 5")
records = cursor.fetchall()
if records:
    for record in records:
        print(f"  {record}")
else:
    print("  No meal records found")

print(f"\n=== Total meal records: ===")
cursor.execute("SELECT COUNT(*) FROM meal_records")
count = cursor.fetchone()
print(f"  {count[0]}")

conn.close()