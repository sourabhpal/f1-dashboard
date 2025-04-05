# F1 Dashboard

A modern web application for Formula 1 fans to view race data, driver standings, team statistics, and more. Built with Next.js, FastAPI, and FastF1.

## Features

- 🏎️ Real-time driver standings with modern Oxanium font styling
- 🏆 Team statistics and points with team logos
- 📅 Race schedule with country flags
- ⏱️ Race timing and qualifying data
- 🔄 Pit stop information
- 🌤️ Race weather conditions
- 📊 Detailed driver statistics
- 🎨 Modern, responsive UI with dark theme
- 🔄 Automatic database schema versioning
- 📱 Mobile-friendly design

## Prerequisites

- Python 3.8 or higher
- Node.js 16.x or higher
- npm or yarn package manager
- Git
- SQLite3

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd f1-dashboard
```

### 2. Backend Setup

1. Create and activate a Python virtual environment:

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

2. Install Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Set up FastF1 cache directory:

```bash
# Create cache directory
mkdir -p backend/cache

# Set appropriate permissions (on Unix-based systems)
chmod 755 backend/cache
```

4. Initialize the Database:

```bash
# Make sure you're in the backend directory
python populate_2025_data.py
```

This script will:
- Create the SQLite database with proper schema
- Populate it with 2025 season data from FastF1
- Set up automatic schema versioning
- Handle database rebuilds when needed

### 3. Frontend Setup

1. Install Node.js dependencies:

```bash
cd frontend
npm install
# or
yarn install
```

2. Add Team Logos:
Place team logo images in `frontend/public/images/teams/` with the following naming convention:
- `red-bull.png`
- `mercedes.png`
- `ferrari.png`
- `mclaren.png`
- `aston-martin.png`
- `alpine.png`
- `williams.png`
- `alphatauri.png`
- `alfa-romeo.png`
- `haas.png`
- `default-team.png` (fallback image)

## Running the Application

### 1. Start the Backend Server

```bash
# Make sure you're in the backend directory and virtual environment is activated
cd backend
uvicorn f1_backend:app --reload --port 8000
```

The backend server will start on `http://localhost:8000`

### 2. Start the Frontend Development Server

```bash
# In a new terminal, navigate to the frontend directory
cd frontend
npm run dev
# or
yarn dev
```

The frontend application will start on `http://localhost:3000`

## Project Structure

```
f1-dashboard/
├── backend/
│   ├── f1_backend.py          # FastAPI backend server
│   ├── populate_2025_data.py  # Database initialization script
│   ├── f1_data.db            # SQLite database
│   ├── cache/                # FastF1 cache directory
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── pages/               # Next.js pages
│   ├── components/          # React components
│   ├── public/             # Static assets
│   │   └── images/        # Images including team logos
│   └── styles/            # CSS styles
└── README.md
```

## Database Schema

The application uses SQLite with the following main tables:

- `driver_standings`: Stores driver race results and points
- `constructors_standings`: Stores team race results and points
- `race_schedule`: Contains race calendar information
- `circuits`: Stores circuit information
- `schema_version`: Tracks database schema version

## Features in Detail

### Automatic Database Management
- Schema version tracking
- Automatic database rebuilds when needed
- Data validation and integrity checks
- Efficient caching of FastF1 data

### Modern UI Elements
- Space-inspired Oxanium font for numerical data
- Team logos with transparency support
- Smooth animations and transitions
- Responsive design for all screen sizes

### Real-time Data
- Live race timing
- Up-to-date standings
- Weather conditions
- Pit stop information

## Dependencies

### Backend Dependencies
- fastapi
- uvicorn
- fastf1
- pandas
- numpy
- python-multipart
- sqlite3

### Frontend Dependencies
- next
- react
- react-dom
- framer-motion
- tailwindcss
- postcss
- autoprefixer

## Environment Variables

No environment variables are required for basic setup. The application uses default configurations for local development.

## Caching

FastF1 uses a local cache to store race data. The cache directory is located at `backend/cache/`. This helps reduce API calls and improves performance.

## Troubleshooting

### Common Issues

1. **FastF1 Cache Permission Errors**
   ```bash
   # Fix cache directory permissions
   chmod -R 755 backend/cache
   ```

2. **Database Lock Errors**
   - Ensure no other process is using the database
   - Delete the database file and restart the application:
     ```bash
     rm backend/f1_data.db*
     ```

3. **Port Conflicts**
   - If port 8000 is in use, modify the backend startup command:
     ```bash
     uvicorn f1_backend:app --reload --port 8001
     ```
   - Update the frontend API URL accordingly

### Logging

- Backend logs are displayed in the terminal where the backend server is running
- Frontend logs are available in the browser's developer console

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [FastF1](https://github.com/theOehrly/Fast-F1) for providing F1 timing data
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework
- [Tailwind CSS](https://tailwindcss.com/) for styling 