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
                    # Convert stored JSON strings back to lists
                    position_data = {}
                    for row in results:
                        position_data[row[0]] = {
                            'positions': eval(row[1]),  # Convert string back to list
                            'lap_numbers': eval(row[2]),  # Convert string back to list
                            'color': row[3],
                            'driver_name': row[4],
                            'team': row[5]
                        }
                    return position_data
                
                # If not in database, fetch from FastF1
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
                                INSERT INTO race_positions (
                                    year, round, driver_abbr, positions, lap_numbers,
                                    color, driver_name, team
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                year, round, abb,
                                str(positions),  # Convert list to string for storage
                                str(lap_numbers),  # Convert list to string for storage
                                color,
                                drv_laps['Driver'].iloc[0],
                                team
                            ))
                    except Exception as e:
                        print(f"Error processing driver {drv}: {str(e)}")
                        continue
                
                conn.commit()
                
                if not position_data:
                    raise HTTPException(status_code=404, detail="No valid position data found for this race")
                    
                return position_data
                
    except Exception as e:
        print(f"Error in get_race_positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 