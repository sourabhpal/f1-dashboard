import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { motion } from 'framer-motion';
import YearSelect from '../components/YearSelect';

export default function Teams() {
  const [currentYear, setCurrentYear] = useState(2025);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availableYears, setAvailableYears] = useState([2025, 2024, 2023, 2022]);

  useEffect(() => {
    const fetchAvailableYears = async () => {
      try {
        const response = await fetch('http://localhost:8000/available-years');
        if (!response.ok) throw new Error('Failed to fetch available years');
        const data = await response.json();
        setAvailableYears(data.years || [2025, 2024, 2023, 2022]);
      } catch (err) {
        console.error('Error fetching available years:', err);
        setAvailableYears([2025, 2024, 2023, 2022]);
      }
    };

    fetchAvailableYears();
  }, []);

  useEffect(() => {
    const fetchTeams = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8000/team_standings/${currentYear}`);
        if (!response.ok) throw new Error('Failed to fetch team data');
        const data = await response.json();
        setTeams(data);
      } catch (err) {
        console.error('Error fetching teams:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, [currentYear]);

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-white">F1 Teams</h1>
          <YearSelect
            value={currentYear}
            onChange={setCurrentYear}
            years={availableYears}
          />
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
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {teams.map((team, index) => (
              <motion.div
                key={team.team}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-800 rounded-lg p-6 shadow-lg"
                style={{ borderLeft: `4px solid ${team.team_color || '#ff0000'}` }}
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold" style={{ color: team.team_color || '#ff0000', fontFamily: 'Genos, sans-serif', fontWeight: '600' }}>{team.team}</h2>
                  </div>
                  <div className="text-2xl font-bold" style={{ color: team.team_color || '#ff0000', fontFamily: 'Genos, sans-serif', fontWeight: '600' }}>{index + 1}</div>
                </div>
                <div className="text-gray-300">
                  <p>Points: {team.total_points}</p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
} 