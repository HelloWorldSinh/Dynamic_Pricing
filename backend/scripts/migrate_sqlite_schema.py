"""Script to safely add missing columns to SQLite database (dynamic_pricing.db)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "dynamic_pricing.db"

def add_column_if_not_exists(cursor, table: str, column_def: str, column_name: str):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        print(f"Adding column '{column_name}' to table '{table}'...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
    else:
        print(f"Column '{column_name}' already exists in table '{table}'.")

def migrate():
    if not DB_PATH.exists():
        print(f"Database file not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        # Table products
        add_column_if_not_exists(cur, "products", "cost_price BIGINT", "cost_price")
        add_column_if_not_exists(cur, "products", "min_margin_pct FLOAT DEFAULT 0.10", "min_margin_pct")
        add_column_if_not_exists(cur, "products", "floor_price BIGINT", "floor_price")
        add_column_if_not_exists(cur, "products", "base_retail_price BIGINT", "base_retail_price")

        # Table crawl_results
        add_column_if_not_exists(cur, "crawl_results", "job_id CHAR(36)", "job_id")

        # Table sku_mappings
        add_column_if_not_exists(cur, "sku_mappings", "reviewed_at TIMESTAMP", "reviewed_at")
        add_column_if_not_exists(cur, "sku_mappings", "reviewed_by VARCHAR(100)", "reviewed_by")

        conn.commit()
        print("Schema migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Migration error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
