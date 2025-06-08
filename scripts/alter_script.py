import sqlite3

conn = sqlite3.connect("alertGabs_rain_db")
cursor = conn.cursor()

# Add new column for rain_streak if it doesn't exist
try:
    cursor.execute("ALTER TABLE weather ADD COLUMN rain_streak INTEGER")
    print("✅ rain_streak column added.")
except sqlite3.OperationalError as e:
    print("ℹ️ Column probably already exists:", e)

conn.commit()
conn.close()