import fastf1
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up FastF1 cache
cache_dir = 'cache'
fastf1.Cache.enable_cache(cache_dir)

def test_driver_nationality():
    """Test if FastF1 provides nationality data for drivers."""
    try:
        # Load a session
        session = fastf1.get_session(2025, 1, 'R')
        session.load(weather=False, messages=False)
        
        # Get results
        results = session.results
        
        # Print driver info
        for _, result in results.iterrows():
            driver = result['DriverNumber']
            driver_info = session.get_driver(driver)
            
            logger.info(f"Driver: {driver_info['FullName']}")
            logger.info(f"Nationality: {driver_info.get('Nationality', 'Unknown')}")
            logger.info(f"All driver info: {driver_info}")
            logger.info("-" * 50)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    test_driver_nationality() 