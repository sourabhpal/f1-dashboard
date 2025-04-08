import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Head from 'next/head';
import Navbar from '../components/Navbar';

// Country flag mapping
const countryFlags = {
  'Australia': '🇦🇺',
  'China': '🇨🇳',
  'Japan': '🇯🇵',
  'Bahrain': '🇧🇭',
  'Saudi Arabia': '🇸🇦',
  'United States': '🇺🇸',
  'Mexico': '🇲🇽',
  'Brazil': '🇧🇷',
  'United Kingdom': '🇬🇧',
  'Belgium': '🇧🇪',
  'Hungary': '🇭🇺',
  'Netherlands': '🇳🇱',
  'Italy': '🇮🇹',
  'Azerbaijan': '🇦🇿',
  'Singapore': '🇸🇬',
  'Austria': '🇦🇹',
  'Spain': '🇪🇸',
  'Canada': '🇨🇦',
  'Monaco': '🇲🇨',
  'France': '🇫🇷',
  'Germany': '🇩🇪',
  'Russia': '🇷🇺',
  'Turkey': '🇹🇷',
  'UAE': '🇦🇪',
  'Qatar': '🇶🇦',
  'Portugal': '🇵🇹',
  'Vietnam': '🇻🇳',
  'South Korea': '🇰🇷',
  'India': '🇮🇳',
  'Malaysia': '🇲🇾',
  'Kazakhstan': '🇰🇿',
  'South Africa': '🇿🇦',
  'Argentina': '🇦🇷',
  'Morocco': '🇲🇦',
  'Sweden': '🇸🇪',
  'Switzerland': '🇨🇭',
  'Luxembourg': '🇱🇺',
  'San Marino': '🇸🇲',
  'European': '🏁',
  'Pacific': '🏁',
  'Unknown': '🏁'
};

export default function Circuits() {
  const [circuits, setCircuits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCircuits = async () => {
      try {
        const response = await fetch('http://localhost:8000/circuits/2025');
        if (!response.ok) {
          throw new Error('Failed to fetch circuit data');
        }
        const data = await response.json();
        setCircuits(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCircuits();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navbar />
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navbar />
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <div className="text-red-500 text-xl">Error: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Head>
        <title>F1 Circuits - Formula 1 Dashboard</title>
        <meta name="description" content="Formula 1 race circuits and track information" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Navbar />

      <main className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-white mb-8 page-title">F1 Circuits</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {circuits.map((circuit, index) => (
            <motion.div
              key={circuit.round}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-2xl">{countryFlags[circuit.country] || '🏁'}</span>
                    <h2 className="text-xl font-semibold text-white">{circuit.name}</h2>
                  </div>
                  {circuit.event.toLowerCase().includes('sprint') && (
                    <span className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                      Sprint
                    </span>
                  )}
                </div>
                
                <div className="space-y-2 text-gray-300">
                  <p><span className="font-medium">Country:</span> {circuit.country}</p>
                  <p><span className="font-medium">First Grand Prix:</span> {circuit.first_grand_prix}</p>
                  <p><span className="font-medium">Circuit Length:</span> {circuit.circuit_length} km</p>
                  <p><span className="font-medium">Number of Laps:</span> {circuit.number_of_laps}</p>
                  <p><span className="font-medium">Race Distance:</span> {circuit.race_distance} km</p>
                  <p><span className="font-medium">Lap Record:</span> {circuit.lap_record}</p>
                  <p><span className="font-medium">DRS Zones:</span> {circuit.drs_zones}</p>
                  <p><span className="font-medium">Track Type:</span> {circuit.track_type}</p>
                </div>
                
                {circuit.track_map && (
                  <div className="mt-4">
                    <img 
                      src={circuit.track_map} 
                      alt={`${circuit.name} track map`}
                      className="w-full h-auto rounded-lg"
                    />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </main>
    </div>
  );
} 