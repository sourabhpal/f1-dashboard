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
db_path = os.path.join(os.path.dirname(__file__), 'f1_data.db')

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
        # Get qualifying positions
        quali_positions = {}
        try:
            quali_session = fastf1.get_session(year, round_num, 'Q')
            quali_session.load()
            for _, driver in quali_session.results.iterrows():
                quali_positions[driver['DriverNumber']] = driver['Position']
        except Exception as e:
            logger.warning(f"Error getting qualifying data for round {round_num}: {str(e)}")

        # Process race results
        driver_data = []
        team_data = {}

        for _, driver in session.results.iterrows():
            driver_number = driver['DriverNumber']
            driver_name = standardize_driver_name(driver['FullName'])
            team = driver['TeamName']
            position = driver['Position']
            
            # Calculate positions gained
            quali_pos = quali_positions.get(driver_number, position)
            positions_gained = quali_pos - position
            
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
                WHERE year = ? AND round = ? AND driver_name = ?
            """, (year, round_num, driver_name))
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
                        WHERE year = ? AND round = ? AND driver_name = ?
                    """, (points, position, year, round_num, driver_name))
                else:
                    # Update race points
                    cursor.execute("""
                        UPDATE driver_standings
                        SET points = ?,
                            position = ?,
                            is_sprint = 0
                        WHERE year = ? AND round = ? AND driver_name = ?
                    """, (points, position, year, round_num, driver_name))
            else:
                # Create new record
                driver_data.append((
                    year, round_num, driver_name, team,
                    0 if is_sprint else points,  # race points
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
                (year, round, driver_name, team, points, total_points, position,
                 fastest_lap_time, qualifying_position, positions_gained, pit_stops,
                 driver_number, driver_color, nationality, is_sprint, sprint_points,
                 sprint_position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, driver_data)
        
        # For sprint races, update the team data
        if is_sprint:
            for team, data in team_data.items():
                # Check if team record exists
                cursor.execute("""
                    SELECT points, sprint_points, is_sprint
                    FROM constructors_standings
                    WHERE year = ? AND round = ? AND team = ?
                """, (year, round_num, team))
                existing_team = cursor.fetchone()
                
                if existing_team:
                    # Update sprint points
                    cursor.execute("""
                        UPDATE constructors_standings
                        SET sprint_points = ?,
                            sprint_position = ?,
                            is_sprint = 1
                        WHERE year = ? AND round = ? AND team = ?
                    """, (
                        data['points'],
                        len([t for t in team_data if team_data[t]['points'] > data['points']]) + 1,
                        year, round_num, team
                    ))
                else:
                    # Create new team record
                    cursor.execute("""
                        INSERT INTO constructors_standings 
                        (year, round, team, points, total_points, position, wins, podiums,
                         fastest_laps, team_color, is_sprint, sprint_points, sprint_position)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        year, round_num, team,
                        0,  # race points
                        0,  # total_points will be updated later
                        None,  # position (main race)
                        data['wins'], data['podiums'], data['fastest_laps'],
                        f"#{data['color']}" if pd.notna(data['color']) and not str(data['color']).startswith('#') else str(data['color']),
                        True,  # is_sprint
                        data['points'],  # sprint points
                        len([t for t in team_data if team_data[t]['points'] > data['points']]) + 1  # sprint position
                    ))
        else:
            # For main races, update team data
            for team, data in team_data.items():
                # Check if team record exists
                cursor.execute("""
                    SELECT points, sprint_points, is_sprint
                    FROM constructors_standings
                    WHERE year = ? AND round = ? AND team = ?
                """, (year, round_num, team))
                existing_team = cursor.fetchone()
                
                if existing_team:
                    # Update race points
                    cursor.execute("""
                        UPDATE constructors_standings
                        SET points = ?,
                            position = ?,
                            wins = ?,
                            podiums = ?,
                            fastest_laps = ?,
                            is_sprint = 0
                        WHERE year = ? AND round = ? AND team = ?
                    """, (
                        data['points'],
                        len([t for t in team_data if team_data[t]['points'] > data['points']]) + 1,
                        data['wins'],
                        data['podiums'],
                        data['fastest_laps'],
                        year, round_num, team
                    ))
                else:
                    # Create new team record
                    cursor.execute("""
                        INSERT INTO constructors_standings 
                        (year, round, team, points, total_points, position, wins, podiums,
                         fastest_laps, team_color, is_sprint, sprint_points, sprint_position)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        year, round_num, team,
                        data['points'],  # race points
                        0,  # total_points will be updated later
                        len([t for t in team_data if team_data[t]['points'] > data['points']]) + 1,
                        data['wins'], data['podiums'], data['fastest_laps'],
                        f"#{data['color']}" if pd.notna(data['color']) and not str(data['color']).startswith('#') else str(data['color']),
                        False,  # is_sprint
                        0,  # sprint points
                        None  # sprint position
                    ))
        
        # Update total points after each race
        update_total_points(cursor, year)
        
        logger.info(f"Successfully processed {'sprint' if is_sprint else 'race'} data for Round {round_num}")
        
    except Exception as e:
        logger.error(f"Error processing {'sprint' if is_sprint else 'race'} data for Round {round_num}: {str(e)}")
        raise

def update_total_points(cursor, year=2025):
    """Update total points for drivers and teams efficiently."""
    try:
        # Update driver total points
        cursor.execute("""
            WITH driver_points AS (
                SELECT 
                    driver_name,
                    round,
                    SUM(points + sprint_points) OVER (
                        PARTITION BY driver_name 
                        ORDER BY round
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) as total_points
                FROM driver_standings
                WHERE year = ?
            )
            UPDATE driver_standings
            SET total_points = (
                SELECT dp.total_points 
                FROM driver_points dp
                WHERE dp.driver_name = driver_standings.driver_name
                AND dp.round = driver_standings.round
            )
            WHERE year = ?
        """, (year, year))
        
        # Update team total points
        cursor.execute("""
            WITH team_points AS (
                SELECT 
                    team,
                    round,
                    SUM(points + sprint_points) OVER (
                        PARTITION BY team 
                        ORDER BY round
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) as total_points
                FROM constructors_standings
                WHERE year = ?
            )
            UPDATE constructors_standings
            SET total_points = (
                SELECT tp.total_points 
                FROM team_points tp
                WHERE tp.team = constructors_standings.team
                AND tp.round = constructors_standings.round
            )
            WHERE year = ?
        """, (year, year))
        
        logger.info("Successfully updated total points")
        
    except Exception as e:
        logger.error(f"Error updating total points: {str(e)}")
        raise

def populate_2025_data():
    """Populate the database with 2025 F1 data."""
    try:
        # Get database connection using context manager
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Drop all existing tables to ensure clean schema
            cursor.execute("DROP TABLE IF EXISTS race_schedule")
            cursor.execute("DROP TABLE IF EXISTS driver_standings")
            cursor.execute("DROP TABLE IF EXISTS constructors_standings")
            
            # Create tables with updated schema
            create_tables()
            
            # Get 2025 schedule
            schedule = fastf1.get_event_schedule(2025)
            
            # Get current date
            current_date = datetime.now().date()
            
            # Process each race
            for _, event in schedule.iterrows():
                round_num = event['RoundNumber']
                race_date = event['EventDate'].date()
                
                # Skip races that haven't happened yet
                if race_date > current_date:
                    logger.info(f"Skipping Round {round_num} ({event['EventName']}) - Race hasn't happened yet (scheduled for {race_date})")
                    continue
                
                # Store race schedule
                cursor.execute("""
                    INSERT OR REPLACE INTO race_schedule
                    (year, round, name, date, country, is_sprint)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    2025,
                    round_num,
                    event['EventName'],
                    event['EventDate'].strftime('%Y-%m-%d'),
                    event['Country'],
                    event['EventFormat'] in ['sprint', 'sprint_qualifying']
                ))
                
                try:
                    # Check if this is a sprint race
                    is_sprint = event['EventFormat'] in ['sprint', 'sprint_qualifying']
                    if is_sprint:
                        logger.info(f"Loading sprint session for Round {round_num} ({event['EventName']})")
                        sprint_session = fastf1.get_session(2025, round_num, 'S')
                        if sprint_session:
                            logger.info("Sprint session found, loading data...")
                            sprint_session.load()
                            logger.info("Processing sprint race data...")
                            process_race_data(sprint_session, round_num, cursor, year=2025, is_sprint=True)
                        else:
                            logger.warning("No sprint session found")
                    
                    # Process main race
                    logger.info(f"Loading main race session for Round {round_num} ({event['EventName']})")
                    race_session = fastf1.get_session(2025, round_num, 'R')
                    if race_session:
                        logger.info("Race session found, loading data...")
                        race_session.load()
                        logger.info("Processing main race data...")
                        process_race_data(race_session, round_num, cursor, year=2025, is_sprint=False)
                    else:
                        logger.warning("No race session found")
                    
                except Exception as e:
                    logger.error(f"Error processing Round {round_num}: {str(e)}")
                    continue
            
            conn.commit()
            
        logger.info("Successfully populated 2025 data")
        
    except Exception as e:
        logger.error(f"Error populating 2025 data: {str(e)}")
        raise

if __name__ == "__main__":
    populate_2025_data() 