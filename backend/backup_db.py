import os
import shutil
import sqlite3
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database paths
DB_PATH = '/app/data/f1_data.db'
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

def create_backup():
    """Create a backup of the current database with timestamp."""
    try:
        # Create backups directory if it doesn't exist
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Generate timestamp for backup name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(BACKUP_DIR, f'f1_data_{timestamp}.db')
        
        # Create backup
        shutil.copy2(DB_PATH, backup_path)
        
        # Save backup metadata
        metadata = {
            'timestamp': timestamp,
            'original_path': DB_PATH,
            'backup_path': backup_path,
            'schema_version': get_schema_version()
        }
        
        metadata_path = os.path.join(BACKUP_DIR, f'f1_data_{timestamp}_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Successfully created backup at {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise

def restore_backup(backup_path=None):
    """Restore database from a backup."""
    try:
        if backup_path is None:
            # Get the most recent backup
            backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
            if not backups:
                raise FileNotFoundError("No backups found")
            
            # Sort by timestamp in filename
            backups.sort(reverse=True)
            backup_path = os.path.join(BACKUP_DIR, backups[0])
        
        # Create a temporary backup of current database
        temp_backup = DB_PATH + '.temp'
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, temp_backup)
        
        try:
            # Restore from backup
            shutil.copy2(backup_path, DB_PATH)
            logger.info(f"Successfully restored database from {backup_path}")
            
            # Remove temporary backup
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
                
        except Exception as e:
            # Restore from temporary backup if something goes wrong
            if os.path.exists(temp_backup):
                shutil.copy2(temp_backup, DB_PATH)
                logger.info("Restored from temporary backup due to error")
            raise e
            
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        raise

def get_schema_version():
    """Get the current schema version from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM schema_version")
        version = cursor.fetchone()[0]
        conn.close()
        return version
    except Exception as e:
        logger.error(f"Error getting schema version: {str(e)}")
        return None

def list_backups():
    """List all available backups with their metadata."""
    try:
        backups = []
        for f in os.listdir(BACKUP_DIR):
            if f.endswith('_metadata.json'):
                metadata_path = os.path.join(BACKUP_DIR, f)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    backups.append(metadata)
        
        # Sort by timestamp
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
        
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        return []

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Database backup and restore utility')
    parser.add_argument('action', choices=['backup', 'restore', 'list'],
                      help='Action to perform: backup, restore, or list backups')
    parser.add_argument('--backup-path', help='Path to specific backup file for restore')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        create_backup()
    elif args.action == 'restore':
        restore_backup(args.backup_path)
    elif args.action == 'list':
        backups = list_backups()
        if backups:
            print("\nAvailable backups:")
            for backup in backups:
                print(f"\nTimestamp: {backup['timestamp']}")
                print(f"Schema Version: {backup['schema_version']}")
                print(f"Backup Path: {backup['backup_path']}")
        else:
            print("No backups found") 