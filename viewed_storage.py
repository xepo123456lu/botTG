import os
from typing import Iterable

import aiosqlite

DEFAULT_DB_PATH = "viewed.sqlite3"


def _db_path() -> str:
    # Можно переопределить путь через переменную окружения (например, на хостинге).
    return os.getenv("VIEWED_DB_PATH") or DEFAULT_DB_PATH


async def init_viewed_db() -> None:
    """
    Локальная SQLite БД только для просмотров анкет.
    Хранит пары (viewer_id -> viewed_id), чтобы не показывать анкеты по кругу.
    """
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS viewed_profiles (
                viewer_id INTEGER NOT NULL,
                viewed_id INTEGER NOT NULL,
                viewed_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (viewer_id, viewed_id)
            )
            """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_viewed_profiles_viewer_id ON viewed_profiles (viewer_id)"
        )
        await db.commit()


async def get_viewed_ids(viewer_id: int) -> list[int]:
    async with aiosqlite.connect(_db_path()) as db:
        async with db.execute(
            "SELECT viewed_id FROM viewed_profiles WHERE viewer_id = ?",
            (viewer_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [int(r[0]) for r in rows]


async def mark_viewed(viewer_id: int, viewed_id: int) -> None:
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            "INSERT OR IGNORE INTO viewed_profiles (viewer_id, viewed_id) VALUES (?, ?)",
            (viewer_id, viewed_id),
        )
        await db.commit()


async def mark_viewed_many(viewer_id: int, viewed_ids: Iterable[int]) -> None:
    values = [(viewer_id, int(v)) for v in viewed_ids]
    if not values:
        return
    async with aiosqlite.connect(_db_path()) as db:
        await db.executemany(
            "INSERT OR IGNORE INTO viewed_profiles (viewer_id, viewed_id) VALUES (?, ?)",
            values,
        )
        await db.commit()

