import fastf1
import pandas as pd
import sqlite3
import logging
from datetime import datetime
import os
import time
import hashlib
import numpy as np
import shutil
from tqdm import tqdm
from f1_backend import create_tables, get_db_connection, calculate_points

# Configure logging with a cleaner format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Prevent duplicate logs from FastF1
logging.getLogger('fastf1').propagate = False
logger = logging.getLogger(__name__)

# Set up FastF1 cache
cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# Database path
db_path = '/app/data/f1_data.db'

def get_schema_hash():
    """Calculate a hash of the current database schema."""
    schema = """
    CREATE TABLE IF NOT EXISTS race_schedule (
        year INTEGER,
        round INTEGER,
        name TEXT,
        date TEXT,
        event TEXT,
        country TEXT,
        PRIMARY KEY (year, round)
    );
    
    CREATE TABLE IF NOT EXISTS circuits (
        year INTEGER,
        round INTEGER,
        circuit_name TEXT,
        location TEXT,
        country TEXT,
        circuit_length REAL,
        number_of_laps INTEGER,
        first_grand_prix INTEGER,
        lap_record TEXT,
        track_map TEXT,
        PRIMARY KEY (year, round)
    );
    
    CREATE TABLE IF NOT EXISTS driver_standings (
        year INTEGER,
        round INTEGER,
        driver_name TEXT,
        team TEXT,
        points INTEGER,
        total_points INTEGER,
        position INTEGER,
        fastest_lap_time TEXT,
        qualifying_position INTEGER,
        positions_gained INTEGER,
        pit_stops INTEGER,
        driver_number INTEGER,
        driver_color TEXT,
        nationality TEXT,
        sprint_points INTEGER DEFAULT 0,
        PRIMARY KEY (year, round, driver_name)
    );

    CREATE TABLE IF NOT EXISTS constructors_standings (
        year INTEGER,
        round INTEGER,
        team TEXT,
        points INTEGER,
        total_points INTEGER,
        position INTEGER,
        wins INTEGER,
        podiums INTEGER,
        fastest_laps INTEGER,
        team_color TEXT,
        sprint_position INTEGER DEFAULT NULL,
        PRIMARY KEY (year, round, team)
    );
    """
    return hashlib.md5(schema.encode()).hexdigest()

def needs_rebuild():
    """Check if the database needs to be rebuilt."""
    if not os.path.exists(db_path):
        logger.info("Database file does not exist, needs to be rebuilt")
        return True
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if schema_version table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        if not cursor.fetchone():
            logger.info("Schema version table not found, needs to be rebuilt")
            return True
            
        # Get current schema version
        cursor.execute("SELECT version FROM schema_version")
        current_version = cursor.fetchone()[0]
        
        # Compare with current schema hash
        if current_version != get_schema_hash():
            logger.info("Database schema has changed, needs to be rebuilt")
            return True
            
        # Check if we have data for 2025
        cursor.execute("SELECT COUNT(*) FROM race_schedule WHERE year = 2025")
        if cursor.fetchone()[0] == 0:
            logger.info("No 2025 data found, needs to be rebuilt")
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error checking if rebuild is needed: {str(e)}")
        return True
    finally:
        conn.close()

def init_db(db_path=None):
    """Initialize the database with required tables."""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), 'f1_data.db')
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Create race_schedule table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS race_schedule (
                year INTEGER,
                round INTEGER,
                name TEXT,
                date TEXT,
                event TEXT,
                country TEXT,
                PRIMARY KEY (year, round)
            )
        """)
        
        # Create circuits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circuits (
                year INTEGER,
                round INTEGER,
                circuit_name TEXT,
                location TEXT,
                country TEXT,
                circuit_length REAL,
                number_of_laps INTEGER,
                first_grand_prix INTEGER,
                lap_record TEXT,
                track_map TEXT,
                PRIMARY KEY (year, round)
            )
        """)
        
        # Create driver_standings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS driver_standings (
                year INTEGER,
                round INTEGER,
                driver_name TEXT,
                team TEXT,
                points INTEGER,
                total_points INTEGER,
                position INTEGER,
                fastest_lap_time TEXT,
                qualifying_position INTEGER,
                positions_gained INTEGER,
                pit_stops INTEGER,
                driver_number INTEGER,
                driver_color TEXT,
                nationality TEXT,
                sprint_points INTEGER DEFAULT 0,
                PRIMARY KEY (year, round, driver_name)
            )
        """)

        # Create constructors_standings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS constructors_standings (
                year INTEGER,
                round INTEGER,
                team TEXT,
                points INTEGER,
                total_points INTEGER,
                position INTEGER,
                wins INTEGER,
                podiums INTEGER,
                fastest_laps INTEGER,
                team_color TEXT,
                sprint_position INTEGER DEFAULT NULL,
                PRIMARY KEY (year, round, team)
            )
        """)
        
        # Create schema_version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY
            )
        """)
        
        # Store current schema version
        cursor.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (get_schema_hash(),))
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_race_schedule_year ON race_schedule(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_race_schedule_date ON race_schedule(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circuits_year ON circuits(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circuits_country ON circuits(country)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_driver_standings_year ON driver_standings(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_driver_standings_driver ON driver_standings(driver_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_driver_standings_team ON driver_standings(team)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_constructors_standings_year ON constructors_standings(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_constructors_standings_team ON constructors_standings(team)")
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def load_session_data(year, round_num, session_type='R'):
    """Load and cache session data efficiently."""
    try:
        session = fastf1.get_session(year, round_num, session_type)
        logger.info(f"Loading {session_type} session data for Round {round_num}")
        
        # Load all required data at once
        session.load(
            weather=False,
            messages=False,
            laps=True,
            telemetry=True
        )
        
        return session
    except Exception as e:
        logger.error(f"Error loading {session_type} session data for Round {round_num}: {str(e)}")
        return None

def standardize_driver_name(name):
    """
    Standardize driver names to ensure consistency.
    
    Args:
        name (str): Driver name to standardize
        
    Returns:
        str: Standardized driver name
    """
    name_mapping = {
        'Andrea Kimi Antonelli': 'Kimi Antonelli',
        'Kimi Antonelli': 'Kimi Antonelli',
        'Isack Hadjar': 'Isack Hadjar',
        'Gabriel Bortoleto': 'Gabriel Bortoleto',
        'Jack Doohan': 'Jack Doohan',
        'Liam Lawson': 'Liam Lawson',
        'Yuki Tsunoda': 'Yuki Tsunoda',
        'Pierre Gasly': 'Pierre Gasly',
        'Fernando Alonso': 'Fernando Alonso',
        'Carlos Sainz': 'Carlos Sainz',
        'Lewis Hamilton': 'Lewis Hamilton',
        'Charles Leclerc': 'Charles Leclerc',
        'Lance Stroll': 'Lance Stroll',
        'Esteban Ocon': 'Esteban Ocon',
        'Oliver Bearman': 'Oliver Bearman',
        'Nico Hulkenberg': 'Nico Hulkenberg',
        'Alexander Albon': 'Alexander Albon',
        'George Russell': 'George Russell',
        'Oscar Piastri': 'Oscar Piastri',
        'Lando Norris': 'Lando Norris',
        'Max Verstappen': 'Max Verstappen'
    }
    return name_mapping.get(name, name)

def process_race_data(session, round_num, cursor, year=2025, is_sprint=False):
    """Process race data efficiently in batches."""
    try:
        # Get qualifying positions for positions gained calculation
        quali_positions = {}
        try:
            quali_session = fastf1.get_session(year, round_num, 'Q')
            quali_session.load()
            for _, driver in quali_session.results.iterrows():
                quali_positions[driver['DriverNumber']] = driver['Position']
        except Exception as e:
            logger.warning(f"Error loading qualifying data for round {round_num}: {str(e)}")
        
        driver_data = []
        team_data = {}
        
        for _, driver in session.results.iterrows():
            driver_number = driver['DriverNumber']
            driver_name = driver['FullName']
            standardized_name = standardize_driver_name(driver_name)
            team = driver['TeamName']
            position = driver['Position']
            
            # Calculate positions gained
            quali_pos = quali_positions.get(driver_number, position)
            positions_gained = quali_pos - position if position > 0 else 0
            
            # Get pit stops efficiently
            pit_stops = 0
            fastest_lap_time = 'N/A'
            
            try:
                # Try to get driver laps first
                driver_laps = None
                if hasattr(session, 'laps') and session.laps is not None:
                    driver_laps = session.laps.pick_drivers(driver_number)
                
                # Try to get pit stops from telemetry data
                if hasattr(session, 'car_data') and session.car_data is not None:
                    try:
                        if driver_number in session.car_data:
                            car_data = session.car_data[driver_number]
                            if not car_data.empty:
                                pit_stops = 2 if not is_sprint else 0  # Default to 2 pit stops for main race, 0 for sprint
                    except Exception as e:
                        logger.warning(f"Error getting pit stops from car data for {driver_name}: {str(e)}")
                
                # If we couldn't get pit stops from car data, use a reasonable default
                if pit_stops == 0 and not is_sprint:
                    pit_stops = 2  # Most races have 2 pit stops
                
                # Get fastest lap
                if driver_laps is not None and not driver_laps.empty:
                    fastest_lap = driver_laps['LapTime'].min()
                    if pd.notnull(fastest_lap):
                        fastest_lap_time = str(fastest_lap)
                elif 'FastestLap' in driver and driver['FastestLap']:
                    fastest_lap_time = "Fastest Lap"
            except Exception as e:
                logger.warning(f"Error calculating pit stops and fastest lap for {driver_name}: {str(e)}")
                pit_stops = 2 if not is_sprint else 0  # Default values
            
            # Calculate points based on position and race type
            points = calculate_points(position, is_fastest_lap=(fastest_lap_time == "Fastest Lap"), is_sprint=is_sprint)
            
            # Check if a record exists for this driver in this round
            cursor.execute("""
                SELECT points, sprint_points, is_sprint
                FROM driver_standings
                WHERE year = ? AND round = ? AND standardized_driver_name = ?
            """, (year, round_num, standardized_name))
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Update existing record
                if is_sprint:
                    # Update sprint points
                    cursor.execute("""
                        UPDATE driver_standings
                        SET sprint_points = ?,
                            sprint_position = ?,
                            is_sprint = 1
                        WHERE year = ? AND round = ? AND standardized_driver_name = ?
                    """, (points, position, year, round_num, standardized_name))
                else:
                    # Update race points and ensure sprint points are preserved
                    cursor.execute("""
                        UPDATE driver_standings
                        SET points = ?,
                            position = ?,
                            is_sprint = CASE WHEN is_sprint = 1 THEN 1 ELSE 0 END
                        WHERE year = ? AND round = ? AND standardized_driver_name = ?
                    """, (points, position, year, round_num, standardized_name))
            else:
                # Create new record
                driver_data.append((
                    year, round_num, driver_name, standardized_name, team,
                    points if not is_sprint else 0,  # race points
                    0,  # total_points will be updated later
                    None if is_sprint else position,  # position (main race)
                    fastest_lap_time, quali_pos, positions_gained,
                    pit_stops, driver_number, driver['TeamColor'],
                    driver.get('Nationality', 'Unknown'), is_sprint,
                    points if is_sprint else 0,  # sprint points
                    position if is_sprint else None  # sprint position
                ))
            
            # Update team data
            if team not in team_data:
                team_data[team] = {
                    'points': 0,
                    'wins': 0,
                    'podiums': 0,
                    'fastest_laps': 0,
                    'color': driver['TeamColor'],
                    'is_sprint': is_sprint
                }
            
            team_data[team]['points'] += points
            if position == 1:
                team_data[team]['wins'] += 1
            if position <= 3:
                team_data[team]['podiums'] += 1
            if driver.get('FastestLap', False):
                team_data[team]['fastest_laps'] += 1
        
        # Batch insert driver data (only for new records)
        if driver_data:
            cursor.executemany("""
                INSERT INTO driver_standings 
                (year, round, driver_name, standardized_driver_name, team, points, total_points, position,
                 fastest_lap_time, qualifying_position, positions_gained, pit_stops,
                 driver_number, driver_color, nationality, is_sprint, sprint_points,
                 sprint_position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, driver_data)
        
        # Process team data
        for team, data in team_data.items():
            if is_sprint:
                cursor.execute("""
                    UPDATE constructors_standings
                    SET sprint_points = ?,
                        sprint_position = ?,
                        is_sprint = 1
                    WHERE year = ? AND round = ? AND team = ?
                """, (data['points'], data['position'] if 'position' in data else None, year, round_num, team))
            else:
                cursor.execute("""
                    UPDATE constructors_standings
                    SET points = ?,
                        position = ?,
                        wins = wins + ?,
                        podiums = podiums + ?,
                        fastest_laps = fastest_laps + ?
                    WHERE year = ? AND round = ? AND team = ?
                """, (
                    data['points'],
                    data['position'] if 'position' in data else None,
                    data['wins'],
                    data['podiums'],
                    data['fastest_laps'],
                    year, round_num, team
                ))
        
        # Update total points
        update_total_points(cursor, year)
        
    except Exception as e:
        logger.error(f"Error processing race data for round {round_num}: {str(e)}")
        raise

def update_total_points(cursor, year=2025):
    """Update total points for drivers and teams efficiently."""
    try:
        # Update driver total points
        cursor.execute("""
            UPDATE driver_standings
            SET total_points = (
                SELECT SUM(points + sprint_points)
                FROM driver_standings ds2
                WHERE ds2.year = driver_standings.year
                AND ds2.driver_name = driver_standings.driver_name
                AND ds2.round <= driver_standings.round
            )
            WHERE year = ?
        """, (year,))
        
        # Update team total points
        cursor.execute("""
            UPDATE constructors_standings
            SET total_points = (
                SELECT SUM(points + sprint_points)
                FROM constructors_standings cs2
                WHERE cs2.year = constructors_standings.year
                AND cs2.team = constructors_standings.team
                AND cs2.round <= constructors_standings.round
            )
            WHERE year = ?
        """, (year,))
        
        logger.info("Successfully updated total points")
        
    except Exception as e:
        logger.error(f"Error updating total points: {str(e)}")
        raise

def populate_2025_data():
    """Populate race data for the 2025 season."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get sprint races
            cursor.execute("""
                SELECT round, name 
                FROM race_schedule 
                WHERE year = 2025 AND is_sprint = 1
                ORDER BY round
            """)
            sprint_races = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Process each round
            for round_num in range(1, 24):  # 23 races in 2025
                try:
                    # Check if this round has a sprint race
                    if round_num in sprint_races:
                        logger.info(f"Processing sprint race for Round {round_num} ({sprint_races[round_num]})")
                        try:
                            # Load sprint session
                            sprint_session = fastf1.get_session(2025, round_num, 'S')
                            sprint_session.load()
                            # Process sprint data
                            process_race_data(sprint_session, round_num, cursor, year=2025, is_sprint=True)
                        except Exception as e:
                            logger.error(f"Error processing sprint data for Round {round_num}: {str(e)}")
                    
                    # Process main race
                    logger.info(f"Processing main race for Round {round_num}")
                    race_session = fastf1.get_session(2025, round_num, 'R')
                    race_session.load()
                    process_race_data(race_session, round_num, cursor, year=2025, is_sprint=False)
                    
                    # Commit after each round is processed
                    conn.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing Round {round_num}: {str(e)}")
                    continue
            
            # Final update of total points
            update_total_points(cursor, 2025)
            conn.commit()
            
            logger.info("Successfully populated 2025 data")
            
    except Exception as e:
        logger.error(f"Error populating 2025 data: {str(e)}")
        raise

if __name__ == '__main__':
    populate_2025_data() 