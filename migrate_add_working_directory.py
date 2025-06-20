#!/usr/bin/env python3
"""
Migration script to add working_directory column to existing TutuItems table
"""
from pathlib import Path
import sqlite3

def get_db_path():
    """Get the database path"""
    return Path.home() / "a" / "base" / "tutu.sqlite"

def migrate():
    """Run the migration"""
    db_path = get_db_path()
    
    if not db_path.exists():
        print(f"🚫 Database not found at {db_path}")
        return
    
    print(f"📂 Migrating database at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tutu_items)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'working_directory' in columns:
            print("✅ Column 'working_directory' already exists!")
            return
        
        # Add the column
        cursor.execute("ALTER TABLE tutu_items ADD COLUMN working_directory VARCHAR(1024)")
        conn.commit()
        
        print("✅ Successfully added 'working_directory' column to tutu_items table!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()