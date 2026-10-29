import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

TEMP_DIR = tempfile.TemporaryDirectory()
DATABASE_PATH = Path(TEMP_DIR.name) / "test.db"
os.environ["DATABASE_PATH"] = str(DATABASE_PATH)

from app import app, init_db


class TaskDockTests(unittest.TestCase):
    def setUp(self):
        init_db()
        with closing(sqlite3.connect(DATABASE_PATH)) as db:
            db.execute("DELETE FROM tasks")
            db.commit()
        self.client = app.test_client()

    def test_index_is_available(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nothing queued", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_task_can_be_added_completed_and_deleted(self):
        response = self.client.post(
            "/tasks",
            data={"title": "  Build the Docker image  "},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Build the Docker image", response.data)

        with closing(sqlite3.connect(DATABASE_PATH)) as db:
            task_id = db.execute("SELECT id FROM tasks").fetchone()[0]

        self.client.post(f"/tasks/{task_id}/toggle")
        with closing(sqlite3.connect(DATABASE_PATH)) as db:
            completed = db.execute(
                "SELECT completed FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()[0]
        self.assertEqual(completed, 1)

        self.client.post(f"/tasks/{task_id}/delete")
        with closing(sqlite3.connect(DATABASE_PATH)) as db:
            count = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        self.assertEqual(count, 0)

    def test_blank_tasks_are_ignored(self):
        self.client.post("/tasks", data={"title": "   "})
        with closing(sqlite3.connect(DATABASE_PATH)) as db:
            count = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        self.assertEqual(count, 0)


def tearDownModule():
    TEMP_DIR.cleanup()


if __name__ == "__main__":
    unittest.main()
