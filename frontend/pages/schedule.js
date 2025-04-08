import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';
import Navbar from '../components/Navbar';
import RaceResultsModal from '../components/RaceResultsModal';
import YearSelector from '../components/YearSelector';
import { API_URL } from '../config';

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
  const [selectedYear, setSelectedYear] = useState(2025);
  const [selectedRace, setSelectedRace] = useState(null);
  const [raceResults, setRaceResults] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [availableYears, setAvailableYears] = useState([2025, 2024, 2023, 2022]);

  useEffect(() => {
    const fetchAvailableYears = async () => {
      try {
        const response = await fetch(`${API_URL}/available-years`);
        if (!response.ok) throw new Error('Failed to fetch available years');
        const data = await response.json();
        setAvailableYears(Array.isArray(data.years) ? data.years : [2025, 2024, 2023, 2022]);
      } catch (err) {
        console.error('Error fetching available years:', err);
        setAvailableYears([2025, 2024, 2023, 2022]);
      }
    };

    fetchAvailableYears();
  }, []);

  useEffect(() => {
    const fetchSchedule = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_URL}/schedule/${selectedYear}`);
        if (!response.ok) throw new Error('Failed to fetch schedule');
        const data = await response.json();
        setSchedule(data);
      } catch (err) {
        console.error('Error fetching schedule:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSchedule();
  }, [selectedYear]);

  const handleRaceClick = async (race) => {
    try {
      const response = await fetch(`${API_URL}/race-results/${selectedYear}/${race.round}`);
      if (!response.ok) {
        throw new Error('Failed to fetch race results');
      }
      const data = await response.json();
      setRaceResults(data.results);
      setSelectedRace(race);
      setIsModalOpen(true);
    } catch (error) {
      console.error('Error fetching race results:', error);
      setError('Failed to load race results');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
            <p className="mt-4 text-gray-400">Loading schedule...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-red-500">
            <p>{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Head>
        <title>F1 Schedule 2025 | F1 Dashboard</title>
        <meta name="description" content="Formula 1 race schedule for the 2025 season" />
      </Head>

      <Navbar />

      <main className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-4xl font-bold text-white page-title">F1 Schedule</h1>
            <YearSelector
              value={selectedYear}
              onChange={setSelectedYear}
              years={availableYears}
            />
          </div>
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {schedule.map((race, index) => (
              <motion.div
                key={`${race.year}-${race.round}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => handleRaceClick(race)}
                className="bg-gray-800 rounded-lg shadow-lg overflow-hidden cursor-pointer hover:bg-gray-700 transition-colors duration-200"
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <span className="text-red-500 font-bold mr-2">#{race.round}</span>
                      <h2 className="text-xl font-semibold text-white">{race.name}</h2>
                    </div>
                    <span className="text-2xl">{countryFlags[race.country] || '🏎️'}</span>
                  </div>
                  <div className="space-y-2">
                    <p className="text-gray-400">{race.country}</p>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-500">Round {race.round}</span>
                      <span className="text-gray-400">{formatDate(race.date)}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
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