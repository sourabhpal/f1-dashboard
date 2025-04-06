#!/bin/bash

# Stop any running containers
echo "Stopping any running containers..."
docker-compose down

# Start the application without watch functionality
echo "Starting the application..."
docker-compose up -d

# Show initial logs
echo "Showing logs (press Ctrl+C to stop watching, containers will continue running)..."
echo "Watching for changes to backend and frontend files..."

# Function to rebuild backend
rebuild_backend() {
  echo "Changes detected in backend files, rebuilding backend..."
  docker-compose stop backend
  docker-compose rm -f backend
  docker-compose up -d --build backend
  echo "Backend rebuilt successfully!"
}

# Function to rebuild frontend
rebuild_frontend() {
  echo "Changes detected in frontend files, rebuilding frontend..."
  docker-compose stop frontend
  docker-compose rm -f frontend
  docker-compose up -d --build frontend
  echo "Frontend rebuilt successfully!"
}

# Get the initial modification times for backend files
backend_last_modified=$(find backend -type f -name "*.py" -exec stat -f %m {} \; 2>/dev/null || find backend -type f -name "*.py" -exec stat -c %Y {} \;)

# Get the initial modification times for frontend pages directory
pages_last_modified=$(find frontend/pages -type f -exec stat -f %m {} \; 2>/dev/null || find frontend/pages -type f -exec stat -c %Y {} \;)

# Get the initial modification times for frontend components directory
components_last_modified=$(find frontend/components -type f -exec stat -f %m {} \; 2>/dev/null || find frontend/components -type f -exec stat -c %Y {} \;)

# Watch for changes to backend and frontend files
while true; do
  # Check if backend files have been modified
  backend_current_modified=$(find backend -type f -name "*.py" -exec stat -f %m {} \; 2>/dev/null || find backend -type f -name "*.py" -exec stat -c %Y {} \;)
  
  # Check if frontend pages files have been modified
  pages_current_modified=$(find frontend/pages -type f -exec stat -f %m {} \; 2>/dev/null || find frontend/pages -type f -exec stat -c %Y {} \;)
  
  # Check if frontend components files have been modified
  components_current_modified=$(find frontend/components -type f -exec stat -f %m {} \; 2>/dev/null || find frontend/components -type f -exec stat -c %Y {} \;)
  
  if [ "$backend_current_modified" != "$backend_last_modified" ]; then
    rebuild_backend
    backend_last_modified=$backend_current_modified
  fi
  
  if [ "$pages_current_modified" != "$pages_last_modified" ] || [ "$components_current_modified" != "$components_last_modified" ]; then
    rebuild_frontend
    pages_last_modified=$pages_current_modified
    components_last_modified=$components_current_modified
  fi
  
  # Sleep for a short time to avoid high CPU usage
  sleep 1
done 