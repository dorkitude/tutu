#!/usr/bin/env python3
"""
Migration script to convert existing UTC timestamps to Pacific time
"""
import sqlite3
from pathlib import Path
import pytz
from datetime import datetime

# Pacific timezone
PACIFIC_TZ = pytz.timezone('America/Los_Angeles')
UTC_TZ = pytz.UTC

def get_db_path():
    db_path = Path.home() / "a" / "base" / "tutu.sqlite"
    return str(db_path)

def convert_utc_to_pacific(utc_timestamp_str):
    """Convert UTC timestamp string to Pacific timezone"""
    if not utc_timestamp_str:
        return None
    
    # Parse the timestamp (SQLite stores as string in format: YYYY-MM-DD HH:MM:SS.ssssss)
    # Handle both with and without microseconds
    try:
        utc_dt = datetime.strptime(utc_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        try:
            utc_dt = datetime.strptime(utc_timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print(f"Warning: Could not parse timestamp: {utc_timestamp_str}")
            return utc_timestamp_str
    
    # Add UTC timezone info
    utc_dt = UTC_TZ.localize(utc_dt)
    
    # Convert to Pacific
    pacific_dt = utc_dt.astimezone(PACIFIC_TZ)
    
    # Return as string without timezone info (SQLite doesn't store timezone)
    return pacific_dt.strftime('%Y-%m-%d %H:%M:%S.%f')

def migrate_database():
    """Migrate all timestamps from UTC to Pacific timezone"""
    db_path = get_db_path()
    
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Backup current data first
        print("Creating backup...")
        backup_path = db_path + '.backup_before_tz_migration'
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Backup created at: {backup_path}")
        
        # Migrate tutu_items table
        print("\nMigrating tutu_items table...")
        cursor.execute("SELECT id, created_at, updated_at, first_progress_at FROM tutu_items")
        items = cursor.fetchall()
        
        for item_id, created_at, updated_at, first_progress_at in items:
            new_created_at = convert_utc_to_pacific(created_at)
            new_updated_at = convert_utc_to_pacific(updated_at)
            new_first_progress_at = convert_utc_to_pacific(first_progress_at) if first_progress_at else None
            
            if new_first_progress_at:
                cursor.execute("""
                    UPDATE tutu_items 
                    SET created_at = ?, updated_at = ?, first_progress_at = ?
                    WHERE id = ?
                """, (new_created_at, new_updated_at, new_first_progress_at, item_id))
            else:
                cursor.execute("""
                    UPDATE tutu_items 
                    SET created_at = ?, updated_at = ?
                    WHERE id = ?
                """, (new_created_at, new_updated_at, item_id))
            
            print(f"  Item {item_id}: {created_at} -> {new_created_at}")
        
        # Migrate tutu_item_steps table
        print("\nMigrating tutu_item_steps table...")
        cursor.execute("SELECT id, created_at, updated_at FROM tutu_item_steps")
        steps = cursor.fetchall()
        
        for step_id, created_at, updated_at in steps:
            new_created_at = convert_utc_to_pacific(created_at)
            new_updated_at = convert_utc_to_pacific(updated_at)
            
            cursor.execute("""
                UPDATE tutu_item_steps 
                SET created_at = ?, updated_at = ?
                WHERE id = ?
            """, (new_created_at, new_updated_at, step_id))
            
            print(f"  Step {step_id}: {created_at} -> {new_created_at}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during migration: {e}")
        print("Database has been rolled back. Your backup is available at:", backup_path)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("🕐 Migrating Tutu database from UTC to Pacific timezone...")
    migrate_database()