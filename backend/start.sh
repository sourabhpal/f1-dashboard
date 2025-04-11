#!/bin/bash

# Check if database exists and has the expected number of races
if [ ! -f /app/data/f1_data.db ] || [ $(sqlite3 /app/data/f1_data.db "SELECT COUNT(*) FROM race_schedule WHERE year = 2025" 2>/dev/null || echo 0) -lt 24 ]; then
  echo "Database needs to be populated or updated..."
  python populate_2025_data.py
else
  echo "Database already populated."
fi

# Start the application
exec uvicorn f1_backend:app --host 0.0.0.0 --port 8000 