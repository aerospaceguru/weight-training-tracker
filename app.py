from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "training.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            weight REAL NOT NULL,
            reps INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        )
    """)
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        log_id = request.form.get("log_id")
        exercise_id = request.form.get("exercise_id")
        new_exercise = request.form.get("new_exercise", "").strip()
        weight = request.form.get("weight")
        reps = request.form.get("reps")

        if new_exercise:
            c.execute("INSERT OR IGNORE INTO exercises (name) VALUES (?)", (new_exercise,))
            conn.commit()
            c.execute("SELECT id FROM exercises WHERE name = ?", (new_exercise,))
            exercise_id = c.fetchone()["id"]

        if log_id:
            # Update existing entry
            c.execute("""
                UPDATE logs 
                SET exercise_id = ?, weight = ?, reps = ?
                WHERE id = ?
            """, (exercise_id, weight, reps, log_id))
        else:
            # Insert new entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                INSERT INTO logs (exercise_id, weight, reps, timestamp)
                VALUES (?, ?, ?, ?)
            """, (exercise_id, weight, reps, timestamp))
        
        conn.commit()
        conn.close()
        return redirect("/")

    c.execute("SELECT * FROM exercises ORDER BY name")
    exercises = c.fetchall()

    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    c.execute("SELECT COUNT(*) as count FROM logs")
    total_logs = c.fetchone()["count"]
    total_pages = (total_logs + per_page - 1) // per_page

    c.execute("""
        SELECT l.id, l.timestamp, e.name, l.weight, l.reps, l.exercise_id
        FROM logs l
        JOIN exercises e ON l.exercise_id = e.id
        ORDER BY l.timestamp DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    logs = c.fetchall()

    edit_id = request.args.get("edit", type=int)
    edit_log = None
    if edit_id:
        c.execute("""
            SELECT l.id, l.exercise_id, l.weight, l.reps
            FROM logs l
            WHERE l.id = ?
        """, (edit_id,))
        edit_log = c.fetchone()

    conn.close()

    return render_template("index.html", 
                         exercises=exercises, 
                         logs=logs, 
                         edit_log=edit_log,
                         page=page,
                         total_pages=total_pages)

@app.route("/delete/<int:log_id>", methods=["POST"])
def delete_log(log_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5055, debug=False)
