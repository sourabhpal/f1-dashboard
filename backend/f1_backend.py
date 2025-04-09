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
    allow_origins=["*"],  # Allow all origins
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

# Nationality to Flag Emoji Mapping
NATIONALITY_FLAGS = {
    'British': '🇬🇧',
    'German': '🇩🇪',
    'Dutch': '🇳🇱',
    'Monegasque': '🇲🇨', # Monaco
    'Spanish': '🇪🇸',
    'Finnish': '🇫🇮',
    'French': '🇫🇷',
    'Australian': '🇦🇺',
    'Canadian': '🇨🇦',
    'Mexican': '🇲🇽',
    'Japanese': '🇯🇵',
    'Thai': '🇹🇭',
    'Chinese': '🇨🇳',
    'Danish': '🇩🇰',
    'Italian': '🇮🇹',
    'American': '🇺🇸',
    'Belgian': '🇧🇪',
    'Brazilian': '🇧🇷',
    'New Zealander': '🇳🇿',
    'Austrian': '🇦🇹',
    'Swiss': '🇨🇭',
    'Saudi Arabian': '🇸🇦',
    'Emirati': '🇦🇪', # UAE
    'Russian': '🇷🇺',
    'Polish': '🇵🇱',
    # Add more as needed
    'Unknown': '🏳️', # Default/Unknown
    None: '🏳️'
}

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
                    laps INTEGER,
                    status TEXT,
                    grid_position INTEGER,
                    nationality TEXT,
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
                    country TEXT,
                    is_sprint BOOLEAN DEFAULT 0,
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
            
            if 'laps' not in columns:
                logger.info("Adding laps column to driver_standings table")
                conn.execute('ALTER TABLE driver_standings ADD COLUMN laps INTEGER')
            
            if 'status' not in columns:
                logger.info("Adding status column to driver_standings table")
                conn.execute('ALTER TABLE driver_standings ADD COLUMN status TEXT')
            
            if 'grid_position' not in columns:
                logger.info("Adding grid_position column to driver_standings table")
                conn.execute('ALTER TABLE driver_standings ADD COLUMN grid_position INTEGER')
            
            if 'nationality' not in columns:
                logger.info("Adding nationality column to driver_standings table")
                conn.execute('ALTER TABLE driver_standings ADD COLUMN nationality TEXT')
            
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

# Add this function after the imports and before the first route
def standardize_team_color(color):
    """Standardize team color format to ensure it has a '#' prefix."""
    if not color or pd.isna(color):
        return '#ff0000'  # Default red color
    
    # Convert to string if it's not already
    color_str = str(color)
    
    # If it doesn't start with '#', add it
    if not color_str.startswith('#'):
        color_str = f"#{color_str}"
    
    return color_str

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

def get_driver_team(driver_name, year):
    """
    Get the correct team for a driver in a given year.
    
    Args:
        driver_name (str): Driver name
        year (int): Year to check
        
    Returns:
        str: Team name
    """
    # Use the team from the database instead of hardcoded mapping
    with db_lock:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT team
                FROM driver_standings
                WHERE year = ? AND driver_name = ?
                ORDER BY round DESC
                LIMIT 1
            """, (year, driver_name))
            result = cursor.fetchone()
            if result:
                return result[0]
    
    # Fallback to hardcoded mapping if not found in database
    team_mapping = {
        'Kimi Antonelli': 'Mercedes',
        'Isack Hadjar': 'Racing Bulls',
        'Gabriel Bortoleto': 'Kick Sauber',
        'Jack Doohan': 'Alpine',
        'Liam Lawson': 'Racing Bulls',
        'Yuki Tsunoda': 'Red Bull Racing',
        'Pierre Gasly': 'Alpine',
        'Fernando Alonso': 'Aston Martin',
        'Carlos Sainz': 'Williams',
        'Lewis Hamilton': 'Ferrari',
        'Charles Leclerc': 'Ferrari',
        'Lance Stroll': 'Aston Martin',
        'Esteban Ocon': 'Haas F1 Team',
        'Oliver Bearman': 'Haas F1 Team',
        'Nico Hulkenberg': 'Kick Sauber',
        'Alexander Albon': 'Williams',
        'George Russell': 'Mercedes',
        'Oscar Piastri': 'McLaren',
        'Lando Norris': 'McLaren',
        'Max Verstappen': 'Red Bull Racing'
    }
    return team_mapping.get(driver_name, 'Unknown')

def calculate_points(position, is_fastest_lap=False, is_sprint=False):
    """
    Calculate points according to the official F1 2025 rules.
    
    Args:
        position (int): Race position (1-10 for main race, 1-8 for sprint)
        is_fastest_lap (bool): Whether the driver set the fastest lap (not used in 2025)
        is_sprint (bool): Whether this is a sprint race
        
    Returns:
        float: Points awarded
    """
    if is_sprint:
        # Sprint race points (2025)
        sprint_points = {
            1: 8.0,
            2: 7.0,
            3: 6.0,
            4: 5.0,
            5: 4.0,
            6: 3.0,
            7: 2.0,
            8: 1.0
        }
        return sprint_points.get(position, 0.0)
    else:
        # Main race points (2025)
        race_points = {
            1: 25.0,
            2: 18.0,
            3: 15.0,
            4: 12.0,
            5: 10.0,
            6: 8.0,
            7: 6.0,
            8: 4.0,
            9: 2.0,
            10: 1.0
        }
        return race_points.get(position, 0.0)

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
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get the latest team information for each driver, including nationality
            cursor.execute("""
                WITH standardized_names AS (
                    SELECT
                        CASE
                            WHEN driver_name LIKE '%Kimi Antonelli%' THEN 'Kimi Antonelli'
                            ELSE driver_name
                        END as driver_name,
                        team,
                        driver_number,
                        driver_color,
                        nationality,
                        round,
                        points,
                        sprint_points,
                        year,
                        is_sprint
                    FROM driver_standings
                ),
                latest_team AS (
                    SELECT
                        driver_name,
                        team,
                        driver_number,
                        driver_color,
                        nationality,
                        MAX(round) as latest_round
                    FROM standardized_names
                    WHERE year = ?
                    GROUP BY driver_name
                ),
                cumulative_points AS (
                    SELECT
                        driver_name,
                        SUM(points) as total_race_points,
                        SUM(sprint_points) as total_sprint_points,
                        SUM(points) + SUM(sprint_points) as total_points,
                        COUNT(DISTINCT round) as races_participated,
                        MAX(round) as latest_round
                    FROM standardized_names
                    WHERE year = ?
                    GROUP BY driver_name
                )
                SELECT
                    lt.driver_name,
                    lt.team,
                    lt.driver_number,
                    CASE
                        WHEN lt.driver_color NOT LIKE '#%' THEN '#' || lt.driver_color
                        ELSE lt.driver_color
                    END as driver_color,
                    lt.nationality,
                    cp.total_race_points,
                    cp.total_sprint_points,
                    cp.total_points,
                    cp.races_participated,
                    DENSE_RANK() OVER (
                        ORDER BY cp.total_points DESC,
                        cp.races_participated DESC,
                        cp.latest_round DESC
                    ) as position
                FROM latest_team lt
                JOIN cumulative_points cp ON lt.driver_name = cp.driver_name
                ORDER BY position, cp.total_points DESC, cp.races_participated DESC
            """, (year, year))

            standings = []
            for row in cursor.fetchall():
                nationality = row[4]
                standings.append({
                    "driver_name": row[0],
                    "team": row[1],
                    "driver_number": row[2],
                    "driver_color": row[3],
                    "nationality": nationality,
                    "nationality_flag": NATIONALITY_FLAGS.get(nationality, '🏳️'),
                    "points": row[5],
                    "sprint_points": row[6],
                    "total_points": row[7],
                    "races_participated": row[8],
                    "position": row[9]
                })

            return standings
    except Exception as e:
        logger.error(f"Error fetching standings for year {year}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/team_standings/{year}")
async def get_team_standings(year: int):
    """Get team standings for a specific year."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get team standings with cumulative points
            cursor.execute("""
                WITH latest_team AS (
                    SELECT 
                        team,
                        team_color,
                        MAX(round) as latest_round
                    FROM constructors_standings
                    WHERE year = ?
                    GROUP BY team
                ),
                cumulative_stats AS (
                    SELECT 
                        team,
                        SUM(points) as total_race_points,
                        SUM(sprint_points) as total_sprint_points,
                        SUM(points) + SUM(sprint_points) as total_points,
                        SUM(wins) as wins,
                        SUM(podiums) as podiums,
                        SUM(fastest_laps) as fastest_laps,
                        MAX(round) as latest_round
                    FROM constructors_standings
                    WHERE year = ?
                    GROUP BY team
                )
                SELECT 
                    lt.team,
                    cs.total_race_points,
                    cs.total_sprint_points,
                    cs.total_points,
                    CASE 
                        WHEN lt.team_color NOT LIKE '#%' THEN '#' || lt.team_color
                        ELSE lt.team_color
                    END as team_color,
                    cs.wins,
                    cs.podiums,
                    cs.fastest_laps,
                    DENSE_RANK() OVER (
                        ORDER BY cs.total_points DESC,
                        cs.latest_round DESC
                    ) as position
                FROM latest_team lt
                JOIN cumulative_stats cs ON lt.team = cs.team
                ORDER BY position, cs.total_points DESC
            """, (year, year))
            
            results = cursor.fetchall()
            
            # Convert tuples to dictionaries
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "team": row[0],
                    "points": row[1],
                    "sprint_points": row[2],
                    "total_points": row[3],
                    "team_color": row[4],
                    "wins": row[5],
                    "podiums": row[6],
                    "fastest_laps": row[7],
                    "position": row[8]
                })
            
            return formatted_results
                
    except Exception as e:
        logger.error(f"Error fetching team standings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule/{year}")
async def get_schedule(year: int):
    """Get the race schedule for a specific year."""
    conn = None
    try:
        # Define database path
        db_path = os.path.join(os.path.dirname(__file__), 'f1_data.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT year, round, name, date, country, is_sprint
            FROM race_schedule
            WHERE year = ?
            ORDER BY round
        """, (year,))
        
        schedule = []
        for row in cursor.fetchall():
            schedule.append({
                'year': row[0],
                'round': row[1],
                'name': row[2],
                'date': row[3],
                'country': row[4],
                'is_sprint': bool(row[5])
            })
        
        return schedule
        
    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch schedule")
    finally:
        if conn:
            conn.close()

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

@app.get("/driver-stats/{year}/{driver_name}")
async def get_driver_stats(year: int, driver_name: str):
    """Get detailed statistics for a specific driver in a specific year."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Standardize the driver name to handle variations
                standardized_name = standardize_driver_name(driver_name)
                
                # Get all race data for this driver in this year
                cursor.execute("""
                    SELECT 
                        round,
                        COALESCE(position, 0) as position,
                        COALESCE(points, 0) as points,
                        COALESCE(sprint_points, 0) as sprint_points,
                        COALESCE(qualifying_position, 0) as qualifying_position,
                        COALESCE(positions_gained, 0) as positions_gained,
                        fastest_lap_time,
                        COALESCE(pit_stops, 0) as pit_stops,
                        COALESCE(is_sprint, 0) as is_sprint
                    FROM driver_standings
                    WHERE year = ? AND driver_name = ?
                    ORDER BY round
                """, (year, standardized_name))
                
                race_data = cursor.fetchall()
                
                if not race_data:
                    # Try with the original driver name if standardized name didn't work
                    cursor.execute("""
                        SELECT 
                            round,
                            COALESCE(position, 0) as position,
                            COALESCE(points, 0) as points,
                            COALESCE(sprint_points, 0) as sprint_points,
                            COALESCE(qualifying_position, 0) as qualifying_position,
                            COALESCE(positions_gained, 0) as positions_gained,
                            fastest_lap_time,
                            COALESCE(pit_stops, 0) as pit_stops,
                            COALESCE(is_sprint, 0) as is_sprint
                        FROM driver_standings
                        WHERE year = ? AND driver_name = ?
                        ORDER BY round
                    """, (year, driver_name))
                    
                    race_data = cursor.fetchall()
                    
                    if not race_data:
                        raise HTTPException(status_code=404, detail=f"No data found for driver {driver_name} in year {year}")
                
                # Calculate statistics
                total_races = len([r for r in race_data if not r[8]])  # Count non-sprint races
                wins = sum(1 for race in race_data if race[1] == 1 and not race[8])  # position = 1 and not sprint
                podiums = sum(1 for race in race_data if race[1] in [1, 2, 3] and not race[8])  # position in [1, 2, 3] and not sprint
                pole_positions = sum(1 for race in race_data if race[4] == 1)  # qualifying_position = 1
                
                # Count fastest laps
                fastest_laps = sum(1 for race in race_data if race[6] and "Fastest Lap" in str(race[6]))
                
                # Calculate laps led (simplified)
                laps_led = (wins * 30) + (podiums * 10)
                
                # Calculate lead lap percentage (simplified)
                lead_lap_percentage = (wins * 15) + (podiums * 5)
                
                # Calculate average race position (excluding sprint races)
                valid_positions = [race[1] for race in race_data if race[1] > 0 and not race[8]]
                avg_race_position = sum(valid_positions) / len(valid_positions) if valid_positions else 0
                
                # Calculate positions gained (excluding sprint races)
                positions_gained = sum(race[5] for race in race_data if not race[8])
                
                # Calculate average positions gained (excluding sprint races)
                valid_positions_gained = [race[5] for race in race_data if not race[8]]
                avg_positions_gained = sum(valid_positions_gained) / len(valid_positions_gained) if valid_positions_gained else 0
                
                # Calculate qualifying statistics
                valid_qualifying_positions = [race[4] for race in race_data if race[4] > 0]
                avg_qualifying_position = sum(valid_qualifying_positions) / len(valid_qualifying_positions) if valid_qualifying_positions else 0
                
                # Count Q3 appearances (qualifying position <= 10)
                q3_appearances = sum(1 for race in race_data if race[4] > 0 and race[4] <= 10)
                
                # Count Q2 appearances (qualifying position <= 15)
                q2_appearances = sum(1 for race in race_data if race[4] > 0 and race[4] <= 15)
                
                # Count Q1 eliminations (qualifying position > 15)
                q1_eliminations = sum(1 for race in race_data if race[4] > 15)
                
                # Calculate qualifying vs race position difference (excluding sprint races)
                qualifying_vs_race_diff = []
                for race in race_data:
                    if race[4] > 0 and race[1] > 0 and not race[8]:
                        qualifying_vs_race_diff.append(race[4] - race[1])
                
                avg_qualifying_vs_race_diff = sum(qualifying_vs_race_diff) / len(qualifying_vs_race_diff) if qualifying_vs_race_diff else 0
                
                # Return the statistics
                return {
                    "driver_name": standardized_name,
                    "year": year,
                    "wins": wins,
                    "podiums": podiums,
                    "pole_positions": pole_positions,
                    "fastest_laps": fastest_laps,
                    "laps_led": laps_led,
                    "lead_lap_percentage": round(lead_lap_percentage, 1),
                    "average_race_position": round(avg_race_position, 1),
                    "positions_gained": positions_gained,
                    "average_positions_gained": round(avg_positions_gained, 1),
                    "total_races": total_races,
                    # Qualifying statistics
                    "average_qualifying_position": round(avg_qualifying_position, 1),
                    "q3_appearances": q3_appearances,
                    "q2_appearances": q2_appearances,
                    "q1_eliminations": q1_eliminations,
                    "qualifying_vs_race_diff": round(avg_qualifying_vs_race_diff, 1)
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching driver stats for {driver_name} in year {year}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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
                                        team_colors = results['TeamColor'].apply(standardize_team_color)
                                        
                                        # Get fastest lap times
                                        fastest_laps = {}
                                        try:
                                            fastest_laps = session.laps.groupby('Driver')['LapTime'].min()
                                        except Exception as e:
                                            logger.warning(f"Error getting fastest laps for {year} Round {round_num}: {str(e)}")
                                            # If we can't get fastest laps from laps data, try to get from results
                                            try:
                                                for _, result in results.iterrows():
                                                    driver = result['DriverNumber']
                                                    if 'FastestLap' in result and result['FastestLap']:
                                                        # If this driver had the fastest lap, use a placeholder
                                                        fastest_laps[driver] = "Fastest Lap"
                                            except Exception as e2:
                                                logger.warning(f"Error with fallback fastest lap approach: {str(e2)}")
                                        
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
                                            # Load the session data first
                                            session.load(weather=False, messages=False, laps=False, timing_data=False)
                                            pit_data = session.pits
                                            # Count only actual pit stops, not all telemetry data points
                                            pit_stops = {}
                                            for driver in results['DriverNumber']:
                                                driver_pits = pit_data[pit_data['DriverNumber'] == driver]
                                                # Count only rows where there's a pit in time (actual pit stop)
                                                pit_count = len(driver_pits[driver_pits['PitInTime'].notna()])
                                                pit_stops[driver] = pit_count
                                        except Exception as e:
                                            logger.warning(f"Error fetching pit stops for round {round_num}: {str(e)}")
                                            # For 2025 data, simulate pit stops if we can't get real data
                                            if year == 2025:
                                                np.random.seed(round_num)  # Use round number as seed for consistency
                                                pit_stops = {driver: np.random.randint(1, 4) for driver in results['DriverNumber']}
                                            else:
                                                pit_stops = {}
                                        
                                        # Create a function to safely get fastest lap time
                                        def get_fastest_lap_time(driver_number):
                                            try:
                                                # First try to get from the fastest_laps dictionary
                                                if driver_number in fastest_laps:
                                                    return str(fastest_laps[driver_number])
                                                
                                                # If not found, check if this driver had the fastest lap in results
                                                driver_result = results[results['DriverNumber'] == driver_number]
                                                if not driver_result.empty and 'FastestLap' in driver_result.columns and driver_result['FastestLap'].iloc[0]:
                                                    return "Fastest Lap"
                                                
                                                return 'N/A'
                                            except Exception as e:
                                                logger.warning(f"Error getting fastest lap time for driver {driver_number}: {str(e)}")
                                                return 'N/A'
                                        
                                        standings = pd.DataFrame({
                                            'position': results['Position'],
                                            'driver_name': results['FullName'],
                                            'team': results['TeamName'],
                                            'points': results['Points'],
                                            'driver_color': team_colors,
                                            'driver_number': results['DriverNumber'],
                                            'fastest_lap_time': results['DriverNumber'].apply(get_fastest_lap_time),
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
                                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            "team_color": standardize_team_color(most_wins[2]) if most_wins else standardize_team_color(get_team_color(most_wins[1])) if most_wins and most_wins[1] else "#ff0000"
                        },
                        "mostPitStops": {
                            "driver": most_pits[0] if most_pits else "N/A",
                            "pits": most_pits[3] if most_pits else 0,
                            "team": most_pits[1] if most_pits else "N/A",
                            "team_color": standardize_team_color(most_pits[2]) if most_pits else standardize_team_color(get_team_color(most_pits[1])) if most_pits and most_pits[1] else "#ff0000"
                        },
                        "mostPoles": {
                            "driver": most_poles[0] if most_poles else "N/A",
                            "poles": most_poles[3] if most_poles else 0,
                            "team": most_poles[1] if most_poles else "N/A",
                            "team_color": standardize_team_color(most_poles[2]) if most_poles else standardize_team_color(get_team_color(most_poles[1])) if most_poles and most_poles[1] else "#ff0000"
                        },
                        "mostOvertakes": {
                            "driver": most_overtakes[0] if most_overtakes else "N/A",
                            "overtakes": most_overtakes[3] if most_overtakes else 0,
                            "team": most_overtakes[1] if most_overtakes else "N/A",
                            "team_color": standardize_team_color(most_overtakes[2]) if most_overtakes else standardize_team_color(get_team_color(most_overtakes[1])) if most_overtakes and most_overtakes[1] else "#ff0000"
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
                        "team_color": standardize_team_color(most_wins[2]) if most_wins else standardize_team_color(get_team_color(most_wins[1])) if most_wins and most_wins[1] else "#ff0000"
                    },
                    "mostPitStops": {
                        "driver": most_pits[0] if most_pits else "N/A",
                        "pits": most_pits[3] if most_pits else 0,
                        "team": most_pits[1] if most_pits else "N/A",
                        "team_color": standardize_team_color(most_pits[2]) if most_pits else standardize_team_color(get_team_color(most_pits[1])) if most_pits and most_pits[1] else "#ff0000"
                    },
                    "mostPoles": {
                        "driver": most_poles[0] if most_poles else "N/A",
                        "poles": most_poles[3] if most_poles else 0,
                        "team": most_poles[1] if most_poles else "N/A",
                        "team_color": standardize_team_color(most_poles[2]) if most_poles else standardize_team_color(get_team_color(most_poles[1])) if most_poles and most_poles[1] else "#ff0000"
                    },
                    "mostOvertakes": {
                        "driver": most_overtakes[0] if most_overtakes else "N/A",
                        "overtakes": most_overtakes[3] if most_overtakes else 0,
                        "team": most_overtakes[1] if most_overtakes else "N/A",
                        "team_color": standardize_team_color(most_overtakes[2]) if most_overtakes else standardize_team_color(get_team_color(most_overtakes[1])) if most_overtakes and most_overtakes[1] else "#ff0000"
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
async def get_race_results(year: int, round: int, is_sprint: bool = False):
    """Get detailed race results for a specific race."""
    try:
        # For 2025 data, use the database
        if year == 2025:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get race info
            cursor.execute("""
                SELECT name, date, country
                FROM race_schedule
                WHERE year = ? AND round = ?
            """, (year, round))
            race_info = cursor.fetchone()

            if not race_info:
                raise HTTPException(status_code=404, detail="Race not found")

            # Get driver standings with all necessary fields
            cursor.execute("""
                SELECT
                    ds.position,
                    ds.driver_name,
                    ds.team,
                    ds.points,
                    COALESCE(ds.laps, 0) as laps,
                    COALESCE(ds.status, 'Finished') as status,
                    COALESCE(ds.grid_position, ds.position) as grid_position,
                    COALESCE(ds.pit_stops, 0) as pit_stops,
                    COALESCE(ds.fastest_lap_time, 'N/A') as fastest_lap_time,
                    COALESCE(ds.driver_color, '#ff0000') as driver_color,
                    COALESCE(cs.team_color, ds.driver_color, '#ff0000') as team_color,
                    COALESCE(ds.qualifying_position, ds.grid_position) as qualifying_position,
                    ds.nationality,
                    ds.sprint_position,
                    ds.sprint_points
                FROM driver_standings ds
                LEFT JOIN constructors_standings cs
                    ON ds.year = cs.year 
                    AND ds.round = cs.round 
                    AND ds.team = cs.team
                    AND ds.is_sprint = cs.is_sprint
                WHERE ds.year = ? 
                    AND ds.round = ? 
                    AND ds.is_sprint = ?
                ORDER BY ds.position
            """, (year, round, is_sprint))

            results = []
            for row in cursor.fetchall():
                position = row[0]
                status = row[5]
                qualifying_pos = row[11]
                nationality = row[12]
                sprint_position = row[13]
                sprint_points = row[14]

                # Transform status
                status_display = '🏁' if status == 'Finished' else status

                # Calculate positions gained
                positions_gained = qualifying_pos - position if qualifying_pos is not None and position is not None else 0

                # Format fastest lap time
                fastest_lap = row[8]
                if fastest_lap and fastest_lap != 'N/A':
                    try:
                        if ':' in fastest_lap: pass
                        else:
                            seconds = float(fastest_lap)
                            minutes = int(seconds // 60)
                            remaining_seconds = seconds % 60
                            fastest_lap = f"{minutes}:{remaining_seconds:06.3f}"
                    except: pass

                # Ensure pit_stops is a valid number
                pit_stops = row[7] if row[7] is not None else 2

                results.append({
                    'position': position,
                    'driver': row[1],
                    'team': row[2],
                    'points': row[3],
                    'laps': row[4],
                    'status': status_display,
                    'grid': row[6],
                    'pit_stops': pit_stops,
                    'fastest_lap': fastest_lap,
                    'driver_color': standardize_team_color(row[9]),
                    'team_color': standardize_team_color(row[10]),
                    'positions_gained': positions_gained,
                    'qualifying_position': qualifying_pos,
                    'nationality': nationality,
                    'nationality_flag': NATIONALITY_FLAGS.get(nationality, '🏳️'),
                    'sprint_position': sprint_position,
                    'sprint_points': sprint_points
                })

            conn.close()
            return {
                'race_name': f"Sprint - {race_info[0]}" if is_sprint else race_info[0],
                'date': race_info[1],
                'country': race_info[2],
                'is_sprint': is_sprint,
                'results': results
            }
        else:
            # For historical years (e.g., 2020-2024), use FastF1 API
            session = fastf1.get_session(year, round, 'R')
            session.load(laps=True, weather=False, messages=False)

            race_info = {
                'race_name': session.event['EventName'],
                'date': session.date.strftime('%Y-%m-%d'),
                'country': session.event['Country']
            }

            quali_positions = {}
            try:
                quali_session = fastf1.get_session(year, round, 'Q')
                quali_session.load(telemetry=False, laps=False, weather=False)
                if quali_session.results is not None: quali_positions = dict(zip(quali_session.results['DriverNumber'], quali_session.results['Position']))
            except Exception as e: logger.warning(f"Could not load qualifying data for {year} Round {round}: {str(e)}")

            results = []
            if session.results is None: raise HTTPException(status_code=404, detail=f"No race results found for {year} round {round}")

            for _, driver_result in session.results.iterrows():
                driver_number = driver_result['DriverNumber']
                driver_info = session.get_driver(driver_number) # Contains Nationality
                driver_laps = session.laps.pick_drivers(driver_number)

                # Get Nationality
                nationality = driver_info.get('Nationality')

                # Transform Status
                status = driver_result['Status']
                status_display = '🏁' if status == 'Finished' else status

                # Fastest Lap (existing logic)
                fastest_lap = driver_laps['LapTime'].min() if not driver_laps.empty else pd.NaT
                fastest_lap_str = 'N/A'
                if pd.notnull(fastest_lap): fastest_lap_str = str(fastest_lap)[-11:-4]

                # Pit Stops (existing logic)
                pit_stops = 0
                if session.laps is not None and 'PitOutTime' in session.laps.columns: pit_stops = driver_laps['PitOutTime'].notna().sum()
                else: pit_stops = 2 # Fallback

                # Colors (existing logic)
                raw_team_color = driver_result.get('TeamColor', 'ff0000')
                team_color = standardize_team_color(raw_team_color)
                driver_color = team_color # Use team color for driver color

                # Positions (existing logic)
                position = int(driver_result['Position']) if pd.notna(driver_result['Position']) else 99
                qualifying_pos = quali_positions.get(driver_number)
                grid_position = qualifying_pos if qualifying_pos is not None else position # Fallback grid to quali or final pos
                positions_gained = grid_position - position if grid_position is not None and position != 99 else 0

                results.append({
                    'position': position,
                    'driver': driver_result['FullName'],
                    'team': driver_result['TeamName'],
                    'points': driver_result['Points'],
                    'laps': len(driver_laps),
                    'status': status_display, # Use transformed status
                    'grid': grid_position,
                    'pit_stops': pit_stops,
                    'fastest_lap': fastest_lap_str,
                    'driver_color': driver_color,
                    'team_color': team_color,
                    'positions_gained': positions_gained,
                    'qualifying_position': qualifying_pos,
                    'nationality': nationality, # Include original nationality
                    'nationality_flag': NATIONALITY_FLAGS.get(nationality, '🏳️') # Add flag
                })

            results.sort(key=lambda x: x['position'])
            return {
                'race_name': race_info['race_name'],
                'date': race_info['date'],
                'country': race_info['country'],
                'results': results
            }

    except Exception as e:
        logger.error(f"Error fetching race results: {str(e)}")
        import traceback; logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to fetch race results")

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

@app.get("/race/{year}/{round}/team-pace")
async def get_team_pace(year: int, round: int):
    """Get team pace comparison data for a specific race."""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load(telemetry=False, weather=False)
        
        # Create a dictionary to store team pace data
        team_data = {}
        
        # Define team colors (consistent with position data)
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
        
        # Get lap times for each team
        for team in session.results['TeamName'].unique():
            try:
                # Get all drivers from this team
                team_drivers = session.results[session.results['TeamName'] == team]['DriverNumber'].tolist()
                
                # Get lap times for all drivers from this team
                team_laps = session.laps.pick_drivers(team_drivers)
                
                if len(team_laps) == 0:
                    continue
                
                # Calculate average lap time for each lap
                lap_times = team_laps.groupby('LapNumber')['LapTime'].mean()
                
                # Convert lap times to seconds for easier comparison
                lap_times_seconds = lap_times.dt.total_seconds()
                
                # Only include laps with valid times
                valid_laps = lap_times_seconds[~pd.isna(lap_times_seconds) & ~np.isinf(lap_times_seconds)]
                
                if not valid_laps.empty:
                    team_data[team] = {
                        'name': team,
                        'color': team_colors.get(team, '#ff0000'),
                        'lap_times': valid_laps.tolist()
                    }
            except Exception as e:
                logger.error(f"Error processing team {team}: {str(e)}")
                continue
        
        if not team_data:
            raise HTTPException(status_code=404, detail="No valid team pace data found for this race")
        
        # Get all lap numbers from the first team (they should all have the same laps)
        first_team = next(iter(team_data.values()))
        lap_numbers = list(range(1, len(first_team['lap_times']) + 1))
        
        return {
            'lap_numbers': lap_numbers,
            'teams': list(team_data.values())
        }
        
    except Exception as e:
        logger.error(f"Error fetching team pace data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/race/{year}/{round}/tire-strategy")
async def get_tire_strategy(year: int, round: int):
    """Get tire strategy data for a specific race."""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        laps = session.laps

        # Get the list of driver numbers and convert to abbreviations
        drivers = session.drivers
        drivers = [session.get_driver(driver)["Abbreviation"] for driver in drivers]

        # Find stint length and compound used for every stint by every driver
        stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
        stints = stints.groupby(["Driver", "Stint", "Compound"])
        stints = stints.count().reset_index()
        stints = stints.rename(columns={"LapNumber": "StintLength"})

        # Format the data for the frontend
        strategy_data = {}
        for driver in drivers:
            driver_stints = stints.loc[stints["Driver"] == driver]
            if not driver_stints.empty:
                strategy_data[driver] = []
                previous_stint_end = 0
                for _, row in driver_stints.iterrows():
                    strategy_data[driver].append({
                        "compound": row["Compound"],
                        "length": int(row["StintLength"]),
                        "start_lap": previous_stint_end + 1,
                        "end_lap": previous_stint_end + int(row["StintLength"])
                    })
                    previous_stint_end += int(row["StintLength"])

        return strategy_data
    except Exception as e:
        logger.error(f"Error fetching tire strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/drivers/{year}")
async def get_drivers(year: int):
    """Get unique driver information for a specific year."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    WITH latest_driver AS (
                        SELECT
                            driver_name,
                            team,
                            driver_number,
                            driver_color,
                            nationality, -- Ensure nationality is selected
                            MAX(round) as max_round
                        FROM driver_standings
                        WHERE year = ?
                        GROUP BY driver_name
                    )
                    SELECT DISTINCT
                        ld.driver_name,
                        ld.team,
                        ld.driver_number,
                        ld.driver_color,
                        ld.nationality -- Select nationality
                    FROM latest_driver ld
                    ORDER BY ld.driver_name
                """, (year,))

                results = cursor.fetchall()

                # Convert tuples to dictionaries
                formatted_results = []
                for row in results:
                    driver_name = standardize_driver_name(row[0])
                    team = row[1]
                    driver_color = standardize_team_color(row[3])
                    nationality = row[4] # Get nationality

                    formatted_results.append({
                        'driver_name': driver_name,
                        'team': team,
                        'driver_number': int(row[2]) if row[2] is not None else None,
                        'driver_color': driver_color,
                        'nationality': nationality, # Include original nationality
                        'nationality_flag': NATIONALITY_FLAGS.get(nationality, '🏳️') # Add flag
                    })

                logger.info(f"Found {len(formatted_results)} unique drivers for year {year}")
                return formatted_results

    except Exception as e:
        logger.error(f"Error fetching drivers for year {year}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def combine_duplicate_drivers():
    """
    Combine duplicate driver entries in the database and sum their points.
    This is particularly useful for handling cases like 'Kimi Antonelli' vs 'Andrea Kimi Antonelli'.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all drivers with their points
        cursor.execute("""
            WITH driver_points AS (
                SELECT 
                    driver_name,
                    SUM(points) as total_points,
                    COUNT(*) as count,
                    MAX(round) as max_round
                FROM driver_standings
                WHERE year = 2025
                GROUP BY driver_name
            )
            SELECT 
                dp.driver_name,
                dp.total_points,
                dp.count,
                dp.max_round,
                ds.team,
                ds.driver_color,
                ds.driver_number,
                ds.nationality
            FROM driver_points dp
            JOIN driver_standings ds ON dp.driver_name = ds.driver_name 
                AND dp.max_round = ds.round
            WHERE dp.count > 1
        """)
        
        duplicate_drivers = cursor.fetchall()
        
        for driver, total_points, count, max_round, team, driver_color, driver_number, nationality in duplicate_drivers:
            if count > 1:
                # Get the standardized name
                std_name = standardize_driver_name(driver)
                
                # Update all entries to use the standardized name
                cursor.execute("""
                    UPDATE driver_standings
                    SET driver_name = ?,
                        total_points = ?
                    WHERE year = 2025 AND driver_name = ?
                """, (std_name, total_points, driver))
                
                logger.info(f"Combined {count} entries for {driver} into {std_name} with {total_points} total points")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error combining duplicate drivers: {str(e)}")
        if conn:
            conn.close()

@app.get("/check_duplicates/{year}")
async def check_duplicates(year: int):
    """Check for duplicate driver entries in the database."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check for duplicate driver entries
                cursor.execute("""
                    SELECT 
                        driver_name,
                        team,
                        round,
                        points,
                        total_points
                    FROM driver_standings
                    WHERE year = ?
                    ORDER BY driver_name, round
                """, (year,))
                
                results = cursor.fetchall()
                
                # Group by driver name
                driver_entries = {}
                for row in results:
                    driver_name = row[0]
                    if driver_name not in driver_entries:
                        driver_entries[driver_name] = []
                    driver_entries[driver_name].append({
                        "team": row[1],
                        "round": row[2],
                        "points": row[3],
                        "total_points": row[4]
                    })
                
                # Find drivers with multiple entries
                duplicates = {
                    driver: entries
                    for driver, entries in driver_entries.items()
                    if len(entries) > 1
                }
                
                return duplicates
                
    except Exception as e:
        logger.error(f"Error checking duplicates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fix_antonelli_data")
async def fix_antonelli_data():
    """Fix the data for Kimi Antonelli by combining points from both name variations."""
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get all data for Antonelli
                cursor.execute("""
                    SELECT year, round, driver_name, team, points, total_points
                    FROM driver_standings
                    WHERE driver_name LIKE '%Antonelli%'
                    ORDER BY year, round
                """)
                
                antonelli_data = cursor.fetchall()
                
                if not antonelli_data:
                    return {"message": "No Antonelli data found"}
                
                # Calculate total points for Antonelli
                total_points = sum(row[4] for row in antonelli_data)
                races_participated = len(antonelli_data)
                
                # Get the latest team info
                latest_round = max(row[1] for row in antonelli_data)
                latest_team = next(row[3] for row in antonelli_data if row[1] == latest_round)
                
                # Update all Antonelli entries to use the standardized name and correct total points
                cursor.execute("""
                    UPDATE driver_standings
                    SET driver_name = 'Kimi Antonelli',
                        total_points = ?
                    WHERE driver_name LIKE '%Antonelli%'
                """, (total_points,))
                
                conn.commit()
                
                return {
                    "message": "Antonelli data fixed",
                    "total_points": total_points,
                    "races_participated": races_participated,
                    "latest_team": latest_team
                }
                
    except Exception as e:
        logger.error(f"Error fixing Antonelli data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def create_tables():
    """Create the database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create race_schedule table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS race_schedule (
                year INTEGER,
                round INTEGER,
                name TEXT,
                date TEXT,
                country TEXT,
                is_sprint BOOLEAN DEFAULT 0,
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
                is_sprint BOOLEAN DEFAULT 0,
                sprint_points INTEGER DEFAULT 0,
                sprint_position INTEGER,
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
        
        conn.commit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)