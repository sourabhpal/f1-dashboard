import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { motion } from 'framer-motion';
import Image from 'next/image';
import YearSelect from '../components/YearSelect';
import { API_URL } from '../config';

// Add country to flag emoji mapping
const countryFlags = {
  'Australia': '🇦🇺',
  'Austria': '🇦🇹',
  'Azerbaijan': '🇦🇿',
  'Bahrain': '🇧🇭',
  'Belgium': '🇧🇪',
  'Brazil': '🇧🇷',
  'Canada': '🇨🇦',
  'China': '🇨🇳',
  'France': '🇫🇷',
  'Germany': '🇩🇪',
  'Hungary': '🇭🇺',
  'Italy': '🇮🇹',
  'Japan': '🇯🇵',
  'Mexico': '🇲🇽',
  'Monaco': '🇲🇨',
  'Netherlands': '🇳🇱',
  'Qatar': '🇶🇦',
  'Russia': '🇷🇺',
  'Saudi Arabia': '🇸🇦',
  'Singapore': '🇸🇬',
  'Spain': '🇪🇸',
  'Turkey': '🇹🇷',
  'United Arab Emirates': '🇦🇪',
  'United Kingdom': '🇬🇧',
  'United States': '🇺🇸',
  'Vietnam': '🇻🇳'
};

export default function Drivers() {
  const [currentYear, setCurrentYear] = useState(2025);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availableYears, setAvailableYears] = useState([2025, 2024, 2023, 2022]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [driverStats, setDriverStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const fetchAvailableYears = async () => {
      try {
        const response = await fetch(`${API_URL}/available-years`);
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
    const fetchDriverData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch both drivers and standings data
        const [driversResponse, standingsResponse] = await Promise.all([
          fetch(`${API_URL}/drivers/${currentYear}`),
          fetch(`${API_URL}/standings/${currentYear}`)
        ]);
        
        if (!driversResponse.ok) throw new Error('Failed to fetch driver data');
        if (!standingsResponse.ok) throw new Error('Failed to fetch standings data');
        
        const driversData = await driversResponse.json();
        const standingsData = await standingsResponse.json();
        
        // Create a map of driver standings for easy lookup
        const standingsMap = {};
        standingsData.forEach(standing => {
          standingsMap[standing.standardized_driver_name || standing.driver_name] = standing;
        });
        
        // Merge drivers data with standings data
        const mergedDrivers = driversData.map(driver => {
          const standing = standingsMap[driver.standardized_driver_name || driver.driver_name] || {};
          return {
            ...driver,
            total_points: standing.total_points || 0,
            points: standing.points || 0,
            sprint_points: standing.sprint_points || 0,
            position: standing.position || null,
            races_participated: standing.races_participated || 0
          };
        });
        
        // Sort drivers by position in standings
        mergedDrivers.sort((a, b) => {
          // If both have positions, sort by position
          if (a.position !== null && b.position !== null) {
            return a.position - b.position;
          }
          // If only one has a position, put the one with position first
          if (a.position !== null) return -1;
          if (b.position !== null) return 1;
          // If neither has a position, sort by name
          return a.driver_name.localeCompare(b.driver_name);
        });
        
        setDrivers(mergedDrivers);
      } catch (err) {
        console.error('Error fetching driver data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDriverData();
  }, [currentYear]);

  // Function to fetch driver statistics
  const fetchDriverStats = async (driverName) => {
    try {
      setLoadingStats(true);
      const response = await fetch(`${API_URL}/driver-stats/${currentYear}/${encodeURIComponent(driverName)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setDriverStats(data);
    } catch (error) {
      console.error('Error fetching driver stats:', error);
      // You might want to show an error message to the user here
    } finally {
      setLoadingStats(false);
    }
  };

  // Function to handle driver tile click
  const handleDriverClick = (driver) => {
    setSelectedDriver(driver);
    setIsModalOpen(true);
    fetchDriverStats(driver.driver_name);
  };

  // Function to close the modal
  const closeModal = () => {
    setSelectedDriver(null);
    setDriverStats(null);
    setIsModalOpen(false);
  };

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

  // Function to get driver image path
  const getDriverImagePath = (driverName) => {
    if (!driverName) return '/images/drivers/default.png';
    
    // Convert driver name to lowercase and replace spaces with hyphens
    const formattedName = driverName.toLowerCase().replace(/\s+/g, '-');
    return `/images/drivers/${formattedName}.png`;
  };

  // StatCard component for displaying statistics
  const StatCard = ({ label, value }) => {
    return (
      <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
        <p className="text-gray-400 text-xs sm:text-sm">{label}</p>
        <p className="text-white text-xl sm:text-2xl font-bold">{value}</p>
      </div>
    );
  };

  // Update the driver card to be clickable with enhanced hover animations
  const DriverCard = ({ driver }) => {
    return (
      <motion.div
        className="bg-gray-800 rounded-lg shadow-lg p-6 cursor-pointer relative overflow-hidden"
        onClick={() => handleDriverClick(driver)}
        whileHover={{ 
          scale: 1.02,
          transition: { duration: 0.2 }
        }}
        whileTap={{ scale: 0.98 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <motion.div 
          className="absolute inset-0 opacity-0"
          style={{ 
            background: `linear-gradient(135deg, ${driver.driver_color}22, ${driver.driver_color}11)`,
          }}
          whileHover={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        />
        
        <div className="flex items-center justify-between mb-4 relative z-10">
          <div className="flex items-center space-x-4">
            <div
              className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold"
              style={{ backgroundColor: driver.driver_color }}
            >
              {driver.position || '-'}
            </div>
            <div>
              <h3 className="text-xl font-semibold text-white">{formatDriverName(driver.driver_name)}</h3>
              <p className="text-gray-400">{driver.team}</p>
            </div>
          </div>
        </div>

        <div className="relative z-10">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-gray-400">Total Points</div>
            <div className="flex items-center space-x-2">
              <div className="text-2xl font-bold text-white">{driver.total_points || 0}</div>
              <span className="text-sm text-gray-400">pts</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-700/50 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-400">Race</div>
                <div className="text-lg font-semibold text-white">{driver.points || 0}</div>
              </div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-400">Sprint</div>
                <div className="text-lg font-semibold text-white">{driver.sprint_points || 0}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-4 text-sm text-gray-400 relative z-10">
          <div className="flex items-center space-x-2">
            <span>#{driver.driver_number || '-'}</span>
            {driver.nationality_flag && (
              <span className="text-base">{driver.nationality_flag}</span>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span>{driver.races_participated || 0} races</span>
          </div>
        </div>
      </motion.div>
    );
  };

  // Update the modal component to include tabs
  const DriverStatsModal = ({ driver, stats, onClose }) => {
    const [activeTab, setActiveTab] = useState('race');
    
    if (!driver || !stats) return null;
  
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-75">
        <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto relative">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {/* Driver header */}
          <div className="p-6 border-b border-gray-800">
            <div className="flex items-center">
              <div
                className="w-12 h-12 rounded-full mr-4"
                style={{ backgroundColor: driver.driver_color }}
              ></div>
              <div>
                <h2 className="text-2xl font-bold text-white">{formatDriverName(driver.driver_name)}</h2>
                <p className="text-gray-400">{driver.team}</p>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-800">
            <div className="flex">
              <button
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'race' ? 'text-white border-b-2 border-blue-500' : 'text-gray-400'
                }`}
                onClick={() => setActiveTab('race')}
              >
                Race Stats
              </button>
              <button
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'qualifying' ? 'text-white border-b-2 border-blue-500' : 'text-gray-400'
                }`}
                onClick={() => setActiveTab('qualifying')}
              >
                Qualifying
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {activeTab === 'race' && (
              <div className="space-y-6">
                {/* Race Results */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Race Results</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                    <StatCard label="Wins" value={stats.wins || 0} />
                    <StatCard label="Podiums" value={stats.podiums || 0} />
                    <StatCard label="Points" value={driver.total_points || 0} />
                    <StatCard label="Races" value={stats.total_races || 0} />
                  </div>
                </div>

                {/* Race Results Table */}
                <div className="bg-gray-800 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Race Results</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-left border-b border-gray-700">
                          <th className="p-3">Round</th>
                          <th className="p-3">Race</th>
                          <th className="p-3">Position</th>
                          <th className="p-3">Points</th>
                          <th className="p-3">Sprint Points</th>
                          <th className="p-3">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.race_results?.map((result) => (
                          <tr key={result.round} className="border-b border-gray-700">
                            <td className="p-3">{result.round}</td>
                            <td className="p-3">{result.race_name}</td>
                            <td className="p-3">{result.position || 'DNF'}</td>
                            <td className="p-3">{result.points || 0}</td>
                            <td className="p-3">{result.sprint_points || 0}</td>
                            <td className="p-3">{result.status || 'Finished'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'qualifying' && (
              <div className="space-y-6">
                {/* Qualifying Stats */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Qualifying Performance</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                    <StatCard label="Pole Positions" value={stats.pole_positions || 0} />
                    <StatCard label="Avg. Qualifying" value={stats.avg_qualifying || '-'} />
                    <StatCard label="Q3 Appearances" value={stats.q3_appearances || 0} />
                    <StatCard label="Q2 Appearances" value={stats.q2_appearances || 0} />
                  </div>
                </div>

                {/* Qualifying Results Table */}
                <div className="bg-gray-800 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Qualifying Results</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-left border-b border-gray-700">
                          <th className="p-3">Round</th>
                          <th className="p-3">Race</th>
                          <th className="p-3">Position</th>
                          <th className="p-3">Q1</th>
                          <th className="p-3">Q2</th>
                          <th className="p-3">Q3</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.qualifying_results?.map((result) => (
                          <tr key={result.round} className="border-b border-gray-700">
                            <td className="p-3">{result.round}</td>
                            <td className="p-3">{result.race_name}</td>
                            <td className="p-3">{result.position || '-'}</td>
                            <td className="p-3">{result.q1 || '-'}</td>
                            <td className="p-3">{result.q2 || '-'}</td>
                            <td className="p-3">{result.q3 || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-white page-title">F1 Drivers</h1>
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
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {drivers.map((driver, index) => (
              <motion.div
                key={driver.driver_number || index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative overflow-hidden rounded-lg shadow-md cursor-pointer hover:shadow-lg transition-all duration-300 ease-in-out group"
                style={{
                  borderLeft: `2px solid ${driver.driver_color || '#ffffff'}`,
                  borderTop: `2px solid ${driver.driver_color || '#ffffff'}`,
                  borderRadius: '1rem',
                  transform: 'translateY(0)',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.08)',
                }}
                whileHover={{ 
                  scale: 1.015,
                  boxShadow: '0 6px 12px rgba(0, 0, 0, 0.12)',
                  transition: { duration: 0.25, ease: "easeOut" }
                }}
                onClick={() => handleDriverClick(driver)}
              >
                <div 
                  className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  style={{
                    background: `linear-gradient(135deg, ${driver.driver_color}15, ${driver.driver_color}08)`,
                  }}
                />
                <div className="relative h-96">
                  {/* Driver image */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Image
                      src={getDriverImagePath(driver.driver_name)}
                      alt={driver.driver_name}
                      width={300}
                      height={300}
                      className="object-contain transition-transform duration-300 group-hover:scale-105"
                      onError={(e) => {
                        e.target.src = '/images/drivers/default.png';
                      }}
                    />
                  </div>
                  
                  {/* Hover overlay effect */}
                  <div 
                    className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ 
                      background: `linear-gradient(135deg, ${driver.driver_color}15, ${driver.driver_color}08)`,
                    }}
                  ></div>
                  
                  {/* Driver number in the top right */}
                  {driver.driver_number && (
                    <div className="absolute top-4 right-4 w-16 h-16">
                      <Image
                        src={`/images/driver-numbers/${driver.driver_number}.png`}
                        alt={`${driver.driver_name}'s number ${driver.driver_number}`}
                        width={64}
                        height={64}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          // If image fails to load, fallback to text number
                          e.target.parentElement.innerHTML = `<span 
                            class="text-6xl font-bold" 
                            style="font-family: Audiowide, sans-serif; color: ${driver.driver_color || '#ffffff'}; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);"
                          >${driver.driver_number}</span>`;
                        }}
                      />
                    </div>
                  )}
                  
                  {/* Position badge in the top left */}
                  {driver.position && (
                    <div className="absolute top-4 left-4">
                      <span 
                        className="text-white font-bold text-sm"
                        style={{ 
                          textShadow: '0 1px 2px rgba(0, 0, 0, 0.8)'
                        }}
                      >
                        P{driver.position}
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="p-6 bg-gray-900/80 backdrop-blur-sm group-hover:bg-gray-800/90 transition-colors duration-300">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 
                          className="text-xl text-white group-hover:text-white transition-colors duration-300" 
                          style={{ 
                            fontFamily: 'Audiowide, sans-serif', 
                            fontWeight: 'normal',
                            letterSpacing: '0.5px',
                            color: driver.driver_color || '#ffffff'
                          }}
                        >
                          {formatDriverName(driver.driver_name)}
                        </h2>
                        {driver.nationality_flag && (
                          <span className="text-2xl ml-2 group-hover:scale-110 transition-transform duration-300">{driver.nationality_flag}</span>
                        )}
                      </div>
                      <p className="text-gray-400 text-sm group-hover:text-gray-300 transition-colors duration-300" style={{ fontFamily: 'Genos, sans-serif', fontWeight: '500' }}>{driver.team}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div>
                      <p className="text-gray-400 text-xs group-hover:text-gray-300 transition-colors duration-300" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>Points</p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-white text-xl font-bold group-hover:text-white transition-colors duration-300" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>
                            {driver.total_points || 0}
                          </span>
                          <span className="text-gray-400 text-sm">pts</span>
                        </div>
                        {driver.sprint_points > 0 && (
                          <div className="flex items-center space-x-1">
                            <span className="text-gray-400 text-sm">Sprint:</span>
                            <span className="text-white text-sm font-medium">{driver.sprint_points}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center justify-end">
                      <div className="flex items-center space-x-1">
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <span className="text-gray-400 text-sm">{driver.races_participated || 0} races</span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Driver Stats Modal */}
      {isModalOpen && (
        <DriverStatsModal
          driver={selectedDriver}
          stats={driverStats}
          onClose={closeModal}
        />
      )}
    </Layout>
  );
} 