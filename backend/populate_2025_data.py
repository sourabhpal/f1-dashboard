import fastf1
import pandas as pd
import sqlite3
import logging
from datetime import datetime
import os
import time
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
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
        position INTEGER,
        fastest_lap_time TEXT,
        qualifying_position INTEGER,
        positions_gained INTEGER,
        pit_stops INTEGER,
        driver_number INTEGER,
        driver_color TEXT,
        PRIMARY KEY (year, round, driver_name)
    );

    CREATE TABLE IF NOT EXISTS constructors_standings (
        year INTEGER,
        round INTEGER,
        team TEXT,
        points INTEGER,
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

def init_db():
    """Initialize the database with required tables."""
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
                position INTEGER,
                fastest_lap_time TEXT,
                qualifying_position INTEGER,
                positions_gained INTEGER,
                pit_stops INTEGER,
                driver_number INTEGER,
                driver_color TEXT,
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

def populate_2025_data():
    """Populate the database with 2025 season data from FastF1 API."""
    # Check if rebuild is needed
    if not needs_rebuild():
        logger.info("Database is up to date, no rebuild needed")
        return
        
    logger.info("Database needs to be rebuilt")
    
    # Delete existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info("Removed existing database")
    
    year = 2025
    current_date = datetime.now()
    
    # Initialize database first
    init_db()
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Fetch schedule from FastF1
        logger.info("Fetching 2025 schedule from FastF1...")
        schedule = fastf1.get_event_schedule(year)
        logger.info(f"Schedule data: {schedule}")
        
        # Process each event in the schedule
        for _, event in schedule.iterrows():
            round_num = event['RoundNumber']
            logger.info(f"Processing round {round_num}")
            
            # Skip testing events (round 0)
            if round_num == 0:
                continue
                
            # Get event details
            event_name = event['EventName']
            circuit_name = event['CircuitName'] if 'CircuitName' in event else event['EventName']
            location = event['Location'] if 'Location' in event else ''
            country = event['Country']
            event_date = pd.to_datetime(event['EventDate']).strftime('%Y-%m-%d') if pd.notna(event['EventDate']) else None
            event_format = event['EventFormat'] if 'EventFormat' in event else 'conventional'
            
            logger.info(f"Event details: name={event_name}, date={event_date}, country={country}")
            
            # Insert into race_schedule
            cursor.execute("""
                INSERT OR REPLACE INTO race_schedule 
                (year, round, name, date, event, country)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (year, round_num, event_name, event_date, event_name, country))
            
            # Check if race has been completed
            if event_date:
                race_date = datetime.strptime(event_date, '%Y-%m-%d')
                if race_date > current_date:
                    logger.info(f"Skipping {event_name} as it hasn't been completed yet")
                    continue
            
            # Get detailed event information
            try:
                event_obj = fastf1.get_event(year, round_num)
                logger.info(f"Event object: {event_obj}")
                
                # Get circuit information
                circuit_data = {
                    'year': year,
                    'round': round_num,
                    'circuit_name': circuit_name,
                    'location': location,
                    'country': country,
                    'circuit_length': getattr(event_obj, 'CircuitLength', 0.0),
                    'number_of_laps': getattr(event_obj, 'NumberOfLaps', 0),
                    'first_grand_prix': getattr(event_obj, 'FirstGrandPrix', 0),
                    'lap_record': getattr(event_obj, 'LapRecord', 'N/A'),
                    'track_map': getattr(event_obj, 'TrackMap', 'N/A')
                }
                
                logger.info(f"Circuit data: {circuit_data}")
                
                cursor.execute("""
                    INSERT OR REPLACE INTO circuits 
                    (year, round, circuit_name, location, country, circuit_length, 
                    number_of_laps, first_grand_prix, lap_record, track_map)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    circuit_data['year'], circuit_data['round'], circuit_data['circuit_name'],
                    circuit_data['location'], circuit_data['country'], circuit_data['circuit_length'],
                    circuit_data['number_of_laps'], circuit_data['first_grand_prix'],
                    circuit_data['lap_record'], circuit_data['track_map']
                ))
                
                # Try to get race results if available
                try:
                    session = fastf1.get_session(year, round_num, 'R')
                    session.load()
                    logger.info(f"Race session results: {session.results}")
                    
                    if session.results is not None:
                        # Calculate constructors standings for this race
                        team_points = {}
                        team_wins = {}
                        team_podiums = {}
                        team_fastest_laps = {}
                        team_colors = {}
                        
                        for _, driver in session.results.iterrows():
                            team = driver['TeamName']
                            points = driver['Points']
                            position = driver['Position']
                            team_color = driver['TeamColor']
                            
                            logger.info(f"Driver result: team={team}, points={points}, position={position}")
                            
                            # Initialize team stats if not exists
                            if team not in team_points:
                                team_points[team] = 0
                                team_wins[team] = 0
                                team_podiums[team] = 0
                                team_fastest_laps[team] = 0
                                team_colors[team] = team_color
                            
                            # Update team stats
                            team_points[team] += points
                            if position == 1:
                                team_wins[team] += 1
                            if position <= 3:
                                team_podiums[team] += 1
                            if driver.get('FastestLap', False):
                                team_fastest_laps[team] += 1
                        
                        logger.info(f"Team stats: {team_points}")
                        
                        # Store constructors standings
                        for team in team_points:
                            cursor.execute("""
                                INSERT OR REPLACE INTO constructors_standings 
                                (year, round, team, points, position, wins, podiums, 
                                fastest_laps, team_color)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                year, round_num, team, team_points[team],
                                len([t for t in team_points if team_points[t] > team_points[team]]) + 1,
                                team_wins[team], team_podiums[team], team_fastest_laps[team],
                                f"#{team_colors[team]}" if pd.notna(team_colors[team]) and not str(team_colors[team]).startswith('#') else str(team_colors[team])
                            ))
                        
                        # Store driver standings
                        for _, driver in session.results.iterrows():
                            # Get qualifying position
                            quali_pos = None
                            try:
                                quali = fastf1.get_session(year, round_num, 'Q')
                                quali.load()
                                quali_result = quali.results[quali.results['DriverNumber'] == driver['DriverNumber']]
                                if not quali_result.empty:
                                    quali_pos = quali_result.iloc[0]['Position']
                            except:
                                quali_pos = 0
                            
                            # Calculate positions gained
                            positions_gained = (quali_pos or 0) - driver['Position'] if quali_pos else 0
                            
                            # Get pit stops
                            try:
                                pit_stops = len(session.laps.pick_driver(driver['DriverNumber']).get_car_data()['Brake'])
                            except:
                                pit_stops = 0
                            
                            cursor.execute("""
                                INSERT OR REPLACE INTO driver_standings 
                                (year, round, driver_name, team, points, position, 
                                fastest_lap_time, qualifying_position, positions_gained, pit_stops,
                                driver_number, driver_color)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                year, round_num, driver['FullName'], driver['TeamName'],
                                driver['Points'], driver['Position'],
                                str(driver.get('FastestLap', 'N/A')),
                                quali_pos or 0, positions_gained, pit_stops,
                                driver['DriverNumber'],
                                f"#{driver['TeamColor']}" if pd.notna(driver['TeamColor']) and not str(driver['TeamColor']).startswith('#') else str(driver['TeamColor'])
                            ))
                except Exception as e:
                    logger.warning(f"Could not fetch race results for round {round_num}: {str(e)}")
                    
            except Exception as e:
                logger.warning(f"Error processing event {event_name}: {str(e)}")
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        conn.commit()
        logger.info("Successfully populated all 2025 data from FastF1")
        
    except Exception as e:
        logger.error(f"Error populating 2025 data: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_2025_data() 