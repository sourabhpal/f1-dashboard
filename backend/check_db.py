import sqlite3
import os

def check_database():
    db_path = '/app/data/f1_data.db'
    print(f"Checking database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database file does not exist at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\nTables in database:")
    for table in tables:
        print(f"\nTable: {table[0]}")
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_database() 