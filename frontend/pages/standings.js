import { useState, useEffect } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import Image from 'next/image';
import Layout from '../components/Layout';
import YearSelect from '../components/YearSelect';
import { API_URL } from '../config';

// Function to format driver name with last name in uppercase
const formatDriverName = (fullName) => {
  if (!fullName) return '';
  const parts = fullName.split(' ');
  if (parts.length > 1) {
    const firstName = parts[0];
    const lastName = parts.slice(1).join(' ').toUpperCase();
    return `${firstName} ${lastName}`;
  }
  return fullName;
};

export default function Standings() {
  const [currentYear, setCurrentYear] = useState(2025);
  const [driverStandings, setDriverStandings] = useState([]);
  const [constructorStandings, setConstructorStandings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availableYears, setAvailableYears] = useState([2025, 2024, 2023, 2022]);
  const [activeTab, setActiveTab] = useState('drivers');

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
    const fetchStandings = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch driver standings
        const driverResponse = await fetch(`${API_URL}/standings/${currentYear}`);
        if (!driverResponse.ok) throw new Error('Failed to fetch driver standings');
        const driverData = await driverResponse.json();
        setDriverStandings(driverData);

        // Fetch constructor standings
        const constructorResponse = await fetch(`${API_URL}/team_standings/${currentYear}`);
        if (!constructorResponse.ok) throw new Error('Failed to fetch constructor standings');
        const constructorData = await constructorResponse.json();
        setConstructorStandings(constructorData);
      } catch (err) {
        console.error('Error fetching standings:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStandings();
  }, [currentYear]);

  return (
    <Layout>
      <Head>
        <title>F1 Standings</title>
        <meta name="description" content="Formula 1 Driver and Constructor Standings" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-white page-title">F1 Standings</h1>
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
          <div className="grid gap-8">
            {/* Tab Navigation */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <button
                onClick={() => setActiveTab('drivers')}
                className={`w-full px-6 py-4 rounded-lg font-semibold transition-all duration-200 tab-button ${
                  activeTab === 'drivers'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                Driver Standings
              </button>
              <button
                onClick={() => setActiveTab('constructors')}
                className={`w-full px-6 py-4 rounded-lg font-semibold transition-all duration-200 tab-button ${
                  activeTab === 'constructors'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                Constructor Standings
              </button>
            </div>

            {/* Driver Standings */}
            {activeTab === 'drivers' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="grid gap-4">
                  {driverStandings.map((standing, index) => (
                    <motion.div
                      key={standing.standardized_driver_name || standing.driver_name}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-gray-800 rounded-lg p-6 shadow-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="text-2xl font-bold" style={{ color: standing.driver_color || '#ff0000', fontFamily: 'Audiowide, sans-serif', fontWeight: 'normal' }}>{standing.position}</div>
                          <div className="flex items-center space-x-4">
                            <div className="relative w-12 h-12 bg-gray-700 rounded-lg p-1">
                              <Image
                                src={`/images/drivers/${(standing.standardized_driver_name || standing.driver_name).toLowerCase().replace(/\s+/g, '-')}.png`}
                                alt={`${standing.driver_name}`}
                                fill
                                sizes="48px"
                                className="object-contain"
                                onError={(e) => {
                                  e.target.src = '/images/drivers/default-driver.png';
                                }}
                              />
                            </div>
                            <div>
                              <h2 
                                className="text-xl font-semibold" 
                                style={{ 
                                  color: standing.driver_color || '#ff0000',
                                  fontFamily: 'Audiowide, sans-serif',
                                  fontWeight: 'normal',
                                  letterSpacing: '0.5px'
                                }}
                              >
                                {formatDriverName(standing.driver_name)}
                              </h2>
                              <p className="text-gray-400" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{standing.team}</p>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-white tracking-wider" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>
                            {standing.total_points} <span className="text-sm text-gray-400">pts</span>
                          </div>
                          <div className="text-xs text-gray-400">
                            <span>Race: {standing.points}</span>
                            {standing.sprint_points > 0 && (
                              <span className="ml-2">Sprint: {standing.sprint_points}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Constructor Standings */}
            {activeTab === 'constructors' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="grid gap-4">
                  {constructorStandings.map((standing, index) => (
                    <motion.div
                      key={standing.team}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-gray-800 rounded-lg p-6 shadow-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="text-2xl font-bold mr-6" style={{ color: standing.team_color || '#ff0000', fontFamily: 'Genos, sans-serif', fontWeight: '600' }}>{index + 1}</div>
                          <div className="flex items-center space-x-6">
                            <div className="relative w-12 h-12 bg-gray-800 rounded-lg p-1">
                              <Image
                                src={`/images/teams/${standing.team.toLowerCase().replace(/\s+/g, '-')}.png`}
                                alt={`${standing.team} logo`}
                                fill
                                sizes="48px"
                                className="object-contain"
                                style={{ mixBlendMode: 'screen' }}
                                onError={(e) => {
                                  e.target.src = '/images/teams/default-team.png';
                                }}
                              />
                            </div>
                            <div>
                              <h3 
                                className="text-xl font-semibold"
                                style={{ 
                                  color: standing.team_color || '#ff0000',
                                  fontFamily: 'Genos, sans-serif',
                                  fontWeight: '600',
                                  fontSize: '1.5rem',
                                  letterSpacing: '0.5px'
                                }}
                              >
                                {standing.team}
                              </h3>
                            </div>
                          </div>
                        </div>
                        <div className="text-2xl font-bold text-white tracking-wider" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>
                          {standing.total_points} <span className="text-sm text-gray-400">pts</span>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
} 