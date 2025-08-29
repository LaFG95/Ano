from flask import Flask, render_template, request, redirect
import psycopg2
import random
import os

app = Flask(__name__)

# Получаем URL базы из переменных окружения Render
DB_URL = os.environ.get("DATABASE_URL")

# ----------------- вспомогательные функции -----------------
def generate_username():
    """Генерируем случайный анонимный ник."""
    return "Anon" + str(random.randint(1000, 9999))

def get_conn():
    """Возвращает соединение с PostgreSQL."""
    return psycopg2.connect(DB_URL)

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

    is_admin = request.args.get("admin") == "supersecret"
    return render_template("home.html", questions=questions, is_admin=is_admin)

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
    is_admin = request.args.get("admin") == "supersecret"
    return render_template("question.html", question=question, comments=comments, is_admin=is_admin)

@app.route("/comment/<int:qid>", methods=["POST"])
def add_comment(qid):
    """Добавление комментария к вопросу."""
    comment_text = request.form.get("comment")
    if comment_text:
        username = generate_username()
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO comments (question_id, text, username) VALUES (%s, %s, %s)", 
                  (qid, comment_text, username))
        conn.commit()
        conn.close()
    return redirect(f"/question/{qid}")

# ----------------- админка -----------------
@app.route("/delete/<int:qid>")
def delete_question(qid):
    """Удаление вопроса и всех его комментариев (только админ)."""
    if request.args.get("admin") != "supersecret":
        return "Нет доступа", 403
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE id=%s", (qid,))
    conn.commit()
    conn.close()
    return redirect("/?admin=supersecret")

@app.route("/delete_comment/<int:cid>")
def delete_comment(cid):
    """Удаление конкретного комментария (только админ)."""
    if request.args.get("admin") != "supersecret":
        return "Нет доступа", 403
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT question_id FROM comments WHERE id=%s", (cid,))
    qid = c.fetchone()
    if qid:
        qid = qid[0]
        c.execute("DELETE FROM comments WHERE id=%s", (cid,))
        conn.commit()
    conn.close()
    return redirect(f"/question/{qid}?admin=supersecret")

# ----------------- запуск -----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
