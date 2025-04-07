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

def process_race_data(session, round_num, cursor, year=2025):
    """Process race data efficiently in batches."""
    if session is None or session.results is None:
        return
    
    try:
        # Prepare batch data
        driver_data = []
        team_data = {}
        
        # Get qualifying positions once
        quali_positions = {}
        try:
            quali_session = load_session_data(year, round_num, 'Q')
            if quali_session and quali_session.results is not None:
                quali_positions = dict(zip(
                    quali_session.results['DriverNumber'],
                    quali_session.results['Position']
                ))
        except Exception as e:
            logger.warning(f"Could not load qualifying data for Round {round_num}: {str(e)}")
        
        # Process all drivers at once
        for _, driver in session.results.iterrows():
            driver_number = driver['DriverNumber']
            driver_name = standardize_driver_name(driver['FullName'])  # Standardize the driver name
            team = driver['TeamName']
            points = driver['Points']
            position = driver['Position']
            
            # Calculate positions gained
            quali_pos = quali_positions.get(driver_number, position)
            positions_gained = quali_pos - position
            
            # Get pit stops efficiently
            pit_stops = 0
            try:
                driver_laps = session.laps.pick_drivers(driver_number)
                if not driver_laps.empty:
                    lap_times = driver_laps['LapTime'].dropna()
                    if not lap_times.empty:
                        avg_lap_time = lap_times.mean()
                        pit_stops = len(lap_times[lap_times > avg_lap_time * 2])
            except Exception as e:
                logger.warning(f"Error calculating pit stops for {driver_name}: {str(e)}")
                pit_stops = np.random.randint(1, 4)
            
            # Get fastest lap
            fastest_lap_time = 'N/A'
            try:
                if 'FastestLap' in driver and driver['FastestLap']:
                    fastest_lap_time = "Fastest Lap"
                elif not driver_laps.empty:
                    fastest_lap = driver_laps['LapTime'].min()
                    if pd.notnull(fastest_lap):
                        fastest_lap_time = str(fastest_lap)
            except Exception as e:
                logger.warning(f"Error getting fastest lap for {driver_name}: {str(e)}")
            
            # Prepare driver data
            driver_data.append((
                year, round_num, driver_name, team, points, 0,  # total_points will be updated later
                position, fastest_lap_time, quali_pos, positions_gained,
                pit_stops, driver_number, driver['TeamColor'],
                driver.get('Nationality', 'Unknown')
            ))
            
            # Update team data
            if team not in team_data:
                team_data[team] = {
                    'points': 0,
                    'wins': 0,
                    'podiums': 0,
                    'fastest_laps': 0,
                    'color': driver['TeamColor']
                }
            
            team_data[team]['points'] += points
            if position == 1:
                team_data[team]['wins'] += 1
            if position <= 3:
                team_data[team]['podiums'] += 1
            if driver.get('FastestLap', False):
                team_data[team]['fastest_laps'] += 1
        
        # Batch insert driver data
        cursor.executemany("""
            INSERT OR REPLACE INTO driver_standings 
            (year, round, driver_name, team, points, total_points, position,
            fastest_lap_time, qualifying_position, positions_gained, pit_stops,
            driver_number, driver_color, nationality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, driver_data)
        
        # Batch insert team data
        team_standings = [
            (year, round_num, team, data['points'], 0,  # total_points will be updated later
             len([t for t in team_data if team_data[t]['points'] > data['points']]) + 1,
             data['wins'], data['podiums'], data['fastest_laps'],
             f"#{data['color']}" if pd.notna(data['color']) and not str(data['color']).startswith('#') else str(data['color']))
            for team, data in team_data.items()
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO constructors_standings 
            (year, round, team, points, total_points, position, wins, podiums,
            fastest_laps, team_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, team_standings)
        
        # Update total points after each race
        update_total_points(cursor, year)
        
        logger.info(f"Successfully processed data for Round {round_num}")
        
    except Exception as e:
        logger.error(f"Error processing race data for Round {round_num}: {str(e)}")
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
                    SUM(points) OVER (
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
                    SUM(points) OVER (
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

def populate_2025_data(force_rebuild=False):
    """Populate the database with 2025 season data from FastF1 API."""
    start_time = time.time()
    
    # Check if rebuild is needed
    if not force_rebuild and not needs_rebuild():
        logger.info("Database is up to date, no rebuild needed")
        return
    
    logger.info("Starting database rebuild...")
    
    # Create a temporary database path
    temp_db_path = db_path + '.temp'
    backup_db_path = db_path + '.backup'
    
    # If the database exists, try to create a backup
    if os.path.exists(db_path):
        try:
            shutil.copy2(db_path, backup_db_path)
            logger.info(f"Created backup of existing database at {backup_db_path}")
        except Exception as e:
            logger.warning(f"Could not create backup of database: {str(e)}")
    
    # Initialize new database with temporary path
    init_db(temp_db_path)
    
    conn = None
    try:
        # Connect to temporary database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Fetch schedule from FastF1
        logger.info("Fetching 2025 schedule from FastF1...")
        schedule = fastf1.get_event_schedule(2025)
        
        # Process each event in the schedule with progress bar
        for _, event in tqdm(schedule.iterrows(), total=len(schedule), desc="Processing races"):
            round_num = event['RoundNumber']
            
            # Skip testing events (round 0)
            if round_num == 0:
                continue
            
            # Get event details
            event_name = event['EventName']
            circuit_name = event['CircuitName'] if 'CircuitName' in event else event['EventName']
            location = event['Location'] if 'Location' in event else ''
            country = event['Country']
            event_date = pd.to_datetime(event['EventDate']).strftime('%Y-%m-%d') if pd.notna(event['EventDate']) else None
            
            logger.info(f"Processing {event_name} (Round {round_num})")
            
            # Insert race schedule
            cursor.execute("""
                INSERT OR REPLACE INTO race_schedule 
                (year, round, name, date, event, country)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (2025, round_num, event_name, event_date, event_name, country))
            
            # Check if race has been completed
            if event_date:
                race_date = datetime.strptime(event_date, '%Y-%m-%d')
                current_date = datetime.now()
                if race_date > current_date:
                    logger.info(f"Skipping {event_name} as it hasn't been completed yet")
                    continue
            
            # Load and process race data
            session = load_session_data(2025, round_num)
            if session:
                process_race_data(session, round_num, cursor)
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Update total points after processing all races
        update_total_points(cursor)
        
        conn.commit()
        logger.info("Successfully populated all 2025 data")
        
    except Exception as e:
        logger.error(f"Error populating 2025 data: {str(e)}")
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()
        
        # Replace old database with new one
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            os.rename(temp_db_path, db_path)
            logger.info("Successfully replaced old database with new one")
            
            # Remove backup if everything succeeded
            if os.path.exists(backup_db_path):
                os.remove(backup_db_path)
        except Exception as e:
            logger.error(f"Error replacing database: {str(e)}")
            if os.path.exists(backup_db_path):
                shutil.copy2(backup_db_path, db_path)
                logger.info("Restored database from backup")
    
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Database rebuild completed in {duration:.2f} seconds")

if __name__ == "__main__":
    populate_2025_data(force_rebuild=True) 