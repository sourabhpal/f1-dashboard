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
   python f1_backend.py
   ```

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