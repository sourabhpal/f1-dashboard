import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { motion } from 'framer-motion';
import YearSelect from '../components/YearSelect';

export default function Timing() {
  const [currentYear, setCurrentYear] = useState(2025);
  const [currentRound, setCurrentRound] = useState(1);
  const [timingData, setTimingData] = useState([]);
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
    const fetchTimingData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8000/timing/${currentYear}/${currentRound}`);
        if (!response.ok) throw new Error('Failed to fetch timing data');
        const data = await response.json();
        setTimingData(data);
      } catch (err) {
        console.error('Error fetching timing data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTimingData();
  }, [currentYear, currentRound]);

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-white">Race Timing Data</h1>
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
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-700">
                  <th className="py-3 px-4">Position</th>
                  <th className="py-3 px-4">Driver</th>
                  <th className="py-3 px-4">Team</th>
                  <th className="py-3 px-4">Last Lap</th>
                  <th className="py-3 px-4">Best Lap</th>
                  <th className="py-3 px-4">Gap</th>
                </tr>
              </thead>
              <tbody>
                {timingData.map((data, index) => (
                  <motion.tr
                    key={data.driver_name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border-b border-gray-700 hover:bg-gray-800/50"
                  >
                    <td className="py-3 px-4 text-red-500 font-bold">{data.position}</td>
                    <td className="py-3 px-4 text-white">{data.driver_name}</td>
                    <td className="py-3 px-4 text-gray-400">{data.team}</td>
                    <td className="py-3 px-4 text-white">{data.last_lap}</td>
                    <td className="py-3 px-4 text-white">{data.best_lap}</td>
                    <td className="py-3 px-4 text-white">{data.gap}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
} 