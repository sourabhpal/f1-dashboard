import fastf1
import pandas as pd
import sqlite3
import logging
from datetime import datetime
import os
import time
import hashlib
import numpy as np

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
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def populate_historical_data():
    """Populate race data for years 2020-2024."""
    try:
        # Initialize database
        init_db()
        
        # Years to populate
        years = range(2020, 2025)
        
        for year in years:
            logger.info(f"Processing year {year}")
            
            # Get race schedule
            schedule = fastf1.get_event_schedule(year)
            
            for _, race in schedule.iterrows():
                round_num = race['RoundNumber']
                logger.info(f"Processing {year} Round {round_num}: {race['EventName']}")
                
                try:
                    # Load race session
                    session = fastf1.get_session(year, round_num, 'R')
                    session.load(weather=False, messages=False, laps=True)
                    
                    # Get race info
                    race_info = {
                        'year': year,
                        'round': round_num,
                        'name': race['EventName'],
                        'date': race['EventDate'].strftime('%Y-%m-%d'),
                        'event': race['EventFormat'],
                        'country': race['Country']
                    }
                    
                    # Store race schedule
                    with db_lock:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT OR REPLACE INTO race_schedule 
                                (year, round, name, date, event, country)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                race_info['year'], race_info['round'],
                                race_info['name'], race_info['date'],
                                race_info['event'], race_info['country']
                            ))
                    
                    # Get results
                    results = session.results
                    
                    # Get fastest laps for each driver
                    fastest_laps = {}
                    for driver in session.drivers:
                        driver_laps = session.laps.pick_drivers(driver)
                        fastest_lap = driver_laps['LapTime'].min()
                        if pd.notnull(fastest_lap):
                            fastest_laps[driver] = str(fastest_lap)
                    
                    # Store driver standings
                    with db_lock:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            for _, result in results.iterrows():
                                driver = result['DriverNumber']
                                driver_info = session.get_driver(driver)
                                
                                # Get team color
                                team_color = driver_info.get('TeamColor', '#ff0000')
                                if team_color and not team_color.startswith('#'):
                                    team_color = f'#{team_color}'
                                
                                # Get grid position
                                grid_position = driver_info.get('GridPosition', result['Position'])
                                
                                # Calculate positions gained
                                positions_gained = grid_position - result['Position']
                                
                                # Get pit stops
                                pit_data = session.pits
                                pit_stops = len(pit_data[pit_data['Driver'] == driver]) if pit_data is not None else 0
                                
                                # Get fastest lap
                                fastest_lap = fastest_laps.get(driver, 'N/A')
                                
                                cursor.execute("""
                                    INSERT OR REPLACE INTO driver_standings 
                                    (year, round, position, driver_name, team, points,
                                     driver_color, driver_number, fastest_lap_time,
                                     qualifying_position, positions_gained, pit_stops,
                                     laps, status, grid_position)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    year, round_num, result['Position'],
                                    f"{driver_info['FirstName']} {driver_info['LastName']}",
                                    driver_info['TeamName'], result['Points'],
                                    team_color, driver, fastest_lap,
                                    grid_position, positions_gained, pit_stops,
                                    len(session.laps.pick_drivers(driver)),
                                    driver_info['Status'], grid_position
                                ))
                    
                    logger.info(f"Successfully processed {year} Round {round_num}")
                    
                except Exception as e:
                    logger.error(f"Error processing {year} Round {round_num}: {str(e)}")
                    continue
        
        logger.info("Historical data population completed")
        
    except Exception as e:
        logger.error(f"Error populating historical data: {str(e)}")
        raise

if __name__ == "__main__":
    populate_historical_data() 