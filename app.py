from flask import Flask, render_template, request, redirect
import os
import psycopg2
import random

app = Flask(__name__)

# ----------------- вспомогательные функции -----------------
def generate_username():
    return "Anon" + str(random.randint(1000, 9999))

def get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL не задана")
    return psycopg2.connect(db_url)

def init_db():
    """Создаём таблицы, если их ещё нет."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            username TEXT NOT NULL
        )
    """)
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
    print("✅ Таблицы проверены/созданы.")

# ----------------- маршруты -----------------
@app.route("/")
def home():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, text, username FROM questions ORDER BY id DESC")
    questions = c.fetchall()
    conn.close()
    toast = request.args.get("toast")
    return render_template("home.html", questions=questions, toast=toast)

@app.route("/ask")
def ask():
    return render_template("ask.html")

@app.route("/submit", methods=["POST"])
def submit():
    question = request.form.get("question")
    if question:
        username = generate_username()
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO questions (text, username) VALUES (%s, %s)", (question, username))
        conn.commit()
        conn.close()
        return redirect("/?toast=Вопрос+добавлен!")
    return "Ошибка: вопрос не введён."

@app.route("/question/<int:qid>")
def question_page(qid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, text, username FROM questions WHERE id=%s", (qid,))
    question = c.fetchone()
    c.execute("SELECT id, text, username FROM comments WHERE question_id=%s ORDER BY id ASC", (qid,))
    comments = c.fetchall()
    conn.close()
    toast = request.args.get("toast")
    return render_template("question.html", question=question, comments=comments, toast=toast)

@app.route("/comment/<int:qid>", methods=["POST"])
def add_comment(qid):
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
    return redirect(f"/question/{qid}?toast=Комментарий+добавлен!")

# ----------------- запуск -----------------
if __name__ == "__main__":
    init_db()  # авто-создание таблиц при старте
    app.run(host="0.0.0.0", port=5000)
else:
    # Если запущено через gunicorn на Render
    init_db()
