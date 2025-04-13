import sqlite3
import os
import sys

# Get the database path - use Docker path when running in container
db_path = '/app/data/f1_data.db' if os.path.exists('/app/data/f1_data.db') else os.path.join(os.path.dirname(__file__), 'data', 'f1_data.db')

def check_table_exists(cursor, table_name):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if required tables exist
    if not check_table_exists(cursor, 'driver_standings'):
        print("Error: driver_standings table does not exist")
        sys.exit(1)
    if not check_table_exists(cursor, 'constructors_standings'):
        print("Error: constructors_standings table does not exist")
        sys.exit(1)

    # First, check the sprint race data
    print("\nSprint Race Details:")
    print("=" * 100)
    cursor.execute("""
        SELECT 
            round,
            driver_name,
            position,
            points,
            sprint_points,
            is_sprint
        FROM driver_standings 
        WHERE year = 2025 AND is_sprint = 1
        ORDER BY round, position
    """)

    print(f"{'Round':<6} {'Driver':<30} {'Position':<10} {'Points':<8} {'Sprint Points':<12} {'Is Sprint':<10}")
    print("-" * 100)

    sprint_rows = cursor.fetchall()
    if not sprint_rows:
        print("No sprint race data found for 2025")
    else:
        for row in sprint_rows:
            print(f"{row[0]:<6} {row[1]:<30} {row[2]:<10} {row[3]:<8} {row[4]:<12} {row[5]:<10}")

    # Query to get driver points
    print("\nDriver Points:")
    print("=" * 80)
    cursor.execute("""
        SELECT 
            driver_name,
            SUM(points) as race_points,
            SUM(sprint_points) as sprint_points,
            SUM(points + sprint_points) as total_points
        FROM driver_standings 
        WHERE year = 2025 
        GROUP BY driver_name 
        ORDER BY total_points DESC
    """)

    print(f"{'Driver Name':<30} {'Race Points':<12} {'Sprint Points':<12} {'Total Points':<12}")
    print("-" * 80)

    driver_rows = cursor.fetchall()
    if not driver_rows:
        print("No driver points data found for 2025")
    else:
        for row in driver_rows:
            print(f"{row[0]:<30} {row[1]:<12} {row[2]:<12} {row[3]:<12}")

    # Query to get team points
    print("\nTeam Points:")
    print("=" * 80)
    cursor.execute("""
        SELECT 
            team,
            SUM(points) as race_points,
            SUM(sprint_points) as sprint_points,
            SUM(points + sprint_points) as total_points
        FROM constructors_standings 
        WHERE year = 2025 
        GROUP BY team 
        ORDER BY total_points DESC
    """)

    print(f"{'Team Name':<30} {'Race Points':<12} {'Sprint Points':<12} {'Total Points':<12}")
    print("-" * 80)

    team_rows = cursor.fetchall()
    if not team_rows:
        print("No team points data found for 2025")
    else:
        for row in team_rows:
            print(f"{row[0]:<30} {row[1]:<12} {row[2]:<12} {row[3]:<12}")

except sqlite3.Error as e:
    print(f"Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close() 