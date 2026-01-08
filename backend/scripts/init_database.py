"""Initialize SQLite database with mock data."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.mock_data_generator import create_sqlite_database

if __name__ == "__main__":
    print("Initializing Tellius Intelligent Feed database...")
    print()

    create_sqlite_database("tellius_feed.db")

    print()
    print("✓ Database initialization complete!")
    print()
    print("Database file: tellius_feed.db")
    print()
