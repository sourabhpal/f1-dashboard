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
                className="relative overflow-hidden rounded-lg shadow-lg"
                style={{
                  borderLeft: `2px solid ${driver.driver_color || '#ffffff'}`,
                  borderTop: `2px solid ${driver.driver_color || '#ffffff'}`,
                  borderRadius: '1rem'
                }}
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
                      <div 
                        className="w-8 h-8 rounded-full flex items-center justify-center"
                        style={{ 
                          backgroundColor: 'rgba(0, 0, 0, 0.6)',
                          border: '1px solid rgba(255, 255, 255, 0.5)',
                          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
                        }}
                      >
                        <span className="text-white font-bold text-sm">{driver.position}</span>
                      </div>
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
    </Layout>
  );
} 