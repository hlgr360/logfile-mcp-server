#!/usr/bin/env python3
"""
AI: Create demo database using shared test database factory.

Uses the standardized test database factory to create demo.db
with consistent test data across all testing scenarios.
"""

import sys
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.fixtures.test_database import create_demo_db


def main():
    """AI: Create demo database with sample data."""
    print("🚀 Creating demo database using shared test factory...")

    db_conn = None
    try:
        db_ops, db_conn = create_demo_db("demo.db")

        # Get actual counts from the created database
        nginx_count = db_ops.execute_query("SELECT COUNT(*) as count FROM nginx_logs")[0]['count']
        nexus_count = db_ops.execute_query("SELECT COUNT(*) as count FROM nexus_logs")[0]['count']

        print("✅ Demo database created successfully!")
        print("📊 Database populated with:")
        print(f"   - {nginx_count} nginx log entries")
        print(f"   - {nexus_count} nexus log entries")
        print("   - Realistic test data from sample logs")
        print("🌐 You can now start the web interface or connect VS Code Copilot")

    except Exception as e:
        print(f"❌ Error creating demo database: {e}")
        sys.exit(1)
    finally:
        # Ensure database connection is properly closed
        if db_conn:
            db_conn.close()


if __name__ == "__main__":
    main()
