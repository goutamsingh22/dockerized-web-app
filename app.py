import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "tasks.db"))
MAX_TITLE_LENGTH = 200

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA busy_timeout=5000")
    return g.db


def init_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DATABASE_PATH)) as db:
        db.execute("PRAGMA busy_timeout=5000")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        db.commit()


@app.teardown_appcontext
def close_db(_exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.template_filter("friendly_date")
def friendly_date(value):
    try:
        created = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return "Unknown"
    return created.astimezone(UTC).strftime("%b %d, %Y")


@app.get("/")
def index():
    db = get_db()
    tasks = db.execute(
        """
        SELECT id, title, completed, created_at
        FROM tasks
        ORDER BY completed ASC, created_at DESC, id DESC
        """
    ).fetchall()
    done = sum(task["completed"] for task in tasks)
    return render_template(
        "index.html",
        tasks=tasks,
        total=len(tasks),
        done=done,
        open_count=len(tasks) - done,
    )


@app.post("/tasks")
def add_task():
    title = " ".join(request.form.get("title", "").split())
    if not title:
        return redirect(url_for("index"))

    get_db().execute(
        "INSERT INTO tasks (title, completed, created_at) VALUES (?, 0, ?)",
        (title[:MAX_TITLE_LENGTH], datetime.now(UTC).isoformat(timespec="seconds")),
    )
    get_db().commit()
    return redirect(url_for("index"))


@app.post("/tasks/<int:task_id>/toggle")
def toggle_task(task_id):
    db = get_db()
    task = db.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task is not None:
        db.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?",
            (0 if task["completed"] else 1, task_id),
        )
        db.commit()
    return redirect(url_for("index"))


@app.post("/tasks/<int:task_id>/delete")
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return redirect(url_for("index"))


@app.get("/health")
def health():
    get_db().execute("SELECT 1").fetchone()
    return {"status": "ok"}


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
