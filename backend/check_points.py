import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'f1_data.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

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

for row in cursor.fetchall():
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

for row in cursor.fetchall():
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

for row in cursor.fetchall():
    print(f"{row[0]:<30} {row[1]:<12} {row[2]:<12} {row[3]:<12}")

conn.close() 