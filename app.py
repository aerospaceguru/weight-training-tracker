from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime
import csv
import io

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
            c.execute("""
                UPDATE logs 
                SET exercise_id = ?, weight = ?, reps = ?
                WHERE id = ?
            """, (exercise_id, weight, reps, log_id))
        else:
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

    search_query = request.args.get("search", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    
    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    query = """
        SELECT l.id, l.timestamp, e.name, l.weight, l.reps, l.exercise_id
        FROM logs l
        JOIN exercises e ON l.exercise_id = e.id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND e.name LIKE ?"
        params.append(f"%{search_query}%")
    
    if date_from:
        query += " AND date(l.timestamp) >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND date(l.timestamp) <= ?"
        params.append(date_to)

    count_query = query.replace("SELECT l.id, l.timestamp, e.name, l.weight, l.reps, l.exercise_id", "SELECT COUNT(*) as count")
    c.execute(count_query, params)
    total_logs = c.fetchone()["count"]
    total_pages = (total_logs + per_page - 1) // per_page

    query += " ORDER BY l.timestamp DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    c.execute(query, params)
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
                         total_pages=total_pages,
                         search_query=search_query,
                         date_from=date_from,
                         date_to=date_to)

@app.route("/export")
def export_csv():
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT l.timestamp, e.name, l.weight, l.reps
        FROM logs l
        JOIN exercises e ON l.exercise_id = e.id
        ORDER BY l.timestamp DESC
    """)
    logs = c.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date/Time", "Exercise", "Weight (kg)", "Reps"])
    
    for log in logs:
        writer.writerow([log["timestamp"], log["name"], log["weight"], log["reps"]])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'training_log_{datetime.now().strftime("%Y%m%d")}.csv'
    )

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
