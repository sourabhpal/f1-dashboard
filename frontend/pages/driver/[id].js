import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import { motion } from 'framer-motion';
import YearSelect from '../../components/YearSelect';

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

export default function DriverDetails() {
  const router = useRouter();
  const { id } = router.query;
  const [driver, setDriver] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentYear, setCurrentYear] = useState(2025);
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
    const fetchDriverDetails = async () => {
      if (!id) return;
      
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8000/driver/${id}/${currentYear}`);
        if (!response.ok) throw new Error('Failed to fetch driver data');
        const data = await response.json();
        setDriver(data);
      } catch (err) {
        console.error('Error fetching driver details:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDriverDetails();
  }, [id, currentYear]);

  if (loading) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error || !driver) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8">
          <div className="bg-red-900/50 text-white p-4 rounded-lg mb-4">
            <p>Error: {error || 'Driver not found'}</p>
            <button
              onClick={() => router.push('/drivers')}
              className="mt-2 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Back to Drivers
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-white">Driver Details</h1>
          <YearSelect
            value={currentYear}
            onChange={setCurrentYear}
            years={availableYears}
          />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-800 rounded-lg shadow-lg overflow-hidden"
        >
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Audiowide, sans-serif', fontWeight: 'normal' }}>
                  {formatDriverName(driver.driver_name)}
                </h1>
                <p className="text-gray-400">{driver.team}</p>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-4xl font-bold text-white" style={{ fontFamily: 'Audiowide, sans-serif', fontWeight: 'normal' }}>
                  #{driver.driver_number}
                </span>
                <div
                  className="w-6 h-6 rounded-full mt-2"
                  style={{ backgroundColor: driver.team_color || '#ff0000' }}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-700 p-4 rounded-lg">
                <h2 className="text-xl font-bold text-white mb-4">Season Stats</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-gray-400">Position</p>
                    <p className="text-white text-2xl font-bold">{driver.position || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Points</p>
                    <p className="text-white text-2xl font-bold">{driver.points || '0'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Wins</p>
                    <p className="text-white text-2xl font-bold">{driver.wins || '0'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Podiums</p>
                    <p className="text-white text-2xl font-bold">{driver.podiums || '0'}</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-700 p-4 rounded-lg">
                <h2 className="text-xl font-bold text-white mb-4">Driver Info</h2>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <p className="text-gray-400">Nationality</p>
                    <p className="text-white">{driver.nationality || 'N/A'}</p>
                  </div>
                  <div className="flex justify-between">
                    <p className="text-gray-400">Date of Birth</p>
                    <p className="text-white">{driver.date_of_birth || 'N/A'}</p>
                  </div>
                  <div className="flex justify-between">
                    <p className="text-gray-400">Place of Birth</p>
                    <p className="text-white">{driver.place_of_birth || 'N/A'}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        <div className="mt-8">
          <button
            onClick={() => router.push('/drivers')}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Back to Drivers
          </button>
        </div>
      </div>
    </Layout>
  );
} 