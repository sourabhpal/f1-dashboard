import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { motion } from 'framer-motion';
import YearSelect from '../components/YearSelect';

export default function PitStops() {
  const [currentYear, setCurrentYear] = useState(2025);
  const [currentRound, setCurrentRound] = useState(1);
  const [pitStops, setPitStops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availableYears, setAvailableYears] = useState([2025, 2024, 2023, 2022]);

  useEffect(() => {
    const fetchAvailableYears = async () => {
      try {
        const response = await fetch('http://localhost:8000/available-years');
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
    const fetchPitStops = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8000/pit-stops/${currentYear}/${currentRound}`);
        if (!response.ok) throw new Error('Failed to fetch pit stop data');
        const data = await response.json();
        setPitStops(data);
      } catch (err) {
        console.error('Error fetching pit stop data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPitStops();
  }, [currentYear, currentRound]);

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-white">Pit Stop Data</h1>
          <div className="flex space-x-4">
            <YearSelect
              value={currentYear}
              onChange={setCurrentYear}
              years={availableYears}
            />
            <select
              value={currentRound}
              onChange={(e) => setCurrentRound(parseInt(e.target.value))}
              className="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              {[...Array(23)].map((_, i) => (
                <option key={i + 1} value={i + 1}>
                  Round {i + 1}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading && (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-900/50 text-white p-4 rounded-lg mb-4">
            <p>Error: {error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-2 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && (
          <div className="grid gap-4">
            {pitStops.map((stop, index) => (
              <motion.div
                key={`${stop.driver}-${stop.lap}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-800 rounded-lg p-6 shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white">{stop.driver}</h2>
                    <p className="text-gray-400">Lap {stop.lap}</p>
                  </div>
                  <div className="text-xl font-bold text-red-500">
                    Stop {stop.stop_number}
                  </div>
                </div>
                <div className="mt-4 text-gray-300">
                  <p>Duration: {stop.duration}s</p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
} 