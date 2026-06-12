from datetime import datetime, timezone
from pathlib import Path
import sqlite3


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2].joinpath("docs", "ingest_registry.db")


class SQLiteIngestRegistry:
	def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
		self.db_path = db_path
		self.db_path.parent.mkdir(parents=True, exist_ok=True)
		self._init_db()

	def _connect(self) -> sqlite3.Connection:
		return sqlite3.connect(self.db_path)

	def _init_db(self) -> None:
		with self._connect() as conn:
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS documents (
					file_hash TEXT PRIMARY KEY,
					file_name TEXT,
					file_size INTEGER,
					source TEXT,
					ingested_at TEXT,
					num_chunks INTEGER
				)
				"""
			)

	def is_duplicate(self, file_hash: str) -> bool:
		with self._connect() as conn:
			row = conn.execute(
				"SELECT 1 FROM documents WHERE file_hash = ? LIMIT 1",
				(file_hash,),
			).fetchone()
			return row is not None

	def add_record(
		self,
		file_hash: str,
		file_name: str,
		file_size: int | None,
		source: str,
		num_chunks: int,
	) -> None:
		with self._connect() as conn:
			conn.execute(
				"""
				INSERT OR IGNORE INTO documents
				(file_hash, file_name, file_size, source, ingested_at, num_chunks)
				VALUES (?, ?, ?, ?, ?, ?)
				""",
				(
					file_hash,
					file_name,
					file_size,
					source,
					datetime.now(timezone.utc).isoformat(),
					num_chunks,
				),
			)
