from flask import Flask, render_template, request, redirect
import sqlite3
import random

app = Flask(__name__)
DB_NAME = "questions.db"

# ----------------- вспомогательные функции -----------------
def generate_username():
    return "Anon" + str(random.randint(1000, 9999))

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Таблица вопросов
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            username TEXT NOT NULL
        )
    ''')
    # Таблица комментариев
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            username TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    conn.commit()
    conn.close()

# ----------------- маршруты -----------------
@app.route("/")
def home():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, text, username FROM questions ORDER BY id DESC")
    questions = c.fetchall()
    conn.close()

    # проверка, админ ли
    is_admin = request.args.get("admin") == "supersecret"
    return render_template("home.html", questions=questions, is_admin=is_admin)

@app.route("/ask")
def ask():
    return render_template("ask.html")

@app.route("/submit", methods=["POST"])
def submit():
    question = request.form.get("question")
    if question:
        username = generate_username()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO questions (text, username) VALUES (?, ?)", (question, username))
        conn.commit()
        conn.close()
        return render_template("thank_you.html", username=username)
    return "Ошибка: вопрос не введён."

@app.route("/question/<int:qid>")
def question_page(qid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, text, username FROM questions WHERE id=?", (qid,))
    question = c.fetchone()
    # Получаем комментарии с id для удаления
    c.execute("SELECT id, text, username FROM comments WHERE question_id=? ORDER BY id ASC", (qid,))
    comments = c.fetchall()
    conn.close()
    is_admin = request.args.get("admin") == "supersecret"
    return render_template("question.html", question=question, comments=comments, is_admin=is_admin)

@app.route("/comment/<int:qid>", methods=["POST"])
def add_comment(qid):
    comment_text = request.form.get("comment")
    if comment_text:
        username = generate_username()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO comments (question_id, text, username) VALUES (?, ?, ?)", 
                  (qid, comment_text, username))
        conn.commit()
        conn.close()
    return redirect(f"/question/{qid}")

# ----------------- админка -----------------
@app.route("/delete/<int:qid>")
def delete_question(qid):
    if request.args.get("admin") != "supersecret":
        return "Нет доступа", 403
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE id=?", (qid,))
    c.execute("DELETE FROM comments WHERE question_id=?", (qid,))
    conn.commit()
    conn.close()
    return redirect("/?admin=supersecret")

@app.route("/delete_comment/<int:cid>")
def delete_comment(cid):
    if request.args.get("admin") != "supersecret":
        return "Нет доступа", 403
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT question_id FROM comments WHERE id=?", (cid,))
    qid = c.fetchone()
    if qid:
        qid = qid[0]
        c.execute("DELETE FROM comments WHERE id=?", (cid,))
        conn.commit()
    conn.close()
    return redirect(f"/question/{qid}?admin=supersecret")

# ----------------- запуск -----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
