"""SQLite database for benchmark results storage.

Provides persistent storage for benchmark sessions and results,
with support for session comparison and historical analysis.
"""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from p2w.benchmark.runtimes import RuntimeInfo
from p2w.benchmark.stats import BenchmarkStats


@dataclass(frozen=True)
class BenchmarkResult:
    """Result of a single benchmark run.

    Attributes:
        benchmark: Benchmark name (e.g., "mandelbrot").
        runtime: Runtime identifier (e.g., "cpython", "pypy", "p2w-nodejs").
        stats: Statistical summary of timing measurements.
        output_hash: Hash of output for correctness verification.
    """

    benchmark: str
    runtime: str
    stats: BenchmarkStats
    output_hash: str


@dataclass
class Session:
    """A benchmark session containing multiple results.

    Attributes:
        id: Session ID (None until saved).
        timestamp: When the session was created.
        description: Optional description.
        git_commit: Git commit hash at time of run.
        results: List of benchmark results.
        runtime_info: Dictionary of runtime information.
    """

    timestamp: datetime
    description: str | None
    git_commit: str | None
    results: list[BenchmarkResult]
    runtime_info: dict[str, RuntimeInfo]
    id: int | None = None


def _get_git_commit() -> str | None:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]  # Short hash
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def hash_output(output: str) -> str:
    """Create a hash of benchmark output for verification."""
    return hashlib.sha256(output.encode("utf-8")).hexdigest()[:16]


class BenchmarkDatabase:
    """SQLite database for benchmark results."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection | None = None

    def __enter__(self) -> BenchmarkDatabase:
        """Open database connection."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close database connection."""
        self.close()

    def open(self) -> None:
        """Open database and initialize schema."""
        self.conn = sqlite3.connect(self.db_path)
        self._init_schema()

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _init_schema(self) -> None:
        """Initialize database schema."""
        if not self.conn:
            return

        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                description TEXT,
                git_commit TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY,
                session_id INTEGER NOT NULL,
                benchmark TEXT NOT NULL,
                runtime TEXT NOT NULL,
                mean_ms REAL,
                median_ms REAL,
                stddev_ms REAL,
                cv REAL,
                ci_lower REAL,
                ci_upper REAL,
                min_ms REAL,
                max_ms REAL,
                runs INTEGER,
                runs_to_stable INTEGER,
                outliers_removed INTEGER,
                output_hash TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runtime_info (
                id INTEGER PRIMARY KEY,
                session_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                version TEXT,
                path TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        self.conn.commit()

    def save_session(self, session: Session) -> int:
        """Save a benchmark session to the database.

        Args:
            session: Session to save.

        Returns:
            Session ID.
        """
        if not self.conn:
            raise RuntimeError("Database not open")

        cursor = self.conn.cursor()

        # Get git commit if not provided
        git_commit = session.git_commit or _get_git_commit()

        # Insert session
        cursor.execute(
            """
            INSERT INTO sessions (timestamp, description, git_commit)
            VALUES (?, ?, ?)
            """,
            (session.timestamp.isoformat(), session.description, git_commit),
        )
        session_id = cursor.lastrowid
        if session_id is None:
            raise RuntimeError("Failed to get session ID")

        # Insert results
        for result in session.results:
            cursor.execute(
                """
                INSERT INTO results (
                    session_id, benchmark, runtime,
                    mean_ms, median_ms, stddev_ms, cv,
                    ci_lower, ci_upper, min_ms, max_ms,
                    runs, runs_to_stable, outliers_removed, output_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    result.benchmark,
                    result.runtime,
                    result.stats.mean * 1000,  # Convert to ms
                    result.stats.median * 1000,
                    result.stats.stddev * 1000,
                    result.stats.cv,
                    result.stats.confidence_95[0] * 1000,
                    result.stats.confidence_95[1] * 1000,
                    result.stats.min * 1000,
                    result.stats.max * 1000,
                    len(result.stats.times),
                    result.stats.runs_to_stable,
                    len(result.stats.outliers),
                    result.output_hash,
                ),
            )

        # Insert runtime info
        for info in session.runtime_info.values():
            cursor.execute(
                """
                INSERT INTO runtime_info (session_id, name, version, path)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, info.name, info.version, info.path),
            )

        self.conn.commit()
        return session_id

    def load_session(self, session_id: int) -> Session | None:
        """Load a session from the database.

        Args:
            session_id: ID of session to load.

        Returns:
            Session or None if not found.
        """
        if not self.conn:
            raise RuntimeError("Database not open")

        cursor = self.conn.cursor()

        # Load session metadata
        cursor.execute(
            "SELECT timestamp, description, git_commit FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        timestamp = datetime.fromisoformat(row[0])
        description = row[1]
        git_commit = row[2]

        # Load results
        cursor.execute(
            """
            SELECT benchmark, runtime, mean_ms, median_ms, stddev_ms, cv,
                   ci_lower, ci_upper, min_ms, max_ms, runs, runs_to_stable,
                   outliers_removed, output_hash
            FROM results WHERE session_id = ?
            """,
            (session_id,),
        )

        results: list[BenchmarkResult] = []
        for row in cursor.fetchall():
            stats = BenchmarkStats(
                times=(),  # Original times not stored
                mean=row[2] / 1000,  # Convert from ms
                median=row[3] / 1000,
                stddev=row[4] / 1000,
                cv=row[5],
                min=row[8] / 1000,
                max=row[9] / 1000,
                iqr=0.0,  # Not stored
                outliers=(),
                confidence_95=(row[6] / 1000, row[7] / 1000),
                runs_to_stable=row[11],
            )
            results.append(
                BenchmarkResult(
                    benchmark=row[0],
                    runtime=row[1],
                    stats=stats,
                    output_hash=row[13] or "",
                )
            )

        # Load runtime info
        cursor.execute(
            "SELECT name, version, path FROM runtime_info WHERE session_id = ?",
            (session_id,),
        )
        runtime_info: dict[str, RuntimeInfo] = {}
        for row in cursor.fetchall():
            runtime_info[row[0]] = RuntimeInfo(
                name=row[0],
                version=row[1] or "",
                available=True,
                path=row[2],
            )

        return Session(
            id=session_id,
            timestamp=timestamp,
            description=description,
            git_commit=git_commit,
            results=results,
            runtime_info=runtime_info,
        )

    def list_sessions(self) -> list[tuple[int, datetime, str | None, str | None]]:
        """List all sessions.

        Returns:
            List of (id, timestamp, description, git_commit) tuples.
        """
        if not self.conn:
            raise RuntimeError("Database not open")

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, description, git_commit FROM sessions ORDER BY id DESC"
        )

        return [
            (row[0], datetime.fromisoformat(row[1]), row[2], row[3])
            for row in cursor.fetchall()
        ]

    def get_latest_session_id(self) -> int | None:
        """Get the ID of the most recent session.

        Returns:
            Session ID or None if no sessions exist.
        """
        if not self.conn:
            raise RuntimeError("Database not open")

        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM sessions")
        row = cursor.fetchone()
        return row[0] if row and row[0] else None

    def compare_sessions(
        self, id1: int, id2: int
    ) -> dict[str, dict[str, tuple[float, float, float]]]:
        """Compare two sessions.

        Args:
            id1: First session ID.
            id2: Second session ID.

        Returns:
            Dictionary mapping benchmark to runtime to
            (mean1_ms, mean2_ms, ratio) tuples.
        """
        session1 = self.load_session(id1)
        session2 = self.load_session(id2)

        if not session1 or not session2:
            return {}

        # Build lookup for session 2
        s2_lookup: dict[tuple[str, str], float] = {}
        for r in session2.results:
            s2_lookup[r.benchmark, r.runtime] = r.stats.mean * 1000

        # Compare
        comparison: dict[str, dict[str, tuple[float, float, float]]] = {}
        for r in session1.results:
            key = (r.benchmark, r.runtime)
            mean1 = r.stats.mean * 1000
            mean2 = s2_lookup.get(key, 0.0)

            if r.benchmark not in comparison:
                comparison[r.benchmark] = {}

            ratio = mean2 / mean1 if mean1 > 0 else 0.0
            comparison[r.benchmark][r.runtime] = (mean1, mean2, ratio)

        return comparison
