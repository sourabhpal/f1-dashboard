# F1 Dashboard

A modern Formula 1 dashboard application that provides real-time race data, schedules, and statistics.

## Features

- Real-time race data visualization
- Race schedule with year selection (2020-2025)
- Driver and constructor standings
- Circuit information
- Race results with detailed statistics
- Dark modern UI with responsive design

## Tech Stack

- **Frontend**: Next.js, React, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, FastF1, SQLite
- **Deployment**: Docker, Docker Compose

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js](https://nodejs.org/) (v14 or later) - for local development
- [Python](https://www.python.org/) (v3.9 or later) - for local development

## Docker Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/f1-dashboard.git
cd f1-dashboard
```

### 2. Build and run with Docker Compose

```bash
# Build and start the containers
docker-compose up --build
```

This will:
- Build both frontend and backend containers
- Start both services
- Set up the networking between them
- Mount the necessary volumes

### 3. Access the application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Local Development Setup

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   ```

5. Populate historical data (optional):
   ```bash
   python populate_historical_data.py
   ```

6. Start the backend server:
   ```bash
   uvicorn f1_backend:app --reload
   ```

### Database Backup and Restore

The application includes a database backup utility that allows you to create, restore, and manage backups of your F1 data.

#### Creating a Backup

To create a backup of the current database:

```bash
python3 backend/backup_db.py backup
```

This will:
- Create a timestamped backup in the `backend/backups` directory
- Save metadata about the backup including schema version
- Log the backup creation process

#### Restoring from a Backup

To restore from the most recent backup:

```bash
python3 backend/backup_db.py restore
```

To restore from a specific backup:

```bash
python3 backend/backup_db.py restore --backup-path /path/to/backup.db
```

#### Listing Available Backups

To view all available backups:

```bash
python3 backend/backup_db.py list
```

This will display:
- Timestamp of each backup
- Schema version
- Backup file path

#### Backup Safety Features

- Automatic creation of temporary backups during restore operations
- Rollback to previous state if restore fails
- Metadata tracking for each backup
- Timestamp-based versioning

## Docker Commands

### Basic Commands

```bash
# Start the containers
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop the containers
docker-compose down

# View logs
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f frontend
docker-compose logs -f backend
```

### Development Commands

```bash
# Rebuild a specific service
docker-compose up --build frontend
docker-compose up --build backend

# Access container shell
docker-compose exec frontend sh
docker-compose exec backend sh

# Run a command in the container
docker-compose exec backend python populate_historical_data.py
```

### Troubleshooting

```bash
# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up

# Check container status
docker-compose ps

# View container logs
docker-compose logs
```

## Project Structure

```
f1-dashboard/
├── frontend/                # Next.js frontend
│   ├── components/          # React components
│   ├── pages/               # Next.js pages
│   ├── public/              # Static assets
│   ├── styles/              # CSS styles
│   ├── Dockerfile           # Frontend Docker configuration
│   └── package.json         # Frontend dependencies
├── backend/                 # FastAPI backend
│   ├── f1_backend.py        # Main backend application
│   ├── init_db.py           # Database initialization
│   ├── populate_historical_data.py  # Data population script
│   ├── f1_data.db           # SQLite database
│   ├── Dockerfile           # Backend Docker configuration
│   └── requirements.txt     # Backend dependencies
└── docker-compose.yml       # Docker Compose configuration
```

## Dependencies

### Frontend Dependencies

- Next.js
- React
- React DOM
- Tailwind CSS
- Framer Motion
- Axios
- Chart.js
- React Chart.js 2

### Backend Dependencies

- FastAPI
- Uvicorn
- FastF1
- Pandas
- NumPy
- SQLite3
- Python-dotenv

## License

MIT 