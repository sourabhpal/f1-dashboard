import sqlite3
import os
from update_database import populate_2025_data, init_db, get_db_connection

def fix_database():
    try:
        # Remove existing database if it exists
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'f1_data.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Removed existing database file")
        
        # Initialize new database
        print("Initializing new database...")
        init_db()
        
        # Populate with 2025 data
        print("Populating 2025 data...")
        populate_2025_data()
        
        # Verify the data
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check Lando Norris's points
            cursor.execute('''
                SELECT round, points, sprint_points, total_points 
                FROM driver_standings 
                WHERE driver_name = "Lando Norris" 
                ORDER BY round
            ''')
            print("\nLando Norris's points breakdown:")
            print("Round | Race Pts | Sprint Pts | Total Pts")
            print("-" * 40)
            for row in cursor.fetchall():
                print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
            
            # Check total points calculation
            cursor.execute('''
                SELECT driver_name, SUM(points + sprint_points) as total
                FROM driver_standings
                GROUP BY driver_name
                ORDER BY total DESC
                LIMIT 5
            ''')
            print("\nTop 5 drivers by total points:")
            print("Driver | Total Points")
            print("-" * 30)
            for row in cursor.fetchall():
                print(f"{row[0]} | {row[1]}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    fix_database() 