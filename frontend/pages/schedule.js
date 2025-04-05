import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';
import Navbar from '../components/Navbar';
import RaceResultsModal from '../components/RaceResultsModal';

// Country flag mapping
const countryFlags = {
  'Australia': '🇦🇺',
  'China': '🇨🇳',
  'Japan': '🇯🇵',
  'Bahrain': '🇧🇭',
  'Saudi Arabia': '🇸🇦',
  'United States': '🇺🇸',
  'Monaco': '🇲🇨',
  'Italy': '🇮🇹',
  'Canada': '🇨🇦',
  'Spain': '🇪🇸',
  'Austria': '🇦🇹',
  'United Kingdom': '🇬🇧',
  'Hungary': '🇭🇺',
  'Belgium': '🇧🇪',
  'Netherlands': '🇳🇱',
  'Singapore': '🇸🇬',
  'Mexico': '🇲🇽',
  'Brazil': '🇧🇷',
  'Qatar': '🇶🇦',
  'Abu Dhabi': '🇦🇪',
  'United Arab Emirates': '🇦🇪'
};

// Format date to be more readable
const formatDate = (dateStr) => {
  if (!dateStr || dateStr === 'Unknown') return 'TBD';
  try {
    // Parse the date string and ensure it's treated as UTC
    const date = new Date(dateStr + 'T00:00:00Z');
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      timeZone: 'UTC'  // Ensure we're using UTC to avoid timezone shifts
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'TBD';
  }
};

const Schedule = () => {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRace, setSelectedRace] = useState(null);
  const [raceResults, setRaceResults] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const fetchSchedule = async () => {
      try {
        const response = await fetch('http://localhost:8000/schedule/2025');
        if (!response.ok) {
          throw new Error('Failed to fetch schedule');
        }
        const data = await response.json();
        setSchedule(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSchedule();
  }, []);

  const handleRaceClick = async (race) => {
    try {
      const response = await fetch(`http://localhost:8000/race-results/2025/${race.round}`);
      if (!response.ok) {
        throw new Error('Failed to fetch race results');
      }
      const data = await response.json();
      setRaceResults(data);
      setSelectedRace(race);
      setIsModalOpen(true);
    } catch (error) {
      console.error('Error fetching race results:', error);
      setError('Failed to load race results');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Head>
        <title>F1 Schedule 2025 | F1 Dashboard</title>
        <meta name="description" content="Formula 1 race schedule for the 2025 season" />
      </Head>

      <Navbar />

      <main className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-white mb-8">2025 F1 Race Schedule</h1>
          
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
            </div>
          ) : error ? (
            <div className="text-red-500 text-xl">Error: {error}</div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {schedule.map((race, index) => (
                <motion.div
                  key={race.round}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-300 cursor-pointer"
                  onClick={() => handleRaceClick(race)}
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl font-bold text-red-500">#{race.round}</span>
                    <span className="text-gray-400 text-sm">{formatDate(race.date)}</span>
                  </div>
                  
                  <h2 className="text-2xl font-bold text-white mb-2">{race.name}</h2>
                  <p className="text-gray-400 mb-4">{race.event}</p>
                  
                  <div className="flex items-center">
                    <span className="text-gray-300">
                      {countryFlags[race.country] || '🏎️'} {race.country}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </main>

      <RaceResultsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        raceName={selectedRace?.name}
        results={raceResults}
      />
    </div>
  );
};

export default Schedule; 