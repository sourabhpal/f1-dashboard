import fastf1
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import threading
import contextlib
import os
import logging
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure FastF1 cache
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'f1_data.db')

# Global lock for database access
db_lock = threading.Lock()

def init_db():
    """Initialize the database with proper schema and settings."""
    with db_lock:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        try:
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA temp_store=MEMORY')
            conn.execute('PRAGMA mmap_size=30000000000')
            conn.execute('PRAGMA page_size=4096')
            
            # Create tables if they don't exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS driver_standings (
                    year INTEGER,
                    round INTEGER,
                    position INTEGER,
                    driver_name TEXT,
                    team TEXT,
                    points REAL,
                    driver_color TEXT,
                    driver_number INTEGER,
                    fastest_lap_time TEXT,
                    qualifying_position INTEGER,
                    positions_gained INTEGER,
                    pit_stops INTEGER,
                    PRIMARY KEY (year, round, driver_name)
                )
            ''')
            
            # Create race schedule table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS race_schedule (
                    year INTEGER,
                    round INTEGER,
                    name TEXT,
                    date TEXT,
                    event TEXT,
                    country TEXT,
                    PRIMARY KEY (year, round)
                )
            ''')
            
            # Create circuits table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS circuits (
                    year INTEGER,
                    round INTEGER,
                    name TEXT,
                    country TEXT,
                    event TEXT,
                    first_grand_prix TEXT,
                    circuit_length REAL,
                    number_of_laps INTEGER,
                    race_distance REAL,
                    lap_record TEXT,
                    drs_zones TEXT,
                    track_type TEXT,
                    track_map TEXT,
                    PRIMARY KEY (year, round)
                )
            """)
            
            # Create race positions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS race_positions (
                    year INTEGER,
                    round INTEGER,
                    driver_abbr TEXT,
                    positions TEXT,
                    lap_numbers TEXT,
                    color TEXT,
                    driver_name TEXT,
                    team TEXT,
                    PRIMARY KEY (year, round, driver_abbr)
                )
            ''')
            
            # Add indexes for better query performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_driver_standings_year_round ON driver_standings(year, round)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_driver_standings_driver ON driver_standings(driver_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_driver_standings_team ON driver_standings(team)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_driver_standings_position ON driver_standings(position)')
            
            conn.execute('CREATE INDEX IF NOT EXISTS idx_race_schedule_year ON race_schedule(year)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_race_schedule_date ON race_schedule(date)')
            
            conn.execute('CREATE INDEX IF NOT EXISTS idx_circuits_year ON circuits(year)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_circuits_country ON circuits(country)')
            
            # Check if new columns exist, if not add them
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(driver_standings)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'fastest_lap_time' not in columns:
                logger.info("Adding fastest_lap_time column to driver_standings table")
                conn.execute('ALTER TABLE driver_standings ADD COLUMN fastest_lap_time TEXT')
            
            if 'qualifying_position' not in columns:
                logger.info("Adding qualifying_position column to driver_standings table")
                conn.execute('ALTER TABLE driver_standings ADD COLUMN qualifying_position INTEGER')
            
            if 'positions_gained' not in columns:
                logger.info("Adding positions_gained column to driver_standings table")
                conn.execute('ALTER TABLE driver_standings ADD COLUMN positions_gained INTEGER')
            
            if 'pit_stops' not in columns:
                logger.info("Adding pit_stops column to driver_standings table")
                conn.execute('ALTER TABLE driver_standings ADD COLUMN pit_stops INTEGER')
            
            # Add index for race positions
            conn.execute('CREATE INDEX IF NOT EXISTS idx_race_positions_year_round ON race_positions(year, round)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_race_positions_driver ON race_positions(driver_abbr)')
            
            conn.commit()
        finally:
            conn.close()

# Initialize database on startup
init_db()

@contextlib.contextmanager
def get_db_connection():
    """Get a database connection with proper thread safety."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

@app.get("/available-years")
async def get_available_years():
    """Get list of available years in the database."""
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT year FROM driver_standings ORDER BY year DESC")
            years = [row[0] for row in cursor.fetchall()]
            
            # If no years in database, fetch from FastF1
            if not years:
                try:
                    current_year = 2025  # Set current year to 2025
                    years = list(range(1950, current_year + 1))  # F1 started in 1950
                    # Filter out years that don't have data
                    valid_years = []
                    for year in years:
                        try:
                            schedule = fastf1.get_event_schedule(year)
                            if not schedule.empty:
                                valid_years.append(year)
                                logger.info(f"Found valid data for year {year}")
                        except Exception as e:
                            logger.warning(f"Error checking year {year}: {str(e)}")
                            continue
                    
                    if valid_years:
                        # Cache the valid years in the database
                        for year in valid_years:
                            cursor.execute("""
                                INSERT INTO driver_standings (year, round, position, driver_name, team, points, driver_color, driver_number)
                                VALUES (?, 0, 0, 'CACHE', 'CACHE', 0, '#ff0000', 0)
                            """, (year,))
                        conn.commit()
                        years = valid_years
                    else:
                        logger.warning("No valid years found, using fallback years")
                        years = [2025, 2024, 2023, 2022]  # Fallback to recent years
                except Exception as e:
                    logger.error(f"Error fetching available years: {str(e)}")
                    years = [2025, 2024, 2023, 2022]  # Fallback to recent years
            
            logger.info(f"Returning available years: {years}")
            return {"years": years}

@app.get("/standings/{year}")
async def get_standings(year: int):
    """Get driver standings for a specific year."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                # Get the latest round for the year
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MAX(round) FROM driver_standings WHERE year = ?
                """, (year,))
                latest_round = cursor.fetchone()[0]
                
                if latest_round is None or latest_round == 0:  # 0 indicates cached year
                    # If no data exists, fetch from FastF1
                    logger.info(f"Fetching standings for year {year} from FastF1")
                    
                    # For 2025, try to fetch from FastF1 first
                    if year == 2025:
                        try:
                            schedule = fastf1.get_event_schedule(year)
                            if not schedule.empty:
                                # Get all races for the year
                                all_standings = []
                                for _, race in schedule.iterrows():
                                    round_num = race['RoundNumber']
                                    try:
                                        # Load the race session
                                        session = fastf1.get_session(year, round_num, 'R')
                                        session.load()
                                        
                                        # Get driver standings with proper column mapping
                                        results = session.results
                                        logger.info(f"Processing race {round_num} for year {year}")
                                        
                                        # Format team colors to include '#' prefix
                                        team_colors = results['TeamColor'].apply(lambda x: f"#{x}" if pd.notna(x) and not str(x).startswith('#') else x)
                                        
                                        # Get fastest lap times
                                        fastest_laps = session.laps.groupby('Driver')['LapTime'].min()
                                        
                                        # Get qualifying positions
                                        try:
                                            quali_session = fastf1.get_session(year, round_num, 'Q')
                                            quali_session.load()
                                            quali_results = quali_session.results
                                            quali_positions = dict(zip(quali_results['DriverNumber'], quali_results['Position']))
                                        except Exception as e:
                                            logger.warning(f"Error fetching qualifying positions for round {round_num}: {str(e)}")
                                            quali_positions = {}
                                        
                                        # Calculate positions gained
                                        positions_gained = {}
                                        for driver in results['DriverNumber']:
                                            quali_pos = quali_positions.get(driver, 20)  # Default to last if no quali position
                                            race_pos = results[results['DriverNumber'] == driver]['Position'].iloc[0]
                                            positions_gained[driver] = quali_pos - race_pos
                                        
                                        # Get pit stops
                                        try:
                                            pit_data = session.pits
                                            pit_stops = pit_data.groupby('DriverNumber').size()
                                        except Exception as e:
                                            logger.warning(f"Error fetching pit stops for round {round_num}: {str(e)}")
                                            pit_stops = {}
                                        
                                        standings = pd.DataFrame({
                                            'position': results['Position'],
                                            'driver_name': results['FullName'],
                                            'team': results['TeamName'],
                                            'points': results['Points'],
                                            'driver_color': team_colors.fillna('#ff0000'),
                                            'driver_number': results['DriverNumber'],
                                            'fastest_lap_time': results['DriverNumber'].map(lambda x: str(fastest_laps.get(x, 'N/A'))),
                                            'qualifying_position': results['DriverNumber'].map(lambda x: quali_positions.get(x, 20)),
                                            'positions_gained': results['DriverNumber'].map(lambda x: positions_gained.get(x, 0)),
                                            'pit_stops': results['DriverNumber'].map(lambda x: pit_stops.get(x, 0))
                                        })
                                        
                                        # Store in database
                                        for _, row in standings.iterrows():
                                            cursor.execute("""
                                                INSERT INTO driver_standings (
                                                    year, round, position, driver_name, team, points,
                                                    driver_color, driver_number, fastest_lap_time,
                                                    qualifying_position, positions_gained, pit_stops
                                                )
                                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                            """, (
                                                year, round_num, row['position'], row['driver_name'],
                                                row['team'], row['points'], row['driver_color'],
                                                row['driver_number'], row['fastest_lap_time'],
                                                row['qualifying_position'], row['positions_gained'],
                                                row['pit_stops']
                                            ))
                                        
                                        all_standings.append(standings)
                                        logger.info(f"Successfully processed race {round_num} for year {year}")
                                    except Exception as e:
                                        logger.warning(f"Error processing race {round_num} for year {year}: {str(e)}")
                                        continue
                                
                                conn.commit()
                                
                                if all_standings:
                                    # Calculate final standings by summing points for each driver
                                    final_standings = pd.concat(all_standings).groupby(['driver_number', 'team', 'driver_color'])['points'].sum().reset_index()
                                    
                                    # Get the most common driver name for each driver number
                                    driver_names = pd.concat(all_standings).groupby('driver_number')['driver_name'].agg(lambda x: x.mode().iloc[0]).reset_index()
                                    final_standings = final_standings.merge(driver_names, on='driver_number')
                                    
                                    final_standings['position'] = final_standings['points'].rank(ascending=False, method='min').astype(int)
                                    final_standings = final_standings.sort_values('position')
                                    
                                    logger.info(f"Successfully calculated final standings for year {year}")
                                    return final_standings.to_dict(orient='records')
                        except Exception as e:
                            logger.warning(f"Error fetching 2025 data from FastF1: {str(e)}")
                    
                    # If FastF1 fails or no data available, use database data
                    logger.info(f"Using database data for year {year}")
                    cursor.execute("""
                        WITH final_points AS (
                            SELECT DISTINCT 
                                driver_number,
                                team,
                                driver_color,
                                SUM(points) as total_points,
                                MAX(driver_name) as driver_name
                            FROM driver_standings
                            WHERE year = ? AND round > 0
                            GROUP BY driver_number, team, driver_color
                        )
                        SELECT 
                            ROW_NUMBER() OVER (ORDER BY total_points DESC) as position,
                            driver_name,
                            team,
                            total_points as points,
                            driver_color,
                            driver_number
                        FROM final_points
                        ORDER BY total_points DESC
                    """, (year,))
                    
                    columns = ['position', 'driver_name', 'team', 'points', 'driver_color', 'driver_number']
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    logger.info(f"Found {len(results)} drivers in standings for year {year}")
                    return results
                
                # If data exists, return from database
                logger.info(f"Fetching standings for year {year} from database")
                cursor.execute("""
                    WITH final_points AS (
                        SELECT DISTINCT 
                            driver_number,
                            team,
                            driver_color,
                            SUM(points) as total_points,
                            MAX(driver_name) as driver_name
                        FROM driver_standings
                        WHERE year = ? AND round > 0
                        GROUP BY driver_number, team, driver_color
                    )
                    SELECT 
                        ROW_NUMBER() OVER (ORDER BY total_points DESC) as position,
                        driver_name,
                        team,
                        total_points as points,
                        driver_color,
                        driver_number
                    FROM final_points
                    ORDER BY total_points DESC
                """, (year,))
                
                columns = ['position', 'driver_name', 'team', 'points', 'driver_color', 'driver_number']
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                logger.info(f"Found {len(results)} drivers in standings for year {year}")
                return results
                
    except Exception as e:
        logger.error(f"Error fetching standings for year {year}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{year}")
async def get_team_standings(year: int):
    """Get team standings for a specific year."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT team, SUM(points) as total_points, MAX(driver_color) as team_color
                    FROM driver_standings
                    WHERE year = ?
                    GROUP BY team
                    ORDER BY total_points DESC
                """, (year,))
                
                return [{"team": row[0], "points": row[1], "team_color": row[2]} for row in cursor.fetchall()]
                
    except Exception as e:
        logger.error(f"Error fetching team standings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule/{year}")
async def get_schedule(year: int):
    """Get race schedule for a specific year."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # First try to get from database
                cursor.execute("""
                    SELECT round, name, date, event, country
                    FROM race_schedule
                    WHERE year = ?
                    ORDER BY round
                """, (year,))
                
                events = cursor.fetchall()
                
                if not events:
                    logger.info(f"No schedule found in database for year {year}, fetching from FastF1")
                    try:
                        # Try to fetch from FastF1
                        schedule = fastf1.get_event_schedule(year)
                        if schedule.empty:
                            raise HTTPException(status_code=404, detail=f"No races found for year {year}")
                        
                        # Convert schedule to list of events
                        events = []
                        for _, event in schedule.iterrows():
                            try:
                                # Get the event details
                                event_details = fastf1.get_event(year, event['RoundNumber'])
                                logger.info(f"Event details for round {event['RoundNumber']}: {event_details}")
                                
                                # Handle different possible column names and get event information
                                round_number = event.get('RoundNumber', event.get('Round', 0))
                                event_name = event.get('EventName', event.get('Name', 'Unknown'))
                                official_event_name = event_details.get('OfficialEventName', event_name)
                                event_date = event.get('EventDate', event.get('Date'))
                                country = event_details.get('Country', 'Unknown')
                                
                                # Format date if it exists
                                if pd.notna(event_date):
                                    # Convert to datetime without timezone
                                    race_date = pd.to_datetime(event_date).tz_localize(None)
                                    date_str = race_date.strftime('%Y-%m-%d')
                                else:
                                    date_str = 'Unknown'
                                
                                # Store in database
                                cursor.execute("""
                                    INSERT INTO race_schedule (year, round, name, date, event, country)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (year, round_number, event_name, date_str, official_event_name, country))
                                
                                events.append({
                                    "round": int(round_number),
                                    "name": str(event_name),
                                    "date": date_str,
                                    "event": str(official_event_name),
                                    "country": str(country)
                                })
                                
                                logger.info(f"Processed event: Round {round_number}, Event: {official_event_name}")
                            except Exception as e:
                                logger.warning(f"Error processing event data: {str(e)}")
                                continue
                        
                        conn.commit()
                        
                    except Exception as e:
                        logger.error(f"Error fetching from FastF1: {str(e)}")
                        # If FastF1 fails, use fallback data for 2025
                        if year == 2025:
                            logger.info("Using fallback data for 2025 season")
                            fallback_events = [
                                {
                                    "round": 1,
                                    "name": "Australian Grand Prix",
                                    "date": "2025-03-16",
                                    "event": "Formula 1 Australian Grand Prix 2025",
                                    "country": "Australia"
                                },
                                {
                                    "round": 2,
                                    "name": "Chinese Grand Prix",
                                    "date": "2025-03-23",
                                    "event": "Formula 1 Chinese Grand Prix 2025",
                                    "country": "China"
                                },
                                {
                                    "round": 3,
                                    "name": "Japanese Grand Prix",
                                    "date": "2025-04-06",
                                    "event": "Formula 1 Japanese Grand Prix 2025",
                                    "country": "Japan"
                                },
                                {
                                    "round": 4,
                                    "name": "Bahrain Grand Prix",
                                    "date": "2025-04-13",
                                    "event": "Formula 1 Gulf Air Bahrain Grand Prix 2025",
                                    "country": "Bahrain"
                                },
                                {
                                    "round": 5,
                                    "name": "Saudi Arabian Grand Prix",
                                    "date": "2025-04-20",
                                    "event": "Formula 1 STC Saudi Arabian Grand Prix 2025",
                                    "country": "Saudi Arabia"
                                }
                            ]
                            
                            # Store fallback data in database
                            for event in fallback_events:
                                cursor.execute("""
                                    INSERT INTO race_schedule (year, round, name, date, event, country)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (year, event["round"], event["name"], event["date"], 
                                     event["event"], event["country"]))
                            
                            conn.commit()
                            events = fallback_events
                        else:
                            raise HTTPException(status_code=500, detail=str(e))
                
                if not events:
                    raise HTTPException(status_code=404, detail=f"No valid race events found for year {year}")
                
                # Convert database results to the expected format
                return [{
                    "round": event[0],
                    "name": event[1],
                    "date": event[2],
                    "event": event[3],
                    "country": event[4]
                } for event in events]
                
    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qualifying/{year}/{round}")
async def get_qualifying_results(year: int, round: int):
    """Get qualifying results for a specific race."""
    try:
        session = fastf1.get_session(year, round, 'Q')
        session.load()
        results = session.results[['Position', 'DriverName', 'TeamName', 'Q3']]
        results.columns = ['position', 'driver_name', 'team', 'q3_time']
        return results.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error fetching qualifying results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/timing/{year}/{round}")
async def get_timing_data(year: int, round: int):
    """Get timing data for a specific race."""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        timing_data = session.laps[['LapNumber', 'Driver', 'LapTime']]
        timing_data.columns = ['lap', 'driver', 'time']
        return timing_data.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error fetching timing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/driver-stats/{year}/{driver}")
async def get_driver_stats(year: int, driver: str):
    """Get detailed statistics for a specific driver."""
    try:
        session = fastf1.get_session(year, 1, 'R')
        session.load()
        driver_data = session.laps.pick_driver(driver)
        stats = {
            "fastest_lap": driver_data['LapTime'].min(),
            "average_lap": driver_data['LapTime'].mean(),
            "total_laps": len(driver_data),
            "position": session.results.pick_driver(driver)['Position'].iloc[0]
        }
        return stats
    except Exception as e:
        logger.error(f"Error fetching driver stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pit-strategy/{year}/{round}")
async def get_pit_strategy(year: int, round: int):
    """Get pit stop strategy data for a specific race."""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        pit_data = session.pits[['LapNumber', 'Driver', 'Stop']]
        pit_data.columns = ['lap', 'driver', 'stop_number']
        return pit_data.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error fetching pit strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quick-stats/{year}")
async def get_quick_stats(year: int):
    """Get quick statistics for the current season."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get the latest round for the year
                cursor.execute("""
                    SELECT MAX(round) FROM driver_standings WHERE year = ?
                """, (year,))
                latest_round = cursor.fetchone()[0]
                
                if latest_round is None or latest_round == 0:
                    # For 2025, try to fetch from FastF1 first
                    if year == 2025:
                        try:
                            schedule = fastf1.get_event_schedule(year)
                            if not schedule.empty:
                                # Get all races for the year
                                all_standings = []
                                for _, race in schedule.iterrows():
                                    round_num = race['RoundNumber']
                                    try:
                                        # Load the race session
                                        session = fastf1.get_session(year, round_num, 'R')
                                        session.load()
                                        
                                        # Get driver standings with proper column mapping
                                        results = session.results
                                        logger.info(f"Processing race {round_num} for year {year}")
                                        
                                        # Format team colors to include '#' prefix
                                        team_colors = results['TeamColor'].apply(lambda x: f"#{x}" if pd.notna(x) and not str(x).startswith('#') else x)
                                        
                                        # Get fastest lap times
                                        fastest_laps = session.laps.groupby('Driver')['LapTime'].min()
                                        
                                        # Get qualifying positions
                                        try:
                                            quali_session = fastf1.get_session(year, round_num, 'Q')
                                            quali_session.load()
                                            quali_results = quali_session.results
                                            quali_positions = dict(zip(quali_results['DriverNumber'], quali_results['Position']))
                                        except Exception as e:
                                            logger.warning(f"Error fetching qualifying positions for round {round_num}: {str(e)}")
                                            quali_positions = {}
                                        
                                        # Calculate positions gained
                                        positions_gained = {}
                                        for driver in results['DriverNumber']:
                                            quali_pos = quali_positions.get(driver, 20)
                                            race_pos = results[results['DriverNumber'] == driver]['Position'].iloc[0]
                                            positions_gained[driver] = quali_pos - race_pos
                                        
                                        # Get pit stops
                                        try:
                                            pit_data = session.pits
                                            pit_stops = pit_data.groupby('DriverNumber').size()
                                        except Exception as e:
                                            logger.warning(f"Error fetching pit stops for round {round_num}: {str(e)}")
                                            pit_stops = {}
                                        
                                        standings = pd.DataFrame({
                                            'position': results['Position'],
                                            'driver_name': results['FullName'],
                                            'team': results['TeamName'],
                                            'points': results['Points'],
                                            'driver_color': team_colors.fillna('#ff0000'),
                                            'driver_number': results['DriverNumber'],
                                            'fastest_lap_time': results['DriverNumber'].map(lambda x: str(fastest_laps.get(x, 'N/A'))),
                                            'qualifying_position': results['DriverNumber'].map(lambda x: quali_positions.get(x, 20)),
                                            'positions_gained': results['DriverNumber'].map(lambda x: positions_gained.get(x, 0)),
                                            'pit_stops': results['DriverNumber'].map(lambda x: pit_stops.get(x, 0))
                                        })
                                        
                                        # Store in database
                                        for _, row in standings.iterrows():
                                            cursor.execute("""
                                                INSERT INTO driver_standings (
                                                    year, round, position, driver_name, team, points,
                                                    driver_color, driver_number, fastest_lap_time,
                                                    qualifying_position, positions_gained, pit_stops
                                                )
                                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                            """, (
                                                year, round_num, row['position'], row['driver_name'],
                                                row['team'], row['points'], row['driver_color'],
                                                row['driver_number'], row['fastest_lap_time'],
                                                row['qualifying_position'], row['positions_gained'],
                                                row['pit_stops']
                                            ))
                                        
                                        all_standings.append(standings)
                                        logger.info(f"Successfully processed race {round_num} for year {year}")
                                    except Exception as e:
                                        logger.warning(f"Error processing race {round_num} for year {year}: {str(e)}")
                                        continue
                                
                                conn.commit()
                                
                                if all_standings:
                                    # Calculate quick stats from actual data
                                    all_data = pd.concat(all_standings)
                                    
                                    # Most wins
                                    most_wins = all_data[all_data['position'] == 1].groupby(['driver_name', 'team', 'driver_color']).size().reset_index(name='wins')
                                    most_wins = most_wins.sort_values('wins', ascending=False).iloc[0]
                                    
                                    # Most pit stops
                                    most_pits = all_data.groupby(['driver_name', 'team', 'driver_color'])['pit_stops'].sum().reset_index()
                                    most_pits = most_pits.sort_values('pit_stops', ascending=False).iloc[0]
                                    
                                    # Most poles
                                    most_poles = all_data[all_data['qualifying_position'] == 1].groupby(['driver_name', 'team', 'driver_color']).size().reset_index(name='poles')
                                    most_poles = most_poles.sort_values('poles', ascending=False).iloc[0]
                                    
                                    # Most overtakes
                                    most_overtakes = all_data.groupby(['driver_name', 'team', 'driver_color'])['positions_gained'].max().reset_index()
                                    most_overtakes = most_overtakes.sort_values('positions_gained', ascending=False).iloc[0]
                                    
                                    return {
                                        "mostWins": {
                                            "driver": most_wins['driver_name'],
                                            "wins": int(most_wins['wins']),
                                            "team": most_wins['team'],
                                            "team_color": most_wins['driver_color']
                                        },
                                        "mostPitStops": {
                                            "driver": most_pits['driver_name'],
                                            "pits": int(most_pits['pit_stops']),
                                            "team": most_pits['team'],
                                            "team_color": most_pits['driver_color']
                                        },
                                        "mostPoles": {
                                            "driver": most_poles['driver_name'],
                                            "poles": int(most_poles['poles']),
                                            "team": most_poles['team'],
                                            "team_color": most_poles['driver_color']
                                        },
                                        "mostOvertakes": {
                                            "driver": most_overtakes['driver_name'],
                                            "overtakes": int(most_overtakes['positions_gained']),
                                            "team": most_overtakes['team'],
                                            "team_color": most_overtakes['driver_color']
                                        }
                                    }
                        except Exception as e:
                            logger.warning(f"Error fetching 2025 data from FastF1: {str(e)}")
                    
                    # If FastF1 fails or no data available, use database data
                    logger.info(f"Using database data for year {year}")
                    cursor.execute("""
                        WITH race_winners AS (
                            SELECT driver_name, team, driver_color, COUNT(*) as wins
                            FROM driver_standings
                            WHERE year = ? AND position = 1 AND round > 0
                            GROUP BY driver_name, team, driver_color
                        )
                        SELECT driver_name, team, driver_color, wins
                        FROM race_winners
                        ORDER BY wins DESC
                        LIMIT 1
                    """, (year,))
                    most_wins = cursor.fetchone()
                    
                    cursor.execute("""
                        SELECT driver_name, team, driver_color, SUM(pit_stops) as total_pits
                        FROM driver_standings
                        WHERE year = ? AND round > 0
                        GROUP BY driver_name, team, driver_color
                        ORDER BY total_pits DESC
                        LIMIT 1
                    """, (year,))
                    most_pits = cursor.fetchone()
                    
                    cursor.execute("""
                        WITH qualifying_results AS (
                            SELECT driver_name, team, driver_color, COUNT(*) as poles
                            FROM driver_standings
                            WHERE year = ? AND qualifying_position = 1 AND round > 0
                            GROUP BY driver_name, team, driver_color
                        )
                        SELECT driver_name, team, driver_color, poles
                        FROM qualifying_results
                        ORDER BY poles DESC
                        LIMIT 1
                    """, (year,))
                    most_poles = cursor.fetchone()
                    
                    cursor.execute("""
                        SELECT driver_name, team, driver_color, MAX(positions_gained) as overtakes
                        FROM driver_standings
                        WHERE year = ? AND round > 0
                        GROUP BY driver_name, team, driver_color
                        ORDER BY overtakes DESC
                        LIMIT 1
                    """, (year,))
                    most_overtakes = cursor.fetchone()
                    
                    return {
                        "mostWins": {
                            "driver": most_wins[0] if most_wins else "N/A",
                            "wins": most_wins[3] if most_wins else 0,
                            "team": most_wins[1] if most_wins else "N/A",
                            "team_color": most_wins[2] if most_wins else "#ff0000"
                        },
                        "mostPitStops": {
                            "driver": most_pits[0] if most_pits else "N/A",
                            "pits": most_pits[3] if most_pits else 0,
                            "team": most_pits[1] if most_pits else "N/A",
                            "team_color": most_pits[2] if most_pits else "#ff0000"
                        },
                        "mostPoles": {
                            "driver": most_poles[0] if most_poles else "N/A",
                            "poles": most_poles[3] if most_poles else 0,
                            "team": most_poles[1] if most_poles else "N/A",
                            "team_color": most_poles[2] if most_poles else "#ff0000"
                        },
                        "mostOvertakes": {
                            "driver": most_overtakes[0] if most_overtakes else "N/A",
                            "overtakes": most_overtakes[3] if most_overtakes else 0,
                            "team": most_overtakes[1] if most_overtakes else "N/A",
                            "team_color": most_overtakes[2] if most_overtakes else "#ff0000"
                        }
                    }
                
                # If data exists, return from database
                logger.info(f"Fetching quick stats for year {year} from database")
                cursor.execute("""
                    WITH race_winners AS (
                        SELECT driver_name, team, driver_color, COUNT(*) as wins
                        FROM driver_standings
                        WHERE year = ? AND position = 1 AND round > 0
                        GROUP BY driver_name, team, driver_color
                    )
                    SELECT driver_name, team, driver_color, wins
                    FROM race_winners
                    ORDER BY wins DESC
                    LIMIT 1
                """, (year,))
                most_wins = cursor.fetchone()
                
                cursor.execute("""
                    SELECT driver_name, team, driver_color, SUM(pit_stops) as total_pits
                    FROM driver_standings
                    WHERE year = ? AND round > 0
                    GROUP BY driver_name, team, driver_color
                    ORDER BY total_pits DESC
                    LIMIT 1
                """, (year,))
                most_pits = cursor.fetchone()
                
                cursor.execute("""
                    WITH qualifying_results AS (
                        SELECT driver_name, team, driver_color, COUNT(*) as poles
                        FROM driver_standings
                        WHERE year = ? AND qualifying_position = 1 AND round > 0
                        GROUP BY driver_name, team, driver_color
                    )
                    SELECT driver_name, team, driver_color, poles
                    FROM qualifying_results
                    ORDER BY poles DESC
                    LIMIT 1
                """, (year,))
                most_poles = cursor.fetchone()
                
                cursor.execute("""
                    SELECT driver_name, team, driver_color, MAX(positions_gained) as overtakes
                    FROM driver_standings
                    WHERE year = ? AND round > 0
                    GROUP BY driver_name, team, driver_color
                    ORDER BY overtakes DESC
                    LIMIT 1
                """, (year,))
                most_overtakes = cursor.fetchone()
                
                return {
                    "mostWins": {
                        "driver": most_wins[0] if most_wins else "N/A",
                        "wins": most_wins[3] if most_wins else 0,
                        "team": most_wins[1] if most_wins else "N/A",
                        "team_color": most_wins[2] if most_wins else "#ff0000"
                    },
                    "mostPitStops": {
                        "driver": most_pits[0] if most_pits else "N/A",
                        "pits": most_pits[3] if most_pits else 0,
                        "team": most_pits[1] if most_pits else "N/A",
                        "team_color": most_pits[2] if most_pits else "#ff0000"
                    },
                    "mostPoles": {
                        "driver": most_poles[0] if most_poles else "N/A",
                        "poles": most_poles[3] if most_poles else 0,
                        "team": most_poles[1] if most_poles else "N/A",
                        "team_color": most_poles[2] if most_poles else "#ff0000"
                    },
                    "mostOvertakes": {
                        "driver": most_overtakes[0] if most_overtakes else "N/A",
                        "overtakes": most_overtakes[3] if most_overtakes else 0,
                        "team": most_overtakes[1] if most_overtakes else "N/A",
                        "team_color": most_overtakes[2] if most_overtakes else "#ff0000"
                    }
                }
                
    except Exception as e:
        logger.error(f"Error fetching quick stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/circuit-preview/{year}")
async def get_circuit_preview(year: int):
    """Get circuit preview information for the next race."""
    try:
        # Get the schedule
        schedule = fastf1.get_event_schedule(year)
        if schedule.empty:
            raise HTTPException(status_code=404, detail=f"No races found for year {year}")
        
        # Find the next race
        now = pd.Timestamp.now()
        next_race = schedule[schedule['EventDate'] > now].iloc[0]
        
        # Get circuit information
        event = fastf1.get_event(year, next_race['RoundNumber'])
        circuit = event.get_circuit_info()
        
        return {
            "name": next_race['EventName'],
            "date": next_race['EventDate'].strftime('%Y-%m-%d'),
            "country": event.get('Country', 'Unknown'),
            "circuitLength": f"{circuit['CircuitLength']:.3f} km",
            "numberOfLaps": circuit['NumberOfLaps'],
            "firstGrandPrix": circuit['FirstGrandPrix'],
            "lapRecord": {
                "time": str(circuit['LapRecord']['Time']),
                "driver": circuit['LapRecord']['Driver'],
                "year": circuit['LapRecord']['Year']
            }
        }
    except Exception as e:
        logger.error(f"Error fetching circuit preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/race-results/{year}/{round}")
async def get_race_results(year: int, round: int):
    """Get detailed race results for a specific race."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get race results from database
                cursor.execute("""
                    SELECT 
                        position,
                        driver_name,
                        team,
                        points,
                        driver_color,
                        driver_number,
                        fastest_lap_time,
                        qualifying_position,
                        positions_gained,
                        pit_stops
                    FROM driver_standings
                    WHERE year = ? AND round = ?
                    ORDER BY position
                """, (year, round))
                
                results = cursor.fetchall()
                
                if not results:
                    # If no data in database, try to fetch from FastF1
                    try:
                        session = fastf1.get_session(year, round, 'R')
                        session.load()
                        
                        # Get race results
                        race_results = session.results
                        
                        # Get fastest lap times
                        fastest_laps = session.laps.groupby('Driver')['LapTime'].min()
                        
                        # Get qualifying positions
                        try:
                            quali_session = fastf1.get_session(year, round, 'Q')
                            quali_session.load()
                            quali_results = quali_session.results
                            quali_positions = dict(zip(quali_results['DriverNumber'], quali_results['Position']))
                        except Exception as e:
                            logger.warning(f"Error fetching qualifying positions: {str(e)}")
                            quali_positions = {}
                        
                        # Calculate positions gained
                        positions_gained = {}
                        for driver in race_results['DriverNumber']:
                            quali_pos = quali_positions.get(driver, 20)
                            race_pos = race_results[race_results['DriverNumber'] == driver]['Position'].iloc[0]
                            positions_gained[driver] = quali_pos - race_pos
                        
                        # Get pit stops
                        try:
                            pit_data = session.pits
                            pit_stops = pit_data.groupby('DriverNumber').size()
                        except Exception as e:
                            logger.warning(f"Error fetching pit stops: {str(e)}")
                            pit_stops = {}
                        
                        # Format results
                        results = []
                        for _, row in race_results.iterrows():
                            driver_number = row['DriverNumber']
                            # Format fastest lap time to be more readable
                            fastest_lap = fastest_laps.get(driver_number)
                            if pd.notna(fastest_lap):
                                fastest_lap_str = str(fastest_lap).split('.')[0]  # Remove microseconds
                            else:
                                fastest_lap_str = 'N/A'
                            
                            results.append({
                                "position": int(row['Position']),
                                "driver_name": str(row['FullName']),
                                "team": str(row['TeamName']),
                                "points": float(row['Points']),
                                "driver_color": f"#{row['TeamColor']}" if pd.notna(row['TeamColor']) and not str(row['TeamColor']).startswith('#') else str(row['TeamColor']),
                                "driver_number": int(driver_number),
                                "fastest_lap_time": fastest_lap_str,
                                "qualifying_position": int(quali_positions.get(driver_number, 20)),
                                "positions_gained": int(positions_gained.get(driver_number, 0)),
                                "pit_stops": int(pit_stops.get(driver_number, 0))
                            })
                        
                        # Store in database for future use
                        for result in results:
                            cursor.execute("""
                                INSERT INTO driver_standings (
                                    year, round, position, driver_name, team, points,
                                    driver_color, driver_number, fastest_lap_time,
                                    qualifying_position, positions_gained, pit_stops
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                year, round, result['position'], result['driver_name'],
                                result['team'], result['points'], result['driver_color'],
                                result['driver_number'], result['fastest_lap_time'],
                                result['qualifying_position'], result['positions_gained'],
                                result['pit_stops']
                            ))
                        
                        conn.commit()
                        
                    except Exception as e:
                        logger.error(f"Error fetching from FastF1: {str(e)}")
                        raise HTTPException(status_code=404, detail=f"No race results found for round {round}")
                
                # Convert database results to the expected format
                return [{
                    "position": row[0],
                    "driver_name": row[1],
                    "team": row[2],
                    "points": row[3],
                    "driver_color": row[4],
                    "driver_number": row[5],
                    "fastest_lap_time": row[6],
                    "qualifying_position": row[7],
                    "positions_gained": row[8],
                    "pit_stops": row[9]
                } for row in results]
                
    except Exception as e:
        logger.error(f"Error fetching race results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/circuits/{year}")
async def get_circuits(year: int):
    """Get detailed circuit information for a specific year."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get circuit information from database
                cursor.execute("""
                    SELECT 
                        round,
                        name,
                        country,
                        event,
                        first_grand_prix,
                        circuit_length,
                        number_of_laps,
                        race_distance,
                        lap_record,
                        drs_zones,
                        track_type,
                        track_map
                    FROM circuits
                    WHERE year = ?
                    ORDER BY round
                """, (year,))
                
                results = cursor.fetchall()
                
                if not results:
                    # If no data in database, try to fetch from FastF1
                    try:
                        schedule = fastf1.get_event_schedule(year)
                        
                        circuits = []
                        for _, event in schedule.iterrows():
                            try:
                                # Skip testing events
                                if event['RoundNumber'] == 0:
                                    continue
                                    
                                # Get event details
                                event_details = fastf1.get_event(year, event['RoundNumber'])
                                
                                # Format circuit data with fallbacks for missing attributes
                                circuit_data = {
                                    "round": int(event['RoundNumber']),
                                    "name": str(event['EventName']),
                                    "country": str(event['Country']),
                                    "event": str(event['EventFormat']),
                                    "first_grand_prix": str(event.get('FirstGrandPrix', 'N/A')),
                                    "circuit_length": float(getattr(event_details, 'CircuitLength', 0.0)),
                                    "number_of_laps": int(getattr(event_details, 'NumberOfLaps', 0)),
                                    "race_distance": float(getattr(event_details, 'RaceDistance', 0.0)),
                                    "lap_record": "N/A",  # Default to N/A since LapRecord is not available
                                    "drs_zones": f"{len(getattr(event_details, 'DRSZones', []))} zones",
                                    "track_type": str(getattr(event_details, 'TrackType', 'N/A')),
                                    "track_map": str(getattr(event_details, 'TrackMap', None)) if hasattr(event_details, 'TrackMap') else None
                                }
                                
                                circuits.append(circuit_data)
                                
                                # Store in database
                                cursor.execute("""
                                    INSERT INTO circuits (
                                        year, round, name, country, event,
                                        first_grand_prix, circuit_length,
                                        number_of_laps, race_distance,
                                        lap_record, drs_zones, track_type,
                                        track_map
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    year, circuit_data['round'], circuit_data['name'],
                                    circuit_data['country'], circuit_data['event'],
                                    circuit_data['first_grand_prix'], circuit_data['circuit_length'],
                                    circuit_data['number_of_laps'], circuit_data['race_distance'],
                                    circuit_data['lap_record'], circuit_data['drs_zones'],
                                    circuit_data['track_type'], circuit_data['track_map']
                                ))
                                
                            except Exception as e:
                                logger.warning(f"Error fetching circuit info for round {event['RoundNumber']}: {str(e)}")
                                continue
                        
                        conn.commit()
                        return circuits
                        
                    except Exception as e:
                        logger.error(f"Error fetching from FastF1: {str(e)}")
                        # Use fallback data for 2025
                        if year == 2025:
                            logger.info("Using fallback data for 2025 circuits")
                            fallback_circuits = [
                                {
                                    "round": 1,
                                    "name": "Australian Grand Prix",
                                    "country": "Australia",
                                    "event": "Formula 1 Australian Grand Prix 2025",
                                    "first_grand_prix": "1985",
                                    "circuit_length": 5.278,
                                    "number_of_laps": 58,
                                    "race_distance": 306.124,
                                    "lap_record": "1:20.235 - Charles Leclerc (2022)",
                                    "drs_zones": "4 zones",
                                    "track_type": "Street Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 2,
                                    "name": "Chinese Grand Prix",
                                    "country": "China",
                                    "event": "Formula 1 Chinese Grand Prix 2025",
                                    "first_grand_prix": "2004",
                                    "circuit_length": 5.451,
                                    "number_of_laps": 56,
                                    "race_distance": 305.256,
                                    "lap_record": "1:32.238 - Lewis Hamilton (2019)",
                                    "drs_zones": "2 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 3,
                                    "name": "Japanese Grand Prix",
                                    "country": "Japan",
                                    "event": "Formula 1 Japanese Grand Prix 2025",
                                    "first_grand_prix": "1976",
                                    "circuit_length": 5.807,
                                    "number_of_laps": 53,
                                    "race_distance": 307.471,
                                    "lap_record": "1:30.983 - Lewis Hamilton (2019)",
                                    "drs_zones": "2 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 4,
                                    "name": "Bahrain Grand Prix",
                                    "country": "Bahrain",
                                    "event": "Formula 1 Gulf Air Bahrain Grand Prix 2025",
                                    "first_grand_prix": "2004",
                                    "circuit_length": 5.412,
                                    "number_of_laps": 57,
                                    "race_distance": 308.238,
                                    "lap_record": "1:31.447 - Pedro de la Rosa (2005)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 5,
                                    "name": "Saudi Arabian Grand Prix",
                                    "country": "Saudi Arabia",
                                    "event": "Formula 1 STC Saudi Arabian Grand Prix 2025",
                                    "first_grand_prix": "2021",
                                    "circuit_length": 6.174,
                                    "number_of_laps": 50,
                                    "race_distance": 308.700,
                                    "lap_record": "1:28.265 - Lewis Hamilton (2021)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Street Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 6,
                                    "name": "Miami Grand Prix",
                                    "country": "United States",
                                    "event": "Formula 1 Crypto.com Miami Grand Prix 2025",
                                    "first_grand_prix": "2022",
                                    "circuit_length": 5.412,
                                    "number_of_laps": 57,
                                    "race_distance": 308.326,
                                    "lap_record": "1:29.708 - Max Verstappen (2023)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Street Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 7,
                                    "name": "Emilia Romagna Grand Prix",
                                    "country": "Italy",
                                    "event": "Formula 1 Rolex Emilia Romagna Grand Prix 2025",
                                    "first_grand_prix": "2020",
                                    "circuit_length": 4.909,
                                    "number_of_laps": 63,
                                    "race_distance": 309.049,
                                    "lap_record": "1:15.484 - Lewis Hamilton (2020)",
                                    "drs_zones": "2 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 8,
                                    "name": "Monaco Grand Prix",
                                    "country": "Monaco",
                                    "event": "Formula 1 Grand Prix de Monaco 2025",
                                    "first_grand_prix": "1950",
                                    "circuit_length": 3.337,
                                    "number_of_laps": 78,
                                    "race_distance": 260.286,
                                    "lap_record": "1:12.909 - Lewis Hamilton (2021)",
                                    "drs_zones": "1 zone",
                                    "track_type": "Street Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 9,
                                    "name": "Spanish Grand Prix",
                                    "country": "Spain",
                                    "event": "Formula 1 Spanish Grand Prix 2025",
                                    "first_grand_prix": "1991",
                                    "circuit_length": 4.657,
                                    "number_of_laps": 66,
                                    "race_distance": 307.236,
                                    "lap_record": "1:18.149 - Max Verstappen (2023)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 10,
                                    "name": "Canadian Grand Prix",
                                    "country": "Canada",
                                    "event": "Formula 1 Canadian Grand Prix 2025",
                                    "first_grand_prix": "1978",
                                    "circuit_length": 4.361,
                                    "number_of_laps": 70,
                                    "race_distance": 305.270,
                                    "lap_record": "1:13.078 - Valtteri Bottas (2019)",
                                    "drs_zones": "2 zones",
                                    "track_type": "Street Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 11,
                                    "name": "Austrian Grand Prix",
                                    "country": "Austria",
                                    "event": "Formula 1 Austrian Grand Prix 2025",
                                    "first_grand_prix": "1970",
                                    "circuit_length": 4.318,
                                    "number_of_laps": 71,
                                    "race_distance": 306.452,
                                    "lap_record": "1:05.619 - Carlos Sainz (2020)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 12,
                                    "name": "British Grand Prix",
                                    "country": "United Kingdom",
                                    "event": "Formula 1 British Grand Prix 2025",
                                    "first_grand_prix": "1950",
                                    "circuit_length": 5.891,
                                    "number_of_laps": 52,
                                    "race_distance": 306.198,
                                    "lap_record": "1:27.097 - Max Verstappen (2023)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 13,
                                    "name": "Belgian Grand Prix",
                                    "country": "Belgium",
                                    "event": "Formula 1 Belgian Grand Prix 2025",
                                    "first_grand_prix": "1950",
                                    "circuit_length": 7.004,
                                    "number_of_laps": 44,
                                    "race_distance": 308.052,
                                    "lap_record": "1:46.286 - Max Verstappen (2023)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 14,
                                    "name": "Hungarian Grand Prix",
                                    "country": "Hungary",
                                    "event": "Formula 1 Hungarian Grand Prix 2025",
                                    "first_grand_prix": "1986",
                                    "circuit_length": 4.381,
                                    "number_of_laps": 70,
                                    "race_distance": 306.630,
                                    "lap_record": "1:16.627 - Lewis Hamilton (2020)",
                                    "drs_zones": "2 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 15,
                                    "name": "Dutch Grand Prix",
                                    "country": "Netherlands",
                                    "event": "Formula 1 Dutch Grand Prix 2025",
                                    "first_grand_prix": "1952",
                                    "circuit_length": 4.259,
                                    "number_of_laps": 72,
                                    "race_distance": 306.587,
                                    "lap_record": "1:11.097 - Lewis Hamilton (2021)",
                                    "drs_zones": "2 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 16,
                                    "name": "Italian Grand Prix",
                                    "country": "Italy",
                                    "event": "Formula 1 Italian Grand Prix 2025",
                                    "first_grand_prix": "1950",
                                    "circuit_length": 5.793,
                                    "number_of_laps": 53,
                                    "race_distance": 306.720,
                                    "lap_record": "1:21.046 - Rubens Barrichello (2004)",
                                    "drs_zones": "2 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 17,
                                    "name": "Azerbaijan Grand Prix",
                                    "country": "Azerbaijan",
                                    "event": "Formula 1 Azerbaijan Grand Prix 2025",
                                    "first_grand_prix": "2017",
                                    "circuit_length": 6.003,
                                    "number_of_laps": 51,
                                    "race_distance": 306.049,
                                    "lap_record": "1:43.009 - Charles Leclerc (2019)",
                                    "drs_zones": "2 zones",
                                    "track_type": "Street Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 18,
                                    "name": "Singapore Grand Prix",
                                    "country": "Singapore",
                                    "event": "Formula 1 Singapore Grand Prix 2025",
                                    "first_grand_prix": "2008",
                                    "circuit_length": 4.940,
                                    "number_of_laps": 62,
                                    "race_distance": 306.143,
                                    "lap_record": "1:41.905 - Charles Leclerc (2023)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Street Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 19,
                                    "name": "United States Grand Prix",
                                    "country": "United States",
                                    "event": "Formula 1 United States Grand Prix 2025",
                                    "first_grand_prix": "2012",
                                    "circuit_length": 5.513,
                                    "number_of_laps": 56,
                                    "race_distance": 308.405,
                                    "lap_record": "1:36.169 - Charles Leclerc (2019)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 20,
                                    "name": "Mexico City Grand Prix",
                                    "country": "Mexico",
                                    "event": "Formula 1 Mexico City Grand Prix 2025",
                                    "first_grand_prix": "1963",
                                    "circuit_length": 4.304,
                                    "number_of_laps": 71,
                                    "race_distance": 305.354,
                                    "lap_record": "1:17.774 - Valtteri Bottas (2021)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 21,
                                    "name": "São Paulo Grand Prix",
                                    "country": "Brazil",
                                    "event": "Formula 1 São Paulo Grand Prix 2025",
                                    "first_grand_prix": "1973",
                                    "circuit_length": 4.309,
                                    "number_of_laps": 71,
                                    "race_distance": 305.879,
                                    "lap_record": "1:10.540 - Valtteri Bottas (2018)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 22,
                                    "name": "Las Vegas Grand Prix",
                                    "country": "United States",
                                    "event": "Formula 1 Las Vegas Grand Prix 2025",
                                    "first_grand_prix": "2023",
                                    "circuit_length": 6.201,
                                    "number_of_laps": 50,
                                    "race_distance": 310.050,
                                    "lap_record": "1:35.490 - Oscar Piastri (2023)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Street Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 23,
                                    "name": "Qatar Grand Prix",
                                    "country": "Qatar",
                                    "event": "Formula 1 Qatar Grand Prix 2025",
                                    "first_grand_prix": "2021",
                                    "circuit_length": 5.380,
                                    "number_of_laps": 57,
                                    "race_distance": 306.660,
                                    "lap_record": "1:23.196 - Max Verstappen (2023)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                },
                                {
                                    "round": 24,
                                    "name": "Abu Dhabi Grand Prix",
                                    "country": "UAE",
                                    "event": "Formula 1 Abu Dhabi Grand Prix 2025",
                                    "first_grand_prix": "2009",
                                    "circuit_length": 5.554,
                                    "number_of_laps": 55,
                                    "race_distance": 305.355,
                                    "lap_record": "1:26.103 - Max Verstappen (2021)",
                                    "drs_zones": "3 zones",
                                    "track_type": "Permanent Circuit",
                                    "track_map": None
                                }
                            ]
                            
                            # Store fallback data in database
                            for circuit in fallback_circuits:
                                cursor.execute("""
                                    INSERT INTO circuits (
                                        year, round, name, country, event,
                                        first_grand_prix, circuit_length,
                                        number_of_laps, race_distance,
                                        lap_record, drs_zones, track_type,
                                        track_map
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    year, circuit['round'], circuit['name'],
                                    circuit['country'], circuit['event'],
                                    circuit['first_grand_prix'], circuit['circuit_length'],
                                    circuit['number_of_laps'], circuit['race_distance'],
                                    circuit['lap_record'], circuit['drs_zones'],
                                    circuit['track_type'], circuit['track_map']
                                ))
                            
                            conn.commit()
                            return fallback_circuits
                        else:
                            raise HTTPException(status_code=404, detail=f"No circuit information found for year {year}")
                
                # Convert database results to the expected format
                return [{
                    "round": row[0],
                    "name": row[1],
                    "country": row[2],
                    "event": row[3],
                    "first_grand_prix": row[4],
                    "circuit_length": row[5],
                    "number_of_laps": row[6],
                    "race_distance": row[7],
                    "lap_record": row[8],
                    "drs_zones": row[9],
                    "track_type": row[10],
                    "track_map": row[11]
                } for row in results]
                
    except Exception as e:
        logger.error(f"Error fetching circuit information: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/race/{year}/{round}/positions")
async def get_race_positions(year: int, round: int):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # First try to get from database
                cursor.execute("""
                    SELECT driver_abbr, positions, lap_numbers, color, driver_name, team
                    FROM race_positions
                    WHERE year = ? AND round = ?
                """, (year, round))
                
                results = cursor.fetchall()
                
                if results:
                    # Convert stored strings back to lists
                    position_data = {}
                    for row in results:
                        try:
                            # Try JSON first
                            positions = json.loads(row[1])
                            lap_numbers = json.loads(row[2])
                        except json.JSONDecodeError:
                            try:
                                # If JSON fails, try eval (for older data)
                                positions = eval(row[1])
                                lap_numbers = eval(row[2])
                            except:
                                # If both fail, skip this row
                                logger.error(f"Error parsing position data for driver {row[0]}")
                                continue
                        
                        position_data[row[0]] = {
                            'positions': positions,
                            'lap_numbers': lap_numbers,
                            'color': row[3],
                            'driver_name': row[4],
                            'team': row[5]
                        }
                    
                    if position_data:
                        return position_data
                
                # If not in database or no valid data, fetch from FastF1
                session = fastf1.get_session(year, round, 'R')
                session.load(telemetry=False, weather=False)
                
                # Create a dictionary to store position data for each driver
                position_data = {}
                
                # Define team colors (you can expand this list)
                team_colors = {
                    'Red Bull Racing': '#0600EF',
                    'Mercedes': '#00D2BE',
                    'Ferrari': '#DC0000',
                    'McLaren': '#FF8700',
                    'Aston Martin': '#006F62',
                    'Alpine': '#0090FF',
                    'Williams': '#005AFF',
                    'AlphaTauri': '#2B4562',
                    'Alfa Romeo': '#900000',
                    'Haas F1 Team': '#FFFFFF'
                }
                
                # Get position data for each driver
                for drv in session.drivers:
                    try:
                        drv_laps = session.laps.pick_drivers(drv)
                        if len(drv_laps) == 0:
                            continue
                            
                        abb = drv_laps['Driver'].iloc[0]
                        team = drv_laps['Team'].iloc[0]
                        
                        # Get position data, handling potential NaN values
                        positions = drv_laps['Position'].fillna(method='ffill').fillna(method='bfill').tolist()
                        lap_numbers = drv_laps['LapNumber'].tolist()
                        
                        # Convert any remaining NaN or infinite values to None
                        positions = [None if pd.isna(pos) or np.isinf(pos) else float(pos) for pos in positions]
                        
                        # Only include drivers who have valid position data
                        if positions and any(pos is not None for pos in positions):
                            # Get team color or use a default
                            color = team_colors.get(team, '#ff0000')
                            
                            position_data[abb] = {
                                'positions': positions,
                                'lap_numbers': lap_numbers,
                                'color': color,
                                'driver_name': drv_laps['Driver'].iloc[0],
                                'team': team
                            }
                            
                            # Store in database
                            cursor.execute("""
                                INSERT OR REPLACE INTO race_positions (
                                    year, round, driver_abbr, positions, lap_numbers,
                                    color, driver_name, team
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                year, round, abb,
                                json.dumps(positions),  # Convert list to JSON string for storage
                                json.dumps(lap_numbers),  # Convert list to JSON string for storage
                                color,
                                drv_laps['Driver'].iloc[0],
                                team
                            ))
                    except Exception as e:
                        logger.error(f"Error processing driver {drv}: {str(e)}")
                        continue
                
                conn.commit()
                
                if not position_data:
                    raise HTTPException(status_code=404, detail="No valid position data found for this race")
                    
                return position_data
                
    except Exception as e:
        logger.error(f"Error in get_race_positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)