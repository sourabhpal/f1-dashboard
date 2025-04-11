import fastf1
import pandas as pd
import sqlite3
import logging
from datetime import datetime
import os
import time
import hashlib
import numpy as np
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up FastF1 cache
cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# Database configuration
DB_PATH = os.getenv('DB_PATH', '/app/data/f1_data.db')

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
        nationality TEXT,
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
    conn = sqlite3.connect(DB_PATH)
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
        raise
    finally:
        conn.close()

def get_db_connection():
    """Get a database connection with proper configuration."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def populate_historical_data(year):
    """Populate race data for the specified year."""
    try:
        # Initialize database
        init_db()
        
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
                    conn.commit()
                
                # Get results
                results = session.results
                
                # Get fastest laps for each driver
                fastest_laps = {}
                try:
                    for driver in session.drivers:
                        driver_laps = session.laps.pick_drivers(driver)
                        fastest_lap = driver_laps['LapTime'].min()
                        if pd.notnull(fastest_lap):
                            fastest_laps[driver] = str(fastest_lap)
                except Exception as e:
                    logger.warning(f"Error getting fastest laps for {year} Round {round_num}: {str(e)}")
                    # If we can't get fastest laps, we'll use a fallback approach
                    try:
                        # Try to get fastest lap from results
                        for _, result in results.iterrows():
                            driver = result['DriverNumber']
                            if 'FastestLap' in result and result['FastestLap']:
                                # If this driver had the fastest lap, use a placeholder
                                fastest_laps[driver] = "Fastest Lap"
                    except Exception as e2:
                        logger.warning(f"Error with fallback fastest lap approach: {str(e2)}")
                
                # Store driver standings
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
                        
                        # Get fastest lap time with fallback
                        fastest_lap_time = fastest_laps.get(driver, '')
                        if not fastest_lap_time and 'FastestLap' in result and result['FastestLap']:
                            fastest_lap_time = "Fastest Lap"
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO driver_standings 
                            (year, round, driver_name, team, points, position, 
                             fastest_lap_time, qualifying_position, positions_gained, 
                             pit_stops, driver_number, driver_color, nationality)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            year, round_num,
                            driver_info['FullName'],
                            driver_info['TeamName'],
                            result['Points'],
                            result['Position'],
                            fastest_lap_time,
                            grid_position,
                            positions_gained,
                            result.get('NumberOfPitStops', 0),
                            driver,
                            team_color,
                            driver_info.get('Nationality', 'Unknown')
                        ))
                    conn.commit()
                
                # Store constructor standings
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    for team in session.results['TeamName'].unique():
                        team_results = session.results[session.results['TeamName'] == team]
                        team_points = team_results['Points'].sum()
                        team_position = len(team_results[team_results['Points'] > team_points]) + 1
                        
                        # Count fastest laps with fallback
                        fastest_laps_count = 0
                        try:
                            fastest_laps_count = len(team_results[team_results['FastestLap'] == True])
                        except Exception as e:
                            logger.warning(f"Error counting fastest laps for team {team}: {str(e)}")
                            # If we can't count fastest laps, use a reasonable default
                            fastest_laps_count = 1 if team_points > 0 else 0
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO constructors_standings 
                            (year, round, team, points, position, wins, podiums, 
                             fastest_laps, team_color)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            year, round_num,
                            team,
                            team_points,
                            team_position,
                            len(team_results[team_results['Position'] == 1]),
                            len(team_results[team_results['Position'].isin([1, 2, 3])]),
                            fastest_laps_count,
                            team_results.iloc[0].get('TeamColor', '#ff0000')
                        ))
                    conn.commit()
                
                logger.info(f"Successfully processed {year} Round {round_num}")
                
            except Exception as e:
                logger.error(f"Error processing {year} Round {round_num}: {str(e)}")
                continue
        
        logger.info(f"Successfully completed processing for year {year}")
        
    except Exception as e:
        logger.error(f"Error processing year {year}: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Populate F1 historical data for a specific year')
    parser.add_argument('year', type=int, help='Year to populate (2020-2025)')
    args = parser.parse_args()

    # Validate year
    if args.year < 2020 or args.year > 2025:
        logger.error("Year must be between 2020 and 2025")
        sys.exit(1)

    try:
        populate_historical_data(args.year)
        logger.info("Data population completed successfully")
    except Exception as e:
        logger.error(f"Failed to populate data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 