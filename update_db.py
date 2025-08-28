import sqlite3

conn = sqlite3.connect("questions.db")
c = conn.cursor()

# Добавляем колонку username в таблицу comments, если её ещё нет
try:
    c.execute("ALTER TABLE comments ADD COLUMN username TEXT DEFAULT 'Аноним'")
    print("Колонка username добавлена.")
except sqlite3.OperationalError:
    print("Колонка username уже существует.")

conn.commit()
conn.close()
