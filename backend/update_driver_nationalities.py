import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path - use the path in the Docker container
db_path = '/app/data/f1_data.db'

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

def update_driver_nationalities():
    """Update driver nationalities in the database."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
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
        
        conn.commit()
        logger.info(f"Updated nationalities for {updated_count} drivers")
        
    except Exception as e:
        logger.error(f"Error updating driver nationalities: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_driver_nationalities() 