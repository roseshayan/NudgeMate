import aiosqlite
from datetime import datetime, timezone
from typing import Optional, List
from nudgemate.config import settings
from nudgemate.database.models import Task, Note, User


class Database:
    def __init__(self, db_path: str = str(settings.DATABASE_PATH)):
        self.db_path = db_path

    async def init_db(self):
        """Initializes tables and configures SQLite pragmas for high performance."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA foreign_keys=ON;")

            # Users table
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                timezone TEXT DEFAULT 'Asia/Tehran',
                daily_briefing_enabled INTEGER DEFAULT 1,
                daily_briefing_time TEXT DEFAULT '08:30',
                nag_interval_minutes INTEGER DEFAULT 15,
                max_nag_count INTEGER DEFAULT 3,
                created_at TEXT,
                language TEXT DEFAULT 'fa'
            );
            """)

            # Automatic migration for existing DB
            try:
                await db.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'fa';")
            except Exception:
                pass

            # Tasks table
            await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                category TEXT DEFAULT 'general',
                priority TEXT DEFAULT 'medium',
                nag_count INTEGER DEFAULT 0,
                last_nag_at TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            );
            """)

            # Notes / Memory table (Second Brain)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            );
            """)

            await db.commit()

    async def get_or_create_user(self, user_id: int, first_name: str, username: Optional[str] = None) -> User:
        """Retrieves an existing user or creates a new one with default preferences."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()

            if row:
                lang = row["language"] if "language" in row.keys() else "fa"
                return User(
                    user_id=row["user_id"],
                    first_name=row["first_name"],
                    username=row["username"],
                    timezone=row["timezone"],
                    daily_briefing_enabled=bool(row["daily_briefing_enabled"]),
                    daily_briefing_time=row["daily_briefing_time"],
                    nag_interval_minutes=row["nag_interval_minutes"],
                    max_nag_count=row["max_nag_count"],
                    created_at=row["created_at"],
                    language=lang or "fa",
                )

            now_str = datetime.now(timezone.utc).isoformat()
            await db.execute(
                """
                INSERT INTO users (user_id, first_name, username, timezone, created_at, language)
                VALUES (?, ?, ?, ?, ?, 'fa')
                """,
                (user_id, first_name, username, settings.TIMEZONE, now_str),
            )
            await db.commit()

            return User(
                user_id=user_id,
                first_name=first_name,
                username=username,
                timezone=settings.TIMEZONE,
                daily_briefing_enabled=True,
                daily_briefing_time="08:30",
                nag_interval_minutes=settings.NAG_INTERVAL_MINUTES,
                max_nag_count=settings.MAX_NAG_COUNT,
                created_at=now_str,
                language="fa",
            )

    async def set_user_language(self, user_id: int, language: str):
        """Updates user's preferred language ('fa' or 'en')."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET language = ? WHERE user_id = ?",
                (language, user_id),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[User]:
        """Gets user by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            lang = row["language"] if "language" in row.keys() else "fa"
            return User(
                user_id=row["user_id"],
                first_name=row["first_name"],
                username=row["username"],
                timezone=row["timezone"],
                daily_briefing_enabled=bool(row["daily_briefing_enabled"]),
                daily_briefing_time=row["daily_briefing_time"],
                nag_interval_minutes=row["nag_interval_minutes"],
                max_nag_count=row["max_nag_count"],
                created_at=row["created_at"],
                language=lang or "fa",
            )


    async def create_task(
        self,
        user_id: int,
        title: str,
        remind_at: str,
        category: str = "general",
        priority: str = "medium",
    ) -> int:
        """Saves a new task and returns its database ID."""
        now_str = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO tasks (user_id, title, remind_at, status, category, priority, nag_count, created_at)
                VALUES (?, ?, ?, 'pending', ?, ?, 0, ?)
                """,
                (user_id, title, remind_at, category, priority, now_str),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_task(self, task_id: int) -> Optional[Task]:
        """Gets a single task by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            return Task(
                id=row["id"],
                user_id=row["user_id"],
                title=row["title"],
                remind_at=row["remind_at"],
                status=row["status"],
                category=row["category"],
                priority=row["priority"],
                nag_count=row["nag_count"],
                last_nag_at=row["last_nag_at"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )

    async def get_user_pending_tasks(self, user_id: int) -> List[Task]:
        """Gets all active pending tasks for a user ordered by remind_at."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE user_id = ? AND status = 'pending' ORDER BY remind_at ASC",
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [
                Task(
                    id=r["id"],
                    user_id=r["user_id"],
                    title=r["title"],
                    remind_at=r["remind_at"],
                    status=r["status"],
                    category=r["category"],
                    priority=r["priority"],
                    nag_count=r["nag_count"],
                    last_nag_at=r["last_nag_at"],
                    created_at=r["created_at"],
                    completed_at=r["completed_at"],
                )
                for r in rows
            ]

    async def get_due_tasks(self, current_iso: str) -> List[Task]:
        """Gets all tasks whose scheduled time has arrived and have not been alerted yet (nag_count == 0)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM tasks
                WHERE status = 'pending'
                  AND remind_at <= ?
                  AND nag_count = 0
                """,
                (current_iso,),
            )
            rows = await cursor.fetchall()
            return [
                Task(
                    id=r["id"],
                    user_id=r["user_id"],
                    title=r["title"],
                    remind_at=r["remind_at"],
                    status=r["status"],
                    category=r["category"],
                    priority=r["priority"],
                    nag_count=r["nag_count"],
                    last_nag_at=r["last_nag_at"],
                    created_at=r["created_at"],
                    completed_at=r["completed_at"],
                )
                for r in rows
            ]

    async def get_tasks_due_for_nagging(self) -> List[Task]:
        """Gets tasks that were alerted but not confirmed/snoozed, needing another nag."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM tasks
                WHERE status = 'pending'
                  AND nag_count > 0
                  AND nag_count < ?
                """,
                (settings.MAX_NAG_COUNT,),
            )
            rows = await cursor.fetchall()
            return [
                Task(
                    id=r["id"],
                    user_id=r["user_id"],
                    title=r["title"],
                    remind_at=r["remind_at"],
                    status=r["status"],
                    category=r["category"],
                    priority=r["priority"],
                    nag_count=r["nag_count"],
                    last_nag_at=r["last_nag_at"],
                    created_at=r["created_at"],
                    completed_at=r["completed_at"],
                )
                for r in rows
            ]

    async def mark_task_completed(self, task_id: int):
        """Marks a task as completed."""
        now_str = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?",
                (now_str, task_id),
            )
            await db.commit()

    async def snooze_task(self, task_id: int, new_remind_at: str):
        """Reschedules a task for later and resets nag count."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tasks SET remind_at = ?, nag_count = 0, last_nag_at = NULL WHERE id = ?",
                (new_remind_at, task_id),
            )
            await db.commit()

    async def update_nag_status(self, task_id: int, nag_count: int, last_nag_at: str):
        """Updates nag counter and timestamp."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tasks SET nag_count = ?, last_nag_at = ? WHERE id = ?",
                (nag_count, last_nag_at, task_id),
            )
            await db.commit()

    async def delete_task(self, task_id: int):
        """Permanently deletes a task."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()

    async def create_note(self, user_id: int, content: str, tags: str = "") -> int:
        """Stores a second-brain note/memo."""
        now_str = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO notes (user_id, content, tags, created_at) VALUES (?, ?, ?, ?)",
                (user_id, content, tags, now_str),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_user_notes(self, user_id: int, limit: int = 15) -> List[Note]:
        """Gets recent notes for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM notes WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            rows = await cursor.fetchall()
            return [
                Note(
                    id=r["id"],
                    user_id=r["user_id"],
                    content=r["content"],
                    tags=r["tags"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    async def search_notes(self, user_id: int, query: str) -> List[Note]:
        """Searches notes by keyword."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            like_query = f"%{query}%"
            cursor = await db.execute(
                "SELECT * FROM notes WHERE user_id = ? AND (content LIKE ? OR tags LIKE ?) ORDER BY id DESC LIMIT 10",
                (user_id, like_query, like_query),
            )
            rows = await cursor.fetchall()
            return [
                Note(
                    id=r["id"],
                    user_id=r["user_id"],
                    content=r["content"],
                    tags=r["tags"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    async def get_user_stats(self, user_id: int) -> dict:
        """Calculates task completion statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            pending = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'completed'",
                (user_id,),
            )
            completed = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COUNT(*) FROM notes WHERE user_id = ?",
                (user_id,),
            )
            notes_count = (await cursor.fetchone())[0]

            return {
                "pending": pending,
                "completed": completed,
                "notes": notes_count,
            }

    async def get_all_users(self) -> List[User]:
        """Retrieves all registered users for global broadcasts or briefings."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users")
            rows = await cursor.fetchall()
            return [
                User(
                    user_id=r["user_id"],
                    first_name=r["first_name"],
                    username=r["username"],
                    timezone=r["timezone"],
                    daily_briefing_enabled=bool(r["daily_briefing_enabled"]),
                    daily_briefing_time=r["daily_briefing_time"],
                    nag_interval_minutes=r["nag_interval_minutes"],
                    max_nag_count=r["max_nag_count"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]


db = Database()
