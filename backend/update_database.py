import fastf1
import pandas as pd
import sqlite3
import logging
import os
import time
import hashlib
import numpy as np
import shutil
from tqdm import tqdm
from datetime import datetime
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
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Driver nationality mapping
DRIVER_NATIONALITIES = {
    # 2025 Drivers
    'Lando Norris': 'British',
    'Max Verstappen': 'Dutch',
    'George Russell': 'British',
    'Kimi Antonelli': 'Italian',
    'Alexander Albon': 'Thai',
    'Lance Stroll': 'Canadian',
    'Nico Hulkenberg': 'German',
    'Charles Leclerc': 'Monegasque',
    'Oscar Piastri': 'Australian',
    'Lewis Hamilton': 'British',
    'Pierre Gasly': 'French',
    'Yuki Tsunoda': 'Japanese',
    'Esteban Ocon': 'French',
    'Oliver Bearman': 'British',
    'Liam Lawson': 'New Zealander',
    'Gabriel Bortoleto': 'Brazilian',
    'Fernando Alonso': 'Spanish',
    'Carlos Sainz': 'Spanish',
    'Jack Doohan': 'Australian',
    'Isack Hadjar': 'French',
    
    # Add more drivers as needed
}

def get_schema_hash():
    """Calculate a hash of the current database schema."""
    schema = """
    CREATE TABLE IF NOT EXISTS race_schedule (
        year INTEGER,
        round INTEGER,
        name TEXT,
        date TEXT,
        qualifying_date TEXT,
        sprint_date TEXT,
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
        qualifying_time TEXT,
        positions_gained INTEGER,
        pit_stops INTEGER,
        driver_number INTEGER,
        driver_color TEXT,
        nationality TEXT,
        is_sprint BOOLEAN DEFAULT 0,
        sprint_points INTEGER DEFAULT 0,
        sprint_position INTEGER,
        laps INTEGER,
        status TEXT,
        grid_position INTEGER,
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
        is_sprint BOOLEAN DEFAULT 0,
        sprint_points INTEGER DEFAULT 0,
        sprint_position INTEGER,
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
        db_path = '/app/data/f1_data.db'
        
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
                qualifying_date TEXT,
                sprint_date TEXT,
                country TEXT,
                is_sprint BOOLEAN DEFAULT 0,
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
                qualifying_time TEXT,
                positions_gained INTEGER,
                pit_stops INTEGER,
                driver_number INTEGER,
                driver_color TEXT,
                nationality TEXT,
                is_sprint BOOLEAN DEFAULT 0,
                sprint_points INTEGER DEFAULT 0,
                sprint_position INTEGER,
                laps INTEGER,
                status TEXT,
                grid_position INTEGER,
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
                is_sprint BOOLEAN DEFAULT 0,
                sprint_points INTEGER DEFAULT 0,
                sprint_position INTEGER,
                PRIMARY KEY (year, round, team)
            )
        """)
        
        # Create schema_version table if it doesn't exist
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_race_schedule_qualifying_date ON race_schedule(qualifying_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_race_schedule_sprint_date ON race_schedule(sprint_date)")
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
        # Get results
        results = session.results
        
        # Initialize data containers
        driver_data = []
        team_data = {}
        
        # Process each driver
        for _, driver in results.iterrows():
            driver_name = standardize_driver_name(driver['FullName'])
            team = driver['TeamName']
            driver_number = driver['DriverNumber']
            position = int(driver['Position']) if pd.notna(driver['Position']) else 99
            quali_pos = None
            positions_gained = 0
            pit_stops = 0
            fastest_lap_time = None
            
            # Get qualifying position if available
            if hasattr(session, 'qualifying') and session.qualifying is not None:
                quali_results = session.qualifying.results
                if not quali_results.empty:
                    quali_driver = quali_results[quali_results['DriverNumber'] == driver_number]
                    if not quali_driver.empty:
                        quali_pos = int(quali_driver.iloc[0]['Position'])
                        positions_gained = quali_pos - position if position != 99 else 0
            
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
            
            # Get nationality from our mapping
            nationality = DRIVER_NATIONALITIES.get(driver_name, 'Unknown')
            
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
                            is_sprint = 1,
                            nationality = ?
                        WHERE year = ? AND round = ? AND driver_name = ?
                    """, (points, position, nationality, year, round_num, driver_name))
                else:
                    # Update race points
                    cursor.execute("""
                        UPDATE driver_standings
                        SET points = ?,
                            position = ?,
                            is_sprint = 0,
                            nationality = ?
                        WHERE year = ? AND round = ? AND driver_name = ?
                    """, (points, position, nationality, year, round_num, driver_name))
            else:
                # Create new record
                driver_data.append((
                    year, round_num, driver_name, team,
                    0 if is_sprint else points,  # race points
                    0,  # total_points will be updated later
                    None if is_sprint else position,  # position (main race)
                    fastest_lap_time, quali_pos, positions_gained,
                    pit_stops, driver_number, driver['TeamColor'],
                    nationality, is_sprint,
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
                 fastest_lap_time, qualifying_position, qualifying_time, positions_gained,
                 pit_stops, driver_number, driver_color, nationality, is_sprint,
                 sprint_points, sprint_position, laps, status, grid_position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(
                year, round_num,
                driver_name, team,
                0 if is_sprint else points,  # points
                0,  # total_points
                None if is_sprint else position,  # position
                fastest_lap_time,
                quali_pos,
                None,  # qualifying_time
                positions_gained,
                pit_stops,
                driver_number,
                driver['TeamColor'],
                nationality,
                is_sprint,
                points if is_sprint else 0,  # sprint_points
                position if is_sprint else None,  # sprint_position
                None,  # laps
                None,  # status
                None  # grid_position
            ) for (year, round_num, driver_name, team, points, position,
                   fastest_lap_time, quali_pos, positions_gained,
                   pit_stops, driver_number, driver_color, nationality, is_sprint,
                   sprint_points, sprint_position) in driver_data])
        
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
        
        # Commit the transaction
        cursor.connection.commit()
        
        logger.info(f"Successfully processed {'sprint' if is_sprint else 'race'} data for Round {round_num}")
        
    except Exception as e:
        logger.error(f"Error processing {'sprint' if is_sprint else 'race'} data for Round {round_num}: {str(e)}")
        raise

def update_total_points(cursor, year=2025):
    """Update total points for drivers and teams efficiently."""
    try:
        # Get all driver points
        cursor.execute("""
            SELECT driver_name, round, points, sprint_points
            FROM driver_standings
            WHERE year = ?
            ORDER BY driver_name, round
        """, (year,))
        
        # Calculate cumulative points for each driver
        driver_points = {}
        for driver_name, round_num, points, sprint_points in cursor.fetchall():
            if driver_name not in driver_points:
                driver_points[driver_name] = {}
            total = points + (sprint_points or 0)
            if round_num > 1:
                total += driver_points[driver_name][round_num - 1]
            driver_points[driver_name][round_num] = total
        
        # Update driver total points
        for driver_name, rounds in driver_points.items():
            for round_num, total in rounds.items():
                cursor.execute("""
                    UPDATE driver_standings
                    SET total_points = ?
                    WHERE year = ? AND round = ? AND driver_name = ?
                """, (total, year, round_num, driver_name))
        
        # Get all team points
        cursor.execute("""
            SELECT team, round, points, sprint_points
            FROM constructors_standings
            WHERE year = ?
            ORDER BY team, round
        """, (year,))
        
        # Calculate cumulative points for each team
        team_points = {}
        for team, round_num, points, sprint_points in cursor.fetchall():
            if team not in team_points:
                team_points[team] = {}
            total = points + (sprint_points or 0)
            if round_num > 1:
                total += team_points[team][round_num - 1]
            team_points[team][round_num] = total
        
        # Update team total points
        for team, rounds in team_points.items():
            for round_num, total in rounds.items():
                cursor.execute("""
                    UPDATE constructors_standings
                    SET total_points = ?
                    WHERE year = ? AND round = ? AND team = ?
                """, (total, year, round_num, team))
        
        # Commit the changes
        cursor.connection.commit()
        
        logger.info("Successfully updated total points")
        
    except Exception as e:
        logger.error(f"Error updating total points: {str(e)}")
        raise

def update_driver_nationalities(cursor):
    """Update driver nationalities in the database."""
    try:
        # Get all unique drivers
        cursor.execute("""
            SELECT DISTINCT driver_name 
            FROM driver_standings
        """)
        drivers = cursor.fetchall()
        
        # Update nationalities
        updated_count = 0
        for (driver_name,) in drivers:
            if driver_name in DRIVER_NATIONALITIES:
                nationality = DRIVER_NATIONALITIES[driver_name]
                cursor.execute("""
                    UPDATE driver_standings
                    SET nationality = ?
                    WHERE driver_name = ?
                """, (nationality, driver_name))
                updated_count += 1
                logger.info(f"Updated nationality for {driver_name} to {nationality}")
        
        logger.info(f"Updated nationalities for {updated_count} drivers")
        
    except Exception as e:
        logger.error(f"Error updating driver nationalities: {str(e)}")
        raise

def process_qualifying_data(session, round_num, cursor, year=2025):
    """Process qualifying data efficiently."""
    try:
        # Get qualifying results
        results = session.results
        
        # Process each driver's qualifying result
        for _, driver in results.iterrows():
            driver_name = standardize_driver_name(driver['FullName'])
            team = driver['TeamName']
            driver_number = driver['DriverNumber']
            position = int(driver['Position']) if pd.notna(driver['Position']) else None
            
            # Get best qualifying time
            qualifying_time = None
            if 'Q3' in driver and pd.notna(driver['Q3']):
                qualifying_time = str(driver['Q3'])
            elif 'Q2' in driver and pd.notna(driver['Q2']):
                qualifying_time = str(driver['Q2'])
            elif 'Q1' in driver and pd.notna(driver['Q1']):
                qualifying_time = str(driver['Q1'])
            
            # Get nationality from our mapping
            nationality = DRIVER_NATIONALITIES.get(driver_name, 'Unknown')
            
            # Update or insert qualifying data
            cursor.execute("""
                INSERT INTO driver_standings 
                (year, round, driver_name, team, points, total_points, position,
                 fastest_lap_time, qualifying_position, qualifying_time, positions_gained,
                 pit_stops, driver_number, driver_color, nationality, is_sprint,
                 sprint_points, sprint_position, laps, status, grid_position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(year, round, driver_name) 
                DO UPDATE SET
                    qualifying_position = excluded.qualifying_position,
                    qualifying_time = excluded.qualifying_time,
                    nationality = excluded.nationality
            """, (
                year, round_num,
                driver_name, team,
                0,  # points
                0,  # total_points
                None,  # position
                None,  # fastest_lap_time
                position,  # qualifying_position
                qualifying_time,
                None,  # positions_gained
                None,  # pit_stops
                driver_number,
                driver['TeamColor'],
                nationality,
                False,  # is_sprint
                0,  # sprint_points
                None,  # sprint_position
                None,  # laps
                None,  # status
                None  # grid_position
            ))
            
        logger.info(f"Successfully processed qualifying data for Round {round_num}")
        
    except Exception as e:
        logger.error(f"Error processing qualifying data for Round {round_num}: {str(e)}")
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
            cursor.execute("DROP TABLE IF EXISTS circuits")
            cursor.execute("DROP TABLE IF EXISTS race_positions")
            
            # Create tables with updated schema
            init_db()
            
            # Get 2025 schedule
            schedule = fastf1.get_event_schedule(2025)
            logger.info(f"Schedule columns: {schedule.columns.tolist()}")
            logger.info(f"First row: {schedule.iloc[0].to_dict()}")
            
            # Get current date
            current_date = datetime.now().date()
            
            # Process each race weekend
            for _, event in schedule.iterrows():
                round_num = event['RoundNumber']
                race_date = event['EventDate'].date()
                
                # Find qualifying and sprint dates from session information
                qualifying_date = None
                sprint_date = None
                for i in range(1, 6):
                    session_name = event[f'Session{i}']
                    session_date = event[f'Session{i}Date']
                    if pd.notna(session_name) and pd.notna(session_date):
                        if 'Qualifying' in str(session_name):
                            qualifying_date = session_date.date()
                        elif 'Sprint' in str(session_name):
                            sprint_date = session_date.date()
                
                # Store race schedule for ALL races, including future ones
                cursor.execute("""
                    INSERT OR REPLACE INTO race_schedule
                    (year, round, name, date, qualifying_date, sprint_date, country, is_sprint)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    2025,
                    round_num,
                    event['EventName'],
                    event['EventDate'].strftime('%Y-%m-%d'),
                    qualifying_date.strftime('%Y-%m-%d') if qualifying_date else None,
                    sprint_date.strftime('%Y-%m-%d') if sprint_date else None,
                    event['Country'],
                    event['EventFormat'] in ['sprint', 'sprint_qualifying']
                ))
                
                # Process qualifying data if it has happened
                if qualifying_date and qualifying_date <= current_date:
                    try:
                        logger.info(f"Loading qualifying session for Round {round_num} ({event['EventName']})")
                        quali_session = fastf1.get_session(2025, round_num, 'Q')
                        if quali_session:
                            logger.info("Qualifying session found, loading data...")
                            quali_session.load()
                            logger.info("Processing qualifying data...")
                            process_qualifying_data(quali_session, round_num, cursor, year=2025)
                        else:
                            logger.warning("No qualifying session found")
                    except Exception as e:
                        logger.error(f"Error processing qualifying for Round {round_num}: {str(e)}")
                else:
                    logger.info(f"Skipping qualifying data for Round {round_num} - Session hasn't happened yet")
                
                # Only process race/sprint data for races that have already happened
                if race_date > current_date:
                    logger.info(f"Skipping race data for Round {round_num} ({event['EventName']}) - Race hasn't happened yet")
                    continue
                
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
            
            # Update driver nationalities
            logger.info("Updating driver nationalities...")
            update_driver_nationalities(cursor)
            
            conn.commit()
            
        logger.info("Successfully populated 2025 data with nationalities")
        
    except Exception as e:
        logger.error(f"Error populating 2025 data: {str(e)}")
        raise

if __name__ == "__main__":
    populate_2025_data() 