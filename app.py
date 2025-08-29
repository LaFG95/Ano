from flask import Flask, render_template, request, redirect
import os
import psycopg2
import random

app = Flask(__name__)

# ----------------- вспомогательные функции -----------------
def generate_username():
    """Генерируем случайный анонимный ник."""
    return "Anon" + str(random.randint(1000, 9999))

def get_conn():
    """Возвращает соединение с PostgreSQL из переменной окружения DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL не задана")
    return psycopg2.connect(db_url)

def init_db():
    """Создание таблиц, если ещё не существуют."""
    conn = get_conn()
    c = conn.cursor()
    
    # Таблица вопросов
    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            username TEXT NOT NULL
        )
    """)
    
    # Таблица комментариев
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            username TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# ----------------- маршруты -----------------
@app.route("/")
def home():
    """Главная страница со списком вопросов."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, text, username FROM questions ORDER BY id DESC")
    questions = c.fetchall()
    conn.close()
    return render_template("home.html", questions=questions, is_admin=False)

@app.route("/ask")
def ask():
    """Страница формы для нового вопроса."""
    return render_template("ask.html")

@app.route("/submit", methods=["POST"])
def submit():
    """Обработка отправки вопроса."""
    question = request.form.get("question")
    if question:
        username = generate_username()
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO questions (text, username) VALUES (%s, %s)", (question, username))
        conn.commit()
        conn.close()
        return render_template("thank_you.html", username=username)
    return "Ошибка: вопрос не введён."

@app.route("/question/<int:qid>")
def question_page(qid):
    """Страница с конкретным вопросом и комментариями."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, text, username FROM questions WHERE id=%s", (qid,))
    question = c.fetchone()
    c.execute("SELECT id, text, username FROM comments WHERE question_id=%s ORDER BY id ASC", (qid,))
    comments = c.fetchall()
    conn.close()
    return render_template("question.html", question=question, comments=comments)

@app.route("/comment/<int:qid>", methods=["POST"])
def add_comment(qid):
    """Добавление комментария к вопросу."""
    comment_text = request.form.get("comment")
    if comment_text:
        username = generate_username()
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO comments (question_id, text, username) VALUES (%s, %s, %s)",
            (qid, comment_text, username)
        )
        conn.commit()
        conn.close()
    return redirect(f"/question/{qid}")

# ----------------- запуск -----------------
if __name__ == "__main__":
    init_db()  # создаём таблицы при старте
    app.run(debug=True)
