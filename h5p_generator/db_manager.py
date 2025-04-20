"""Database operations for H5P Material Generator."""

import sqlite3
from typing import List, Tuple, Optional
from pathlib import Path

from h5p_generator.config import DB_PATH


class DatabaseManager:
    """Manager for SQLite database operations."""

    def __init__(self, db_path: Path = DB_PATH):
        """Initialize database connection path."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()

                # Create frameworks table if it doesn't exist
                c.execute("""
                    CREATE TABLE IF NOT EXISTS frameworks (
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE,
                        prompt TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Add default frameworks if table is empty
                c.execute("SELECT COUNT(*) FROM frameworks")
                if c.fetchone()[0] == 0:
                    self._add_default_frameworks(c)

                # No explicit commit needed with `with` statement
        except sqlite3.Error as e:
            # Consider adding logging here
            print(f"Database initialization error: {e}")
            raise  # Re-raise the exception after logging/printing

    def _add_default_frameworks(self, cursor) -> None:
        """Add default prompt frameworks (expects an active cursor)."""
        # This method now expects an active cursor from the calling function
        # to operate within the same transaction.
        examples = [
            (
                "Bloom's Taxonomy",
                "Generate questions aligned with Bloom's Taxonomy: 2 remembering, 2 understanding, "
                "2 applying, 2 analyzing, 1 evaluating, 1 creating. Return in JSON format.",
            ),
            (
                "Socratic Method",
                "Generate questions that encourage critical thinking and exploration, "
                "following the Socratic Method. Return 10 questions in JSON format.",
            ),
            (
                "Simple Recall",
                "Generate straightforward recall questions to test basic comprehension "
                "of the text. Return 10 questions in JSON format.",
            ),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO frameworks (name, prompt) VALUES (?, ?)", examples
        )

    def get_all_frameworks(self) -> List[str]:
        """Get all framework names."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT name FROM frameworks ORDER BY name")
                frameworks = [row[0] for row in c.fetchall()]
            return frameworks
        except sqlite3.Error as e:
            print(f"Error fetching frameworks: {e}")
            return []  # Return empty list on error

    def get_prompt_by_name(self, name: str) -> Optional[str]:
        """Get prompt text by framework name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT prompt FROM frameworks WHERE name = ?", (name,))
                result = c.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error fetching prompt for {name}: {e}")
            return None  # Return None on error

    def add_framework(self, name: str, prompt: str) -> bool:
        """Add new prompt framework."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO frameworks (name, prompt) VALUES (?, ?)",
                    (name, prompt),
                )
            return True
        except sqlite3.IntegrityError:
            # Framework with this name already exists - expected, not an error
            return False
        except sqlite3.Error as e:
            print(f"Error adding framework {name}: {e}")
            return False  # Return False on other SQL errors

    def delete_framework(self, name: str) -> bool:
        """Delete prompt framework by name."""
        deleted = False
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM frameworks WHERE name = ?", (name,))
                deleted = c.rowcount > 0
            return deleted
        except sqlite3.Error as e:
            print(f"Error deleting framework {name}: {e}")
            return False  # Return False on error
