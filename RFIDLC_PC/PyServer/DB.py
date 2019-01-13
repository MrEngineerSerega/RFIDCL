import sqlite3

limit = input("лимит выборки")

conn = sqlite3.connect("Chinook_Sqlite.sqlite")
cursor = conn.cursor()

cursor.execute("SELECT Name FROM Artist ORDER BY Name LIMIT 5")
results = cursor.fetchall()

print(results)

cursor.execute("INSERT INTO Artist VALUES (Null, 'fdgdfgdfg')")
conn.commit()

cursor.execute("SELECT Name FROM Artist ORDER BY Name LIMIT :limit", {"limit": int(limit)})
results = cursor.fetchall()

print(results)

conn.close()
