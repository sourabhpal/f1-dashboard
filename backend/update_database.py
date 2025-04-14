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
from validate_and_repair import validate_sprint_data, repair_sprint_data

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
db_path = os.path.join(os.path.dirname(__file__), 'data', 'f1_data.db')
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
        standardized_driver_name TEXT,
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
        is_sprint INTEGER DEFAULT 0,
        sprint_points INTEGER DEFAULT 0,
        sprint_position INTEGER,
        laps INTEGER,
        status TEXT,
        grid_position INTEGER,
        fastest_lap_count INTEGER DEFAULT 0,
        PRIMARY KEY (year, round, standardized_driver_name)
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
        is_sprint INTEGER DEFAULT 0,
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
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'f1_data.db')
        
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
        
        # Create driver_standings table with standardized_driver_name column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS driver_standings (
                year INTEGER,
                round INTEGER,
                driver_name TEXT,
                standardized_driver_name TEXT,
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
                is_sprint INTEGER DEFAULT 0,
                sprint_points INTEGER DEFAULT 0,
                sprint_position INTEGER,
                laps INTEGER,
                status TEXT,
                grid_position INTEGER,
                fastest_lap_count INTEGER DEFAULT 0,
                PRIMARY KEY (year, round, standardized_driver_name)
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
                is_sprint INTEGER DEFAULT 0,
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_driver_standings_driver ON driver_standings(standardized_driver_name)")
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

def get_race_info(year, round):
    """Get race information from FastF1."""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        race_name = session.event.EventName
        race_date = session.event.EventDate.strftime('%Y-%m-%d')
        country = session.event.Country
        
        return (race_name, race_date, country)
    except Exception as e:
        logger.error(f"Error getting race info for {year} Round {round}: {str(e)}")
        return None

def get_race_results(year, round, race_type='race'):
    """Get race results from FastF1."""
    try:
        session_type = 'S' if race_type == 'sprint' else 'R'
        session = fastf1.get_session(year, round, session_type)
        session.load()
        
        results = []
        for _, driver in session.results.iterrows():
            driver_name = standardize_driver_name(driver['FullName'])
            team = driver['TeamName']
            driver_number = driver['DriverNumber']
            position = int(driver['Position']) if pd.notna(driver['Position']) else 99
            status = driver['Status'] if 'Status' in driver else 'Finished'
            
            # Get driver color and nationality
            driver_color = driver['TeamColor'] if 'TeamColor' in driver else '#000000'
            nationality = DRIVER_NATIONALITIES.get(driver_name, 'Unknown')
            
            results.append({
                'driver_number': driver_number,
                'driver_name': driver_name,
                'team': team,
                'position': position,
                'status': status,
                'driver_color': driver_color,
                'team_color': driver_color,
                'nationality': nationality
            })
            
        return results
    except Exception as e:
        logger.error(f"Error getting {race_type} results for {year} Round {round}: {str(e)}")
        return None

def validate_and_repair_sprint_data(conn, year, round_num, race_name):
    """Validate and repair sprint data for a specific race."""
    try:
        cursor = conn.cursor()
        
        # Check if sprint data exists
        cursor.execute("""
            SELECT COUNT(*) FROM driver_standings
            WHERE year = ? AND round = ? AND is_sprint = 1
        """, (year, round_num))
        
        count = cursor.fetchone()[0]
        if count == 0:
            logger.warning(f"No sprint records found for {race_name} (Round {round_num})")
            return False
        
        # Check if sprint points were assigned
        cursor.execute("""
            SELECT COUNT(*) FROM driver_standings
            WHERE year = ? AND round = ? AND is_sprint = 1 AND sprint_points > 0
        """, (year, round_num))
        
        points_count = cursor.fetchone()[0]
        if points_count == 0:
            logger.warning(f"No sprint points assigned for {race_name} (Round {round_num})")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating sprint data: {str(e)}")
        return False

def repair_sprint_data(conn, year, round_num, race_name):
    """Repair missing or incorrect sprint data for a specific race."""
    try:
        cursor = conn.cursor()
        
        # Load sprint session data
        session = load_session_data(year, round_num, 'S')
        if not session:
            logger.error(f"Could not load sprint session for Round {round_num}")
            return False
        
        # Start a transaction for this race
        cursor.execute("BEGIN TRANSACTION")
        
        # Process each driver's sprint result
        for _, driver in session.results.iterrows():
            try:
                driver_name = standardize_driver_name(driver['FullName'])
                team = driver['TeamName']
                position = int(driver['Position']) if pd.notna(driver['Position']) else None
                status = driver['Status'] if 'Status' in driver else 'Finished'
                
                # Calculate sprint points
                points = 0
                if position is not None:
                    if position == 1:
                        points = 8
                    elif position == 2:
                        points = 7
                    elif position == 3:
                        points = 6
                    elif position == 4:
                        points = 5
                    elif position == 5:
                        points = 4
                    elif position == 6:
                        points = 3
                    elif position == 7:
                        points = 2
                    elif position == 8:
                        points = 1
                
                # First, try to update existing record
                cursor.execute("""
                    UPDATE driver_standings
                    SET sprint_points = ?,
                        sprint_position = ?,
                        is_sprint = 1
                    WHERE year = ? AND round = ? AND standardized_driver_name = ?
                """, (points, position, year, round_num, driver_name))
                
                # If no record was updated, insert a new one
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO driver_standings (
                            year, round, driver_name, standardized_driver_name, team,
                            points, total_points, position, status, is_sprint,
                            sprint_points, sprint_position
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        year, round_num, driver['FullName'], driver_name, team,
                        0, 0, None, status, 1,
                        points, position
                    ))
                
            except Exception as e:
                logger.error(f"Error processing driver {driver.get('FullName', 'Unknown')}: {str(e)}")
                continue
        
        # Commit the transaction for this race
        conn.commit()
        logger.info(f"Successfully repaired sprint data for Round {round_num}")
        return True
        
    except Exception as e:
        logger.error(f"Error repairing sprint data for Round {round_num}: {str(e)}")
        conn.rollback()
        return False

def process_race_data(conn, year, round_num, race_type='race'):
    """Process race data for both sprint and main race."""
    try:
        cursor = conn.cursor()
        
        # Get race data
        session = load_session_data(year, round_num, race_type)
        if not session:
            logger.error(f"No session data found for {year} Round {round_num} ({race_type})")
            return
            
        # Get qualifying positions for positions gained calculation
        quali_positions = get_qualifying_positions(year, round)
        
        # Process driver standings
        driver_data = []
        for _, driver in session.results.iterrows():
            try:
                driver_name = driver['FullName']
                standardized_name = standardize_driver_name(driver_name)
                team = driver['TeamName']
                position = driver.get('Position', None)
                status = driver.get('Status', 'Finished')
                
                # Calculate points based on race type
                if race_type == 'sprint':
                    points = calculate_points(position, is_sprint=True)
                    race_points = 0
                else:
                    points = calculate_points(position, is_sprint=False)
                    race_points = points
                
                # Calculate positions gained
                quali_pos = quali_positions.get(driver['DriverNumber'], position)
                positions_gained = quali_pos - position if position is not None else 0
                
                # Get driver color and nationality
                driver_color = driver.get('TeamColor', '#000000')
                nationality = DRIVER_NATIONALITIES.get(standardized_name, 'Unknown')
                
                # Create new record
                driver_data.append((
                    year, round_num, driver_name, standardized_name, team,
                    race_points,  # race points
                    0,  # total_points will be updated later
                    None if race_type == 'sprint' else position,  # position (main race)
                    driver.get('FastestLapTime', None), quali_pos, positions_gained,
                    driver.get('PitStops', 0), driver['DriverNumber'], driver_color,
                    nationality, race_type == 'sprint',
                    points if race_type == 'sprint' else 0,  # sprint points
                    position if race_type == 'sprint' else None  # sprint position
                ))
            except Exception as e:
                logger.error(f"Error processing driver {driver.get('FullName', 'Unknown')}: {str(e)}")
                continue
        
        # Process driver standings
        for driver in driver_data:
            try:
                # Check if record exists
                cursor.execute("""
                    SELECT COUNT(*) FROM driver_standings 
                    WHERE year = ? AND round = ? AND standardized_driver_name = ?
                """, (driver[0], driver[1], driver[3]))
                
                if cursor.fetchone()[0] > 0:
                    # Update existing record
                    if race_type == 'race':
                        cursor.execute('''
                            UPDATE driver_standings 
                            SET points = ?,
                                position = ?,
                                status = ?,
                                is_sprint = 0
                            WHERE year = ? AND round = ? AND standardized_driver_name = ?
                        ''', (driver[5], driver[7], driver[8], driver[0], driver[1], driver[3]))
                    else:  # sprint
                        cursor.execute('''
                            UPDATE driver_standings 
                            SET sprint_points = ?,
                                sprint_position = ?,
                                is_sprint = 1
                            WHERE year = ? AND round = ? AND standardized_driver_name = ?
                        ''', (driver[6], driver[7], driver[0], driver[1], driver[3]))
                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO driver_standings 
                        (year, round, driver_name, standardized_driver_name, team, points, total_points, position, 
                         fastest_lap_time, qualifying_position, positions_gained, pit_stops, driver_number, 
                         driver_color, nationality, is_sprint, sprint_points, sprint_position)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', driver)
            except Exception as e:
                logger.error(f"Error processing driver record: {str(e)}")
                continue
        
        # Process team standings
        team_data = {}
        for driver in session.results['DriverNumber']:
            result = session.results[session.results['DriverNumber'] == driver].iloc[0]
            team = result['TeamName']
            
            if team not in team_data:
                team_data[team] = {
                    'points': 0,
                    'sprint_points': 0,
                    'position': result['Position'],
                    'wins': 0,
                    'podiums': 0,
                    'fastest_laps': 0,
                    'color': result['TeamColor']
                }
            
            # Update team stats
            if result['Position'] == 1:
                team_data[team]['wins'] += 1
            if result['Position'] <= 3:
                team_data[team]['podiums'] += 1
            
            # Handle fastest lap points if available
            try:
                if result.get('FastestLap', False) and result.get('FastestLapRank', 0) == 1:
                    team_data[team]['fastest_laps'] += 1
                    if result['Position'] <= 10 and race_type == 'race':
                        team_data[team]['points'] += 1  # Extra point for fastest lap if in top 10
            except (KeyError, ValueError):
                pass  # Ignore if FastestLap data is not available
            
            # Calculate points based on race type
            if race_type == 'race':
                team_data[team]['points'] += calculate_points(result['Position'], is_sprint=False)
            else:  # sprint
                team_data[team]['sprint_points'] += calculate_points(result['Position'], is_sprint=True)
        
        # Process team standings
        for team, data in team_data.items():
            # Check if record exists
            cursor.execute("""
                SELECT COUNT(*) FROM constructors_standings 
                WHERE year = ? AND round = ? AND team = ?
            """, (year, round_num, team))
            
            if cursor.fetchone()[0] > 0:
                # Update existing record
                if race_type == 'race':
                    cursor.execute('''
                        UPDATE constructors_standings 
                        SET points = ?,
                            position = ?,
                            wins = ?,
                            podiums = ?,
                            fastest_laps = ?,
                            is_sprint = 0
                        WHERE year = ? AND round = ? AND team = ?
                    ''', (
                        data['points'],
                        data['position'],
                        data['wins'],
                        data['podiums'],
                        data['fastest_laps'],
                        year, round_num, team
                    ))
                else:  # sprint
                    cursor.execute('''
                        UPDATE constructors_standings 
                        SET sprint_points = ?,
                            sprint_position = ?,
                            is_sprint = 1
                        WHERE year = ? AND round = ? AND team = ?
                    ''', (
                        data['sprint_points'],
                        data['position'],
                        year, round_num, team
                    ))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO constructors_standings 
                    (year, round, team, points, sprint_points, position, wins, podiums,
                     fastest_laps, team_color, is_sprint, sprint_position)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    year, round_num, team,
                    data['points'] if race_type == 'race' else 0,
                    data['sprint_points'] if race_type == 'sprint' else 0,
                    data['position'],
                    data['wins'],
                    data['podiums'],
                    data['fastest_laps'],
                    data['color'],
                    1 if race_type == 'sprint' else 0,
                    data['position'] if race_type == 'sprint' else None
                ))
        
        # Update total points for both drivers and teams
        update_total_points(cursor, year)
        
        conn.commit()
        logger.info(f"Successfully processed {race_type} data for {year} Round {round_num}")
        
    except Exception as e:
        logger.error(f"Error processing {race_type} data for {year} Round {round_num}: {str(e)}")
        conn.rollback()
        raise

def validate_race_data(conn, year, round, race_type):
    """Validate that race data was processed correctly."""
    cursor = conn.cursor()
    
    if race_type == 'sprint':
        # Check if sprint data was properly recorded
        cursor.execute("""
            SELECT COUNT(*) FROM driver_standings 
            WHERE year = ? AND round = ? AND is_sprint = 1
        """, (year, round))
        
        sprint_records = cursor.fetchone()[0]
        if sprint_records == 0:
            logger.warning(f"No sprint records found for {year} Round {round}")
            
        # Check if sprint points were assigned
        cursor.execute("""
            SELECT COUNT(*) FROM driver_standings 
            WHERE year = ? AND round = ? AND sprint_points > 0
        """, (year, round))
        
        sprint_points = cursor.fetchone()[0]
        if sprint_points == 0:
            logger.warning(f"No sprint points assigned for {year} Round {round}")
    else:
        # Check if race data was properly recorded
        cursor.execute("""
            SELECT COUNT(*) FROM driver_standings 
            WHERE year = ? AND round = ? AND is_sprint = 0
        """, (year, round))
        
        race_records = cursor.fetchone()[0]
        if race_records == 0:
            logger.warning(f"No race records found for {year} Round {round}")
            
        # Check if race points were assigned
        cursor.execute("""
            SELECT COUNT(*) FROM driver_standings 
            WHERE year = ? AND round = ? AND points > 0
        """, (year, round))
        
        race_points = cursor.fetchone()[0]
        if race_points == 0:
            logger.warning(f"No race points assigned for {year} Round {round}")

def update_total_points(cursor, year):
    """Update total points for drivers and constructors.
    
    Args:
        cursor: Database cursor
        year: Year to update points for
    """
    try:
        # Update driver total points
        cursor.execute('''
            UPDATE driver_standings
            SET total_points = (
                SELECT SUM(COALESCE(points, 0) + COALESCE(sprint_points, 0))
                FROM driver_standings ds2
                WHERE ds2.year = driver_standings.year
                AND ds2.standardized_driver_name = driver_standings.standardized_driver_name
                AND ds2.round <= driver_standings.round
                AND ds2.year = ?
            )
            WHERE year = ?
        ''', (year, year))
        
        # Update constructor total points
        cursor.execute('''
            UPDATE constructors_standings
            SET total_points = (
                SELECT SUM(COALESCE(points, 0) + COALESCE(sprint_points, 0))
                FROM constructors_standings cs2
                WHERE cs2.year = constructors_standings.year
                AND cs2.team = constructors_standings.team
                AND cs2.round <= constructors_standings.round
                AND cs2.year = ?
            )
            WHERE year = ?
        ''', (year, year))
        
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
                (year, round, driver_name, standardized_driver_name, team, points, total_points, position,
                 fastest_lap_time, qualifying_position, qualifying_time, positions_gained,
                 pit_stops, driver_number, driver_color, nationality, is_sprint,
                 sprint_points, sprint_position, laps, status, grid_position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(year, round, standardized_driver_name) 
                DO UPDATE SET
                    qualifying_position = excluded.qualifying_position,
                    qualifying_time = excluded.qualifying_time,
                    nationality = excluded.nationality
            """, (
                year, round_num,
                driver_name, driver_name,  # Both driver_name and standardized_driver_name
                team,
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

def get_qualifying_positions(year, round):
    """Get qualifying positions for a specific race.
    
    Args:
        year (int): The year of the race
        round (int): The round number
        
    Returns:
        dict: Dictionary mapping driver numbers to their qualifying positions
    """
    try:
        session = fastf1.get_session(year, round, 'Q')
        session.load()
        
        positions = {}
        for _, driver in session.results.iterrows():
            driver_number = driver['DriverNumber']
            position = int(driver['Position']) if pd.notna(driver['Position']) else None
            positions[driver_number] = position
            
        return positions
    except Exception as e:
        logger.error(f"Error getting qualifying positions for {year} Round {round}: {str(e)}")
        return {}

def populate_2025_data():
    """Populate the database with 2025 F1 data."""
    try:
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
                is_sprint_race = event['EventFormat'] in ['sprint', 'sprint_qualifying']
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
                    is_sprint_race
                ))
                
                # Only process race data for races that have already happened
                if race_date > current_date:
                    logger.info(f"Skipping race data for Round {round_num} ({event['EventName']}) - Race hasn't happened yet (scheduled for {race_date})")
                    continue
                
                try:
                    # Process sprint race first if it exists
                    if is_sprint_race and sprint_date and sprint_date <= current_date:
                        logger.info(f"Loading sprint session for Round {round_num} ({event['EventName']})")
                        sprint_session = fastf1.get_session(2025, round_num, 'S')
                        if sprint_session:
                            logger.info("Sprint session found, loading data...")
                            sprint_session.load()
                            logger.info("Processing sprint race data...")
                            process_race_data(conn, 2025, round_num, 'sprint')
                            
                            # Validate and repair sprint data if needed
                            if not validate_and_repair_sprint_data(conn, 2025, round_num, event['EventName']):
                                logger.info("Issues found in sprint data, attempting to repair...")
                                repair_sprint_data(conn, 2025, round_num, event['EventName'])
                        else:
                            logger.warning("No sprint session found")
                    
                    # Process main race
                    logger.info(f"Loading main race session for Round {round_num} ({event['EventName']})")
                    race_session = fastf1.get_session(2025, round_num, 'R')
                    if race_session:
                        logger.info("Race session found, loading data...")
                        race_session.load()
                        logger.info("Processing main race data...")
                        process_race_data(conn, 2025, round_num, 'race')
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

def rebuild_database():
    """Drop and recreate the database with the new schema."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'f1_data.db')
        
        # Backup the old database if it exists
        if os.path.exists(db_path):
            backup_path = f"{db_path}.backup"
            shutil.copy2(db_path, backup_path)
            logger.info(f"Created backup of existing database at {backup_path}")
        
        # Remove the old database
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info("Removed old database")
        
        # Initialize the new database
        init_db(db_path)
        logger.info("Created new database with updated schema")
        
        return True
    except Exception as e:
        logger.error(f"Error rebuilding database: {str(e)}")
        return False

if __name__ == "__main__":
    # Rebuild the database with the new schema
    if rebuild_database():
        populate_2025_data()
    else:
        logger.error("Failed to rebuild database, exiting...") 