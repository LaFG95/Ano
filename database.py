import sqlite3

conn = sqlite3.connect("questions.db")
c = conn.cursor()

# создаём таблицу, если её нет
c.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL
)
""")

conn.commit()
conn.close()
print("База данных и таблица созданы!")
