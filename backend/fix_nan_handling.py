import sqlite3
import os
import pandas as pd
import numpy as np
import fastf1
import json

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'f1_data.db')

def fix_race_positions():
    """Fix the race positions data by properly handling NaN values."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all race positions
    cursor.execute("SELECT year, round, driver_abbr, positions FROM race_positions")
    results = cursor.fetchall()
    
    for year, round_num, driver_abbr, positions_str in results:
        try:
            # Convert string to list
            positions = eval(positions_str)
            
            # Convert any NaN or infinite values to None
            fixed_positions = [None if pd.isna(pos) or np.isinf(pos) else float(pos) for pos in positions]
            
            # Update the database
            cursor.execute("""
                UPDATE race_positions
                SET positions = ?
                WHERE year = ? AND round = ? AND driver_abbr = ?
            """, (str(fixed_positions), year, round_num, driver_abbr))
            
            print(f"Fixed positions for {driver_abbr} in {year} round {round_num}")
        except Exception as e:
            print(f"Error fixing positions for {driver_abbr} in {year} round {round_num}: {str(e)}")
    
    conn.commit()
    conn.close()

def fetch_and_store_race_positions(year, round_num):
    """Fetch race positions from FastF1 and store in database with proper NaN handling."""
    try:
        # Get the session data
        session = fastf1.get_session(year, round_num, 'R')
        session.load(telemetry=False, weather=False)
        
        # Create a dictionary to store position data for each driver
        position_data = {}
        
        # Define team colors
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
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
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
                    
                    # Delete existing data for this driver in this race
                    cursor.execute("""
                        DELETE FROM race_positions
                        WHERE year = ? AND round = ? AND driver_abbr = ?
                    """, (year, round_num, abb))
                    
                    # Store in database
                    cursor.execute("""
                        INSERT INTO race_positions (
                            year, round, driver_abbr, positions, lap_numbers,
                            color, driver_name, team
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        year, round_num, abb,
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
        conn.close()
        
        print(f"Successfully fetched and stored race positions for {year} round {round_num}")
        return position_data
    except Exception as e:
        print(f"Error fetching race positions: {str(e)}")
        return None

if __name__ == "__main__":
    # Fix existing data
    fix_race_positions()
    
    # Fetch and store data for specific races
    # Example: Australian Grand Prix 2025 (round 1)
    fetch_and_store_race_positions(2025, 1) 