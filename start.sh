#!/bin/bash

# Stop any running containers
echo "Stopping any running containers..."
docker-compose down

# Start the application
echo "Starting the application..."
docker-compose up -d

# Show logs
echo "Showing logs (press Ctrl+C to stop viewing logs, containers will continue running)..."
docker-compose logs -f 