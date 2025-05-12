import sqlite3
import sys
from pathlib import Path


def print_schema(db_path):
    """Print the complete schema of the SQLite database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in the database.")
            return

        print(f"\n=== DATABASE SCHEMA: {Path(db_path).name} ===\n")

        # For each table, print its schema
        for table in tables:
            table_name = table[0]

            # Skip the sqlite_sequence table (internal SQLite table)
            if table_name == 'sqlite_sequence':
                continue

            print(f"\n-- TABLE: {table_name}")

            # Get table creation SQL
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            create_table_sql = cursor.fetchone()[0]
            print(f"{create_table_sql};")

            # Get column details
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            print("\n  COLUMNS:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                constraints = []
                if pk:
                    constraints.append("PRIMARY KEY")
                if not_null:
                    constraints.append("NOT NULL")
                if default_val is not None:
                    constraints.append(f"DEFAULT {default_val}")

                constraints_str = " ".join(constraints)
                print(f"    {col_name} ({col_type}) {constraints_str}")

            # Get indexes for this table
            cursor.execute(f"SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}';")
            indexes = cursor.fetchall()

            if indexes:
                print("\n  INDEXES:")
                for idx_name, idx_sql in indexes:
                    print(f"    {idx_name}: {idx_sql};")

        # Get views
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view';")
        views = cursor.fetchall()

        if views:
            print("\n=== VIEWS ===")
            for view_name, view_sql in views:
                print(f"\n-- VIEW: {view_name}")
                print(f"{view_sql};")

        # Get triggers
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger';")
        triggers = cursor.fetchall()

        if triggers:
            print("\n=== TRIGGERS ===")
            for trigger_name, trigger_sql in triggers:
                print(f"\n-- TRIGGER: {trigger_name}")
                print(f"{trigger_sql};")

        conn.close()

    except sqlite3.Error as e:
        print(f"SQLite error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


# Example usage
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py database_file.db")
        sys.exit(1)

    db_path = sys.argv[1]
    if not Path(db_path).exists():
        print(f"Error: Database file '{db_path}' not found.")
        sys.exit(1)

    print_schema(db_path)
