#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('instance/cfpa_zms.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM recipes')
count = cursor.fetchone()[0]
print(f'Total recipes: {count}')

if count > 0:
    cursor.execute('SELECT id, name FROM recipes LIMIT 3')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]}')
else:
    print('No recipes found in database')

conn.close()