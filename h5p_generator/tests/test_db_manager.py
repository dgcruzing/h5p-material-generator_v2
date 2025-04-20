"""Tests for database manager."""

import unittest
import tempfile
from pathlib import Path
import sqlite3

from h5p_generator.db_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test DatabaseManager class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db").name
        self.db_manager = DatabaseManager(Path(self.temp_db))

    def test_init_db(self):
        """Test database initialization."""
        # Check if default frameworks are added
        frameworks = self.db_manager.get_all_frameworks()
        self.assertGreaterEqual(len(frameworks), 3)
        self.assertIn("Bloom's Taxonomy", frameworks)

    def test_add_and_get_framework(self):
        """Test adding and retrieving frameworks."""
        # Add new framework
        success = self.db_manager.add_framework("Test Framework", "Test prompt")
        self.assertTrue(success)

        # Check if framework was added
        frameworks = self.db_manager.get_all_frameworks()
        self.assertIn("Test Framework", frameworks)

        # Get prompt by name
        prompt = self.db_manager.get_prompt_by_name("Test Framework")
        self.assertEqual(prompt, "Test prompt")

    def test_delete_framework(self):
        """Test deleting frameworks."""
        # Add framework
        self.db_manager.add_framework("Temp Framework", "Temp prompt")

        # Delete framework
        success = self.db_manager.delete_framework("Temp Framework")
        self.assertTrue(success)

        # Check if framework was deleted
        frameworks = self.db_manager.get_all_frameworks()
        self.assertNotIn("Temp Framework", frameworks)

    def test_unique_constraint(self):
        """Test unique constraint for framework names."""
        # Add framework
        self.db_manager.add_framework("Unique Framework", "First prompt")

        # Try to add framework with same name
        success = self.db_manager.add_framework("Unique Framework", "Second prompt")
        self.assertFalse(success)
