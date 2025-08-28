import sqlite3

conn = sqlite3.connect("questions.db")
c = conn.cursor()

# Таблица вопросов
c.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL
)
""")

# Таблица комментариев
c.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    text TEXT NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(id)
)
""")

conn.commit()
conn.close()
print("База данных создана!")
