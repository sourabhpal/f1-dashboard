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
    setLoadingStats(true);
    try {
      // In a real implementation, you would fetch this data from your API
      // For now, we'll simulate the data
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Generate random statistics for demonstration
      const stats = {
        wins: Math.floor(Math.random() * 5),
        podiums: Math.floor(Math.random() * 10) + 5,
        polePositions: Math.floor(Math.random() * 5),
        fastestLaps: Math.floor(Math.random() * 3),
        lapsLed: Math.floor(Math.random() * 200) + 50,
        leadLapPercentage: (Math.random() * 15).toFixed(1),
        averageRacePosition: (Math.random() * 10 + 5).toFixed(1),
        averageGridPosition: (Math.random() * 10 + 5).toFixed(1),
        positionsGained: Math.floor(Math.random() * 50) + 10,
        averagePositionsGained: (Math.random() * 3).toFixed(1)
      };
      
      setDriverStats(stats);
    } catch (err) {
      console.error('Error fetching driver stats:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  // Function to handle driver tile click
  const handleDriverClick = (driver) => {
    setSelectedDriver(driver);
    fetchDriverStats(driver.driver_name);
  };

  // Function to close the modal
  const closeModal = () => {
    setSelectedDriver(null);
    setDriverStats(null);
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
      {selectedDriver && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div 
            className="bg-gray-900 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            style={{
              borderLeft: `4px solid ${selectedDriver.driver_color || '#ffffff'}`,
              borderTop: `4px solid ${selectedDriver.driver_color || '#ffffff'}`,
            }}
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-4">
                  <div className="relative w-24 h-24 rounded-full overflow-hidden">
                    <Image
                      src={getDriverImagePath(selectedDriver.driver_name)}
                      alt={selectedDriver.driver_name}
                      width={96}
                      height={96}
                      className="object-cover"
                      onError={(e) => {
                        e.target.src = '/images/drivers/default.png';
                      }}
                    />
                  </div>
                  <div>
                    <h2 
                      className="text-2xl font-bold"
                      style={{ 
                        color: selectedDriver.driver_color || '#ffffff',
                        fontFamily: 'Audiowide, sans-serif'
                      }}
                    >
                      {formatDriverName(selectedDriver.driver_name)}
                    </h2>
                    <p className="text-gray-400">{selectedDriver.team}</p>
                    {selectedDriver.position && (
                      <p className="text-white mt-1">Championship Position: {selectedDriver.position}</p>
                    )}
                  </div>
                </div>
                <button 
                  onClick={closeModal}
                  className="text-gray-400 hover:text-white"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {loadingStats ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
                </div>
              ) : driverStats ? (
                <div>
                  <h3 className="text-xl font-bold mb-4 text-white">Race Performance</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Wins</p>
                      <p className="text-white text-2xl font-bold">{driverStats.wins}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Podiums</p>
                      <p className="text-white text-2xl font-bold">{driverStats.podiums}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Pole Positions</p>
                      <p className="text-white text-2xl font-bold">{driverStats.polePositions}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Fastest Laps</p>
                      <p className="text-white text-2xl font-bold">{driverStats.fastestLaps}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Laps Led</p>
                      <p className="text-white text-2xl font-bold">{driverStats.lapsLed}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Lead Lap Percentage</p>
                      <p className="text-white text-2xl font-bold">{driverStats.leadLapPercentage}%</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Average Race Position</p>
                      <p className="text-white text-2xl font-bold">{driverStats.averageRacePosition}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Average Grid Position</p>
                      <p className="text-white text-2xl font-bold">{driverStats.averageGridPosition}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Positions Gained</p>
                      <p className="text-white text-2xl font-bold">{driverStats.positionsGained}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Average Positions Gained</p>
                      <p className="text-white text-2xl font-bold">{driverStats.averagePositionsGained}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-400 py-8">
                  <p>No statistics available for this driver.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
} 