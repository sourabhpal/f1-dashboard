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
          standingsMap[standing.driver_name] = standing;
        });
        
        // Merge drivers data with standings data
        const mergedDrivers = driversData.map(driver => {
          const standing = standingsMap[driver.driver_name] || {};
          return {
            ...driver,
            total_points: standing.total_points || 0,
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

  // Update the driver card to be clickable with enhanced hover animations
  const DriverCard = ({ driver }) => {
    return (
      <motion.div
        className="bg-white rounded-lg shadow-md p-4 cursor-pointer relative overflow-hidden"
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
            background: `linear-gradient(45deg, ${driver.driver_color}33, transparent)`,
          }}
          whileHover={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        />
        <div className="flex items-center justify-between mb-2 relative z-10">
          <div className="flex items-center">
            <div
              className="w-8 h-8 rounded-full mr-2"
              style={{ backgroundColor: driver.driver_color }}
            ></div>
            <div>
              <h3 className="font-semibold">{driver.driver_name}</h3>
              <p className="text-sm text-gray-500">{driver.team}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">P{driver.position || '-'}</div>
            <div className="text-sm text-gray-500">{driver.total_points || 0} pts</div>
          </div>
        </div>
        <div className="flex justify-between text-sm text-gray-500 relative z-10">
          <div>#{driver.driver_number || '-'}</div>
          <div>{driver.races_participated || 0} races</div>
        </div>
      </motion.div>
    );
  };

  // Update the modal component to include tabs
  const DriverStatsModal = ({ isOpen, onClose, driver, stats, isLoading }) => {
    const [activeTab, setActiveTab] = useState('race');
    
    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-2 sm:p-4">
        <div 
          className="bg-gray-900 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto"
          style={{
            borderLeft: `4px solid ${driver?.driver_color || '#ffffff'}`,
            borderTop: `4px solid ${driver?.driver_color || '#ffffff'}`,
          }}
        >
          <div className="p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
              <div className="flex items-center gap-4 w-full sm:w-auto">
                <div className="relative w-20 h-20 sm:w-24 sm:h-24 rounded-full overflow-hidden flex-shrink-0">
                  <Image
                    src={getDriverImagePath(driver?.driver_name)}
                    alt={driver?.driver_name}
                    width={96}
                    height={96}
                    className="object-cover"
                    onError={(e) => {
                      e.target.src = '/images/drivers/default.png';
                    }}
                  />
                </div>
                <div className="flex-grow">
                  <h2 
                    className="text-xl sm:text-2xl font-bold"
                    style={{ 
                      color: driver?.driver_color || '#ffffff',
                      fontFamily: 'Audiowide, sans-serif'
                    }}
                  >
                    {formatDriverName(driver?.driver_name)}
                  </h2>
                  <p className="text-gray-400 text-sm sm:text-base">{driver?.team}</p>
                  {driver?.position && (
                    <p className="text-white mt-1 text-sm sm:text-base">Championship Position: {driver.position}</p>
                  )}
                </div>
              </div>
              <button 
                onClick={onClose}
                className="text-gray-400 hover:text-white absolute top-4 right-4 sm:relative sm:top-0 sm:right-0"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
              </div>
            ) : stats ? (
              <div>
                {/* Tabs */}
                <div className="flex border-b border-gray-700 mb-4">
                  <button
                    className={`py-2 px-4 text-sm font-medium ${
                      activeTab === 'race'
                        ? 'text-white border-b-2'
                        : 'text-gray-400 hover:text-white'
                    }`}
                    style={{
                      borderColor: activeTab === 'race' ? driver?.driver_color || '#ffffff' : 'transparent'
                    }}
                    onClick={() => setActiveTab('race')}
                  >
                    Race Performance
                  </button>
                  <button
                    className={`py-2 px-4 text-sm font-medium ${
                      activeTab === 'qualifying'
                        ? 'text-white border-b-2'
                        : 'text-gray-400 hover:text-white'
                    }`}
                    style={{
                      borderColor: activeTab === 'qualifying' ? driver?.driver_color || '#ffffff' : 'transparent'
                    }}
                    onClick={() => setActiveTab('qualifying')}
                  >
                    Qualifying Performance
                  </button>
                </div>

                {/* Race Performance Tab */}
                {activeTab === 'race' && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Wins</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.wins}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Podiums</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.podiums}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Pole Positions</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.pole_positions}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Fastest Laps</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.fastest_laps}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Laps Led</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.laps_led}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Lead Lap %</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.lead_lap_percentage}%</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Avg Race Position</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.average_race_position}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Positions Gained</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.positions_gained}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Avg Positions Gained</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.average_positions_gained}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Total Races</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.total_races}</p>
                    </div>
                  </div>
                )}

                {/* Qualifying Performance Tab */}
                {activeTab === 'qualifying' && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Avg Qualifying Position</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.average_grid_position || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Q3 Appearances</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.q3_appearances || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Q2 Appearances</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.q2_appearances || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Q1 Eliminations</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.q1_eliminations || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
                      <p className="text-gray-400 text-xs sm:text-sm">Quali vs Race Position</p>
                      <p className="text-white text-xl sm:text-2xl font-bold">{stats.quali_vs_race_position || 'N/A'}</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-400 py-8">
                <p>No statistics available for this driver.</p>
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
                className="relative overflow-hidden rounded-lg shadow-lg cursor-pointer hover:shadow-xl transition-shadow duration-300"
                style={{
                  borderLeft: `2px solid ${driver.driver_color || '#ffffff'}`,
                  borderTop: `2px solid ${driver.driver_color || '#ffffff'}`,
                  borderRadius: '1rem'
                }}
                onClick={() => handleDriverClick(driver)}
              >
                <div className="relative h-96">
                  {/* Driver image */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Image
                      src={getDriverImagePath(driver.driver_name)}
                      alt={driver.driver_name}
                      width={300}
                      height={300}
                      className="object-contain"
                      onError={(e) => {
                        e.target.src = '/images/drivers/default.png';
                      }}
                    />
                  </div>
                  
                  {/* Driver number in the top right */}
                  {driver.driver_number && (
                    <div className="absolute top-4 right-4">
                      <span 
                        className="text-6xl font-bold" 
                        style={{ 
                          fontFamily: 'Audiowide, sans-serif',
                          color: driver.driver_color || '#ffffff',
                          textShadow: '2px 2px 4px rgba(0, 0, 0, 0.5)'
                        }}
                      >
                        {driver.driver_number}
                      </span>
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
                
                <div className="p-6 bg-gray-900/80 backdrop-blur-sm">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 
                          className="text-xl text-white" 
                          style={{ 
                            fontFamily: 'Audiowide, sans-serif', 
                            fontWeight: 'normal',
                            letterSpacing: '0.5px',
                            color: driver.driver_color || '#ffffff'
                          }}
                        >
                          {formatDriverName(driver.driver_name)}
                        </h2>
                        {driver.nationality && countryFlags[driver.nationality] && (
                          <span className="text-2xl ml-2">{countryFlags[driver.nationality]}</span>
                        )}
                      </div>
                      <p className="text-gray-400 text-sm" style={{ fontFamily: 'Genos, sans-serif', fontWeight: '500' }}>{driver.team}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div>
                      <p className="text-gray-400 text-xs" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>Points</p>
                      <p className="text-white font-bold" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{driver.total_points || 0}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-xs" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>Races</p>
                      <p className="text-white font-bold" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{driver.races_participated || 0}</p>
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
          isOpen={isModalOpen}
          onClose={closeModal}
          driver={selectedDriver}
          stats={driverStats}
          isLoading={loadingStats}
        />
      )}
    </Layout>
  );
} 