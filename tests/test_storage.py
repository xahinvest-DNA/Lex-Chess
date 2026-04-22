import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from app.storage.sqlite import SQLiteStorage, utcnow


class StorageTests(unittest.TestCase):
    def test_storage_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "bot.sqlite3"
            storage = SQLiteStorage(db_path)
            storage.init()

            storage.save_session(1, {"step_index": 2, "answers": {"name": "Ivan"}})
            session = storage.get_session(1)
            self.assertIsNotNone(session)
            self.assertEqual(session["step_index"], 2)

            storage.schedule_reminder(1, "incomplete", utcnow() + timedelta(seconds=1), {})
            due = storage.list_due_reminders(utcnow() + timedelta(seconds=2))
            self.assertEqual(len(due), 1)


if __name__ == "__main__":
    unittest.main()
