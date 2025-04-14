import sqlite3
import logging
import time
from f1_backend import get_db_connection, calculate_points, standardize_driver_name
import fastf1
import os
import pandas as pd
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up FastF1 cache
cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

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

def validate_sprint_data():
    """Validate that sprint data was processed correctly."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all sprint races
            cursor.execute("""
                SELECT year, round, name
                FROM race_schedule
                WHERE is_sprint = 1
            """)
            
            sprint_races = cursor.fetchall()
            
            for year, round_num, race_name in sprint_races:
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

def repair_sprint_data():
    """Repair missing or incorrect sprint data."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all sprint races
            cursor.execute("""
                SELECT year, round, name
                FROM race_schedule
                WHERE is_sprint = 1
            """)
            
            sprint_races = cursor.fetchall()
            
            for year, round_num, race_name in sprint_races:
                try:
                    logger.info(f"Repairing sprint data for {race_name} (Round {round_num})")
                    
                    # Load sprint session data
                    session = load_session_data(year, round_num, 'S')
                    if not session:
                        logger.error(f"Could not load sprint session for Round {round_num}")
                        continue
                    
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
                            
                        except sqlite3.OperationalError as e:
                            if "database is locked" in str(e):
                                logger.warning(f"Database locked while processing {driver.get('FullName', 'Unknown')}, retrying...")
                                time.sleep(1)  # Wait a bit before retrying
                                continue
                            else:
                                logger.error(f"Error processing driver {driver.get('FullName', 'Unknown')}: {str(e)}")
                                continue
                        except Exception as e:
                            logger.error(f"Error processing driver {driver.get('FullName', 'Unknown')}: {str(e)}")
                            continue
                    
                    # Commit the transaction for this race
                    conn.commit()
                    logger.info(f"Successfully repaired sprint data for Round {round_num}")
                    
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        logger.warning(f"Database locked while processing Round {round_num}, retrying...")
                        time.sleep(2)  # Wait longer before retrying the entire race
                        continue
                    else:
                        logger.error(f"Error repairing sprint data for Round {round_num}: {str(e)}")
                        conn.rollback()
                        continue
                except Exception as e:
                    logger.error(f"Error repairing sprint data for Round {round_num}: {str(e)}")
                    conn.rollback()
                    continue
            
            return True
            
    except Exception as e:
        logger.error(f"Error in repair_sprint_data: {str(e)}")
        return False

def update_total_points(cursor, year):
    """Update total points for drivers and teams."""
    try:
        # Update driver total points
        cursor.execute("""
            UPDATE driver_standings
            SET total_points = (
                SELECT SUM(points + sprint_points)
                FROM driver_standings ds2
                WHERE ds2.year = driver_standings.year
                AND ds2.driver_name = driver_standings.driver_name
                AND ds2.round <= driver_standings.round
            )
            WHERE year = ?
        """, (year,))
        
        # Update team total points
        cursor.execute("""
            UPDATE constructors_standings
            SET total_points = (
                SELECT SUM(points + sprint_points)
                FROM constructors_standings cs2
                WHERE cs2.year = constructors_standings.year
                AND cs2.team = constructors_standings.team
                AND cs2.round <= constructors_standings.round
            )
            WHERE year = ?
        """, (year,))
        
        logger.info("Successfully updated total points")
        
    except Exception as e:
        logger.error(f"Error updating total points: {str(e)}")
        raise

def main():
    """Main function to validate and repair sprint data."""
    try:
        # Validate sprint data
        if not validate_sprint_data():
            logger.info("Issues found in sprint data, attempting to repair...")
            repair_sprint_data()
        else:
            logger.info("Sprint data validation successful")
            
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise

if __name__ == "__main__":
    main() 