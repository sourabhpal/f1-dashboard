import sqlite3
import os
from datetime import datetime

DB_PATH = '/app/data/f1_data.db'

def fix_schema():
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Drop existing tables
        cursor.execute("DROP TABLE IF EXISTS driver_standings")
        cursor.execute("DROP TABLE IF EXISTS constructors_standings")
        cursor.execute("DROP TABLE IF EXISTS race_schedule")
        
        # Create tables with correct schema
        cursor.execute("""
        CREATE TABLE driver_standings (
            year INTEGER,
            round INTEGER,
            driver_name TEXT,
            team TEXT,
            points INTEGER DEFAULT 0,
            position INTEGER,
            wins INTEGER DEFAULT 0,
            fastest_laps INTEGER DEFAULT 0,
            nationality TEXT,
            qualifying_position INTEGER,
            sprint_position INTEGER,
            sprint_points INTEGER DEFAULT 0,
            is_sprint BOOLEAN DEFAULT 0,
            PRIMARY KEY (year, round, driver_name)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE constructors_standings (
            year INTEGER,
            round INTEGER,
            team TEXT,
            points INTEGER DEFAULT 0,
            position INTEGER,
            wins INTEGER DEFAULT 0,
            sprint_points INTEGER DEFAULT 0,
            is_sprint BOOLEAN DEFAULT 0,
            sprint_position INTEGER,
            PRIMARY KEY (year, round, team)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE race_schedule (
            year INTEGER,
            round INTEGER,
            name TEXT,
            date TEXT,
            country TEXT,
            is_sprint BOOLEAN DEFAULT 0,
            PRIMARY KEY (year, round)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_driver_standings_year ON driver_standings(year)")
        cursor.execute("CREATE INDEX idx_driver_standings_driver ON driver_standings(driver_name)")
        cursor.execute("CREATE INDEX idx_driver_standings_team ON driver_standings(team)")
        cursor.execute("CREATE INDEX idx_constructors_standings_year ON constructors_standings(year)")
        cursor.execute("CREATE INDEX idx_constructors_standings_team ON constructors_standings(team)")
        cursor.execute("CREATE INDEX idx_race_schedule_year ON race_schedule(year)")
        
        # Commit the changes
        conn.commit()
        print("Schema has been fixed successfully!")
        
    except Exception as e:
        print(f"Error fixing schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema() 