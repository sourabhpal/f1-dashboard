import { useState, useEffect } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import Layout from '../components/Layout';
import Image from 'next/image';
import { API_URL } from '../config';

// Feature categories with icons
const featureCategories = [
  {
    title: 'Race Information',
    icon: '🏎️',
    features: [
      { name: 'Race Schedule', description: 'Complete F1 calendar with race dates and venues' },
      { name: 'Race Results', description: 'Detailed race results and podium finishes' },
      { name: 'Qualifying', description: 'Qualifying session results and grid positions' }
    ]
  },
  {
    title: 'Driver Statistics',
    icon: '👤',
    features: [
      { name: 'Driver Standings', description: 'Current season driver championship standings' },
      { name: 'Driver Performance', description: 'Individual driver statistics and achievements' },
      { name: 'Race History', description: 'Historical race results and performance data' }
    ]
  },
  {
    title: 'Team Analytics',
    icon: '🏆',
    features: [
      { name: 'Constructor Standings', description: 'Team championship standings and points' },
      { name: 'Team Performance', description: 'Team statistics and race performance' },
      { name: 'Car Development', description: 'Team car development and upgrades' }
    ]
  },
  {
    title: 'Race Analysis',
    icon: '📊',
    features: [
      { name: 'Race Timing', description: 'Detailed lap times and race timing data' },
      { name: 'Pit Stop Analysis', description: 'Pit stop strategies and timing analysis' },
      { name: 'Weather Conditions', description: 'Race weather data and conditions' }
    ]
  }
];

// Country to flag emoji mapping
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

export default function Home() {
  const [standings, setStandings] = useState([]);
  const [nextRace, setNextRace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [countdown, setCountdown] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [quickStats, setQuickStats] = useState({
    mostWins: { driver: '', wins: 0, team: '', team_color: '#ff0000' },
    mostPitStops: { driver: '', pits: 0, team: '', team_color: '#ff0000' },
    mostPoles: { driver: '', poles: 0, team: '', team_color: '#ff0000' },
    mostOvertakes: { driver: '', overtakes: 0, team: '', team_color: '#ff0000' }
  });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch standings
        const standingsResponse = await fetch(`${API_URL}/standings/2025`);
        if (!standingsResponse.ok) throw new Error('Failed to fetch standings');
        const standingsData = await standingsResponse.json();
        setStandings(standingsData);

        // Fetch next race
        const scheduleResponse = await fetch(`${API_URL}/schedule/2025`);
        if (!scheduleResponse.ok) throw new Error('Failed to fetch schedule');
        const scheduleData = await scheduleResponse.json();
        
        // Find the next race
        const now = new Date();
        const nextRaceData = scheduleData.find(race => new Date(race.date) > now);
        setNextRace(nextRaceData);

        // Fetch quick stats
        const quickStatsResponse = await fetch(`${API_URL}/quick-stats/2025`);
        if (!quickStatsResponse.ok) throw new Error('Failed to fetch quick stats');
        const quickStatsData = await quickStatsResponse.json();
        setQuickStats(quickStatsData);

        // Calculate countdown
        if (nextRaceData) {
          const raceDate = new Date(nextRaceData.date);
          const updateCountdown = () => {
            const now = new Date();
            const diff = raceDate - now;
            
            setCountdown({
              days: Math.floor(diff / (1000 * 60 * 60 * 24)),
              hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
              minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
              seconds: Math.floor((diff % (1000 * 60)) / 1000)
            });
          };

          updateCountdown();
          const timer = setInterval(updateCountdown, 1000);
          return () => clearInterval(timer);
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <Layout>
      <Head>
        <title>Monty's F1 Dashboard</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-900/80 backdrop-blur-sm rounded-xl p-8 shadow-xl max-w-7xl mx-auto mb-12 relative overflow-hidden border border-gray-800"
        >
          {/* Animated racing lines */}
          <div className="absolute inset-0 overflow-hidden">
            {/* Primary racing line */}
            <motion.div 
              className="absolute h-0.5 bg-[#E10600]/30 rounded-full"
              style={{ 
                width: '100%', 
                top: '25%',
                left: '-100%',
                boxShadow: '0 0 15px rgba(225,6,0,0.3)'
              }}
              animate={{ 
                left: ['-100%', '100%'],
              }}
              transition={{ 
                duration: 2.5,
                repeat: Infinity,
                ease: "linear"
              }}
            />
            <motion.div 
              className="absolute h-0.5 bg-[#E10600]/30 rounded-full"
              style={{ 
                width: '100%', 
                top: '75%',
                left: '-100%',
                boxShadow: '0 0 15px rgba(225,6,0,0.3)'
              }}
              animate={{ 
                left: ['100%', '-100%'],
              }}
              transition={{ 
                duration: 2.5,
                repeat: Infinity,
                ease: "linear"
              }}
            />
            
            {/* Secondary racing lines */}
            <motion.div 
              className="absolute h-0.5 bg-[#E10600]/20 rounded-full"
              style={{ 
                width: '100%', 
                top: '40%',
                left: '-100%',
                boxShadow: '0 0 8px rgba(225,6,0,0.2)'
              }}
              animate={{ 
                left: ['-100%', '100%'],
              }}
              transition={{ 
                duration: 3.5,
                repeat: Infinity,
                ease: "linear"
              }}
            />
            <motion.div 
              className="absolute h-0.5 bg-[#E10600]/20 rounded-full"
              style={{ 
                width: '100%', 
                top: '60%',
                left: '-100%',
                boxShadow: '0 0 8px rgba(225,6,0,0.2)'
              }}
              animate={{ 
                left: ['100%', '-100%'],
              }}
              transition={{ 
                duration: 3.5,
                repeat: Infinity,
                ease: "linear"
              }}
            />
          </div>
          
          <div className="flex flex-col items-center justify-center relative z-10">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-center mb-3"
            >
              <h1 
                className="text-4xl md:text-5xl font-bold page-title"
                style={{ 
                  color: '#E10600',
                  textShadow: '0 0 20px rgba(225,6,0,0.3)',
                  fontFamily: 'Audiowide, sans-serif',
                  letterSpacing: '1px'
                }}
              >
                Monty's F1 Dashboard
              </h1>
            </motion.div>
            <motion.p 
              className="text-gray-300 text-lg md:text-xl text-center max-w-2xl"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              Comprehensive Formula 1 statistics, race results, and analysis
            </motion.p>
          </div>
        </motion.div>
      </div>

      {/* Season Quick Stats */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-8 mb-8 shadow-xl">
        <h2 className="text-2xl font-bold text-white mb-8 page-title text-center">Season Quick Stats</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow duration-300 min-h-[180px] flex flex-col"
            style={{
              borderLeft: `4px solid ${quickStats.mostWins.team_color || '#ff0000'}`,
            }}
          >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>
              <span className="mr-2">🏆</span> Most Wins
            </h3>
            <div className="flex-grow flex flex-col justify-center">
              <p className="text-2xl font-bold mb-2" style={{ 
                color: quickStats.mostWins.team_color || '#ff0000',
                fontFamily: 'Audiowide, sans-serif',
                fontWeight: 'normal',
                letterSpacing: '0.5px'
              }}>
                {formatDriverName(quickStats.mostWins.driver)}
              </p>
              <p className="text-gray-400 tracking-wider mb-2" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{quickStats.mostWins.wins} wins</p>
              <p className="text-sm text-gray-500 break-words" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{quickStats.mostWins.team}</p>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow duration-300 min-h-[180px] flex flex-col"
            style={{
              borderLeft: `4px solid ${quickStats.mostPitStops.team_color || '#ff0000'}`,
            }}
          >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>
              <span className="mr-2">⛽</span> Most Pit Stops
            </h3>
            <div className="flex-grow flex flex-col justify-center">
              <p className="text-2xl font-bold mb-2" style={{ 
                color: quickStats.mostPitStops.team_color || '#ff0000',
                fontFamily: 'Audiowide, sans-serif',
                fontWeight: 'normal',
                letterSpacing: '0.5px'
              }}>
                {formatDriverName(quickStats.mostPitStops.driver)}
              </p>
              <p className="text-gray-400 tracking-wider mb-2" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{quickStats.mostPitStops.pits} stops</p>
              <p className="text-sm text-gray-500 break-words" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{quickStats.mostPitStops.team}</p>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow duration-300 min-h-[180px] flex flex-col"
            style={{
              borderLeft: `4px solid ${quickStats.mostPoles.team_color || '#ff0000'}`,
            }}
          >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>
              <span className="mr-2">🚩</span> Most Poles
            </h3>
            <div className="flex-grow flex flex-col justify-center">
              <p className="text-2xl font-bold mb-2" style={{ 
                color: quickStats.mostPoles.team_color || '#ff0000',
                fontFamily: 'Audiowide, sans-serif',
                fontWeight: 'normal',
                letterSpacing: '0.5px'
              }}>
                {formatDriverName(quickStats.mostPoles.driver)}
              </p>
              <p className="text-gray-400 tracking-wider mb-2" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{quickStats.mostPoles.poles} poles</p>
              <p className="text-sm text-gray-500 break-words" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{quickStats.mostPoles.team}</p>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow duration-300 min-h-[180px] flex flex-col"
            style={{
              borderLeft: `4px solid ${quickStats.mostOvertakes.team_color || '#ff0000'}`,
            }}
          >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>
              <span className="mr-2">🔄</span> Most Overtakes
            </h3>
            <div className="flex-grow flex flex-col justify-center">
              <p className="text-2xl font-bold mb-2" style={{ 
                color: quickStats.mostOvertakes.team_color || '#ff0000',
                fontFamily: 'Audiowide, sans-serif',
                fontWeight: 'normal',
                letterSpacing: '0.5px'
              }}>
                {formatDriverName(quickStats.mostOvertakes.driver)}
              </p>
              <p className="text-gray-400 tracking-wider mb-2" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{quickStats.mostOvertakes.overtakes} positions</p>
              <p className="text-sm text-gray-500 break-words" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{quickStats.mostOvertakes.team}</p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Next Race & Circuit Preview */}
      {nextRace && (
        <div className="bg-gray-900 py-8">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              {/* Next Race Info */}
              <div className="text-center flex flex-col justify-center">
                <h2 className="text-2xl font-bold text-white mb-4">
                  <span className="mr-2">{countryFlags[nextRace.country] || '🏎️'}</span>
                  {nextRace.name}
                </h2>
                <p className="text-gray-400 mb-6">{nextRace.date}</p>
                <div className="flex justify-center space-x-4">
                  {Object.entries(countdown).map(([unit, value]) => (
                    <div key={unit} className="text-center">
                      <div className="bg-red-600 text-white rounded-lg p-4 w-20">
                        <div className="text-2xl font-bold">{value}</div>
                        <div className="text-sm uppercase">
                          {unit === 'minutes' ? 'mins' : unit === 'seconds' ? 'secs' : unit}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Circuit Preview */}
              <div className="bg-gray-800 rounded-lg p-6 flex flex-col justify-center">
                <h3 className="text-xl font-bold text-white mb-4">Circuit Preview</h3>
                <div className="relative w-full aspect-[16/9] rounded-lg overflow-hidden bg-gray-700">
                  <Image
                    src="/images/circuits/default-circuit.jpg"
                    alt={`${nextRace?.name || 'Next Race'} Circuit`}
                    fill
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    className="object-contain"
                    priority
                    onError={(e) => {
                      e.target.src = '/images/circuits/default-circuit.jpg';
                    }}
                  />
                </div>
                {nextRace && (
                  <div className="mt-4">
                    <h4 className="text-lg font-semibold text-white">
                      <span className="mr-2">{countryFlags[nextRace.country] || '🏎️'}</span>
                      {nextRace.name}
                    </h4>
                    <p className="text-gray-400">{nextRace.date}</p>
                    <p className="text-gray-400">{nextRace.country}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Current Driver and Constructor Standings */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-8 mb-8 shadow-xl">
        <h2 className="text-2xl font-bold text-white mb-8 page-title text-center">Current Standings</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {/* Driver Standings */}
          <div>
            <h3 className="text-xl font-bold text-white mb-6 page-title flex items-center">
              <span className="mr-2">👤</span> Driver Standings
            </h3>
            <div className="grid gap-5">
              {standings.slice(0, 3).map((driver, index) => (
                <motion.div
                  key={driver.driver_name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ 
                    scale: 1.02,
                    y: -5,
                    transition: { duration: 0.2 }
                  }}
                  className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg p-5 shadow-lg hover:shadow-xl transition-shadow duration-300 h-24 flex items-center"
                  style={{
                    borderLeft: `4px solid ${driver.driver_color || '#ff0000'}`,
                  }}
                >
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center">
                      <motion.div 
                        className="text-3xl font-bold mr-4"
                        style={{ color: driver.driver_color || '#ff0000' }}
                        whileHover={{ scale: 1.1 }}
                      >
                        {driver.position}
                      </motion.div>
                      <div className="flex items-center">
                        <div className="relative w-12 h-12 bg-gray-700 rounded-lg p-1 mr-3">
                          <Image
                            src={`/images/drivers/${driver.driver_name.toLowerCase().replace(/\s+/g, '-')}.png`}
                            alt={`${driver.driver_name}`}
                            fill
                            sizes="48px"
                            className="object-contain"
                            onError={(e) => {
                              e.target.src = '/images/drivers/default-driver.png';
                            }}
                          />
                        </div>
                        <div>
                          <h3 
                            className="text-xl font-medium"
                            style={{ 
                              color: driver.driver_color || '#ff0000',
                              fontFamily: 'Audiowide, sans-serif',
                              fontWeight: 'normal',
                              letterSpacing: '0.5px'
                            }}
                          >
                            {formatDriverName(driver.driver_name)}
                          </h3>
                          <p className="text-gray-400 text-xl" style={{ fontFamily: 'Genos, sans-serif', fontWeight: '500' }}>{driver.team}</p>
                        </div>
                      </div>
                    </div>
                    <motion.div 
                      className="text-2xl font-bold text-white tracking-wider ml-auto"
                      whileHover={{ scale: 1.1 }}
                      style={{ fontFamily: 'Audiowide, sans-serif' }}
                    >
                      {driver.total_points}
                      <span className="text-sm text-gray-400 ml-1" style={{ fontFamily: 'Genos, sans-serif' }}>pts</span>
                    </motion.div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Constructor Standings */}
          <div>
            <h3 className="text-xl font-bold text-white mb-6 page-title flex items-center">
              <span className="mr-2">🏆</span> Constructor Standings
            </h3>
            <div className="grid gap-5">
              {Object.values(standings.reduce((acc, driver) => {
                const team = driver.team;
                if (!acc[team]) {
                  acc[team] = {
                    team: team,
                    total_points: 0,
                    drivers: [],
                    driver_color: driver.driver_color
                  };
                }
                // Only add points and driver if not already added
                if (!acc[team].drivers.includes(driver.driver_name)) {
                  acc[team].total_points += driver.total_points;
                  acc[team].drivers.push(driver.driver_name);
                }
                return acc;
              }, {}))
              .sort((a, b) => b.total_points - a.total_points)
              .slice(0, 3)
              .map((team, index) => (
                <motion.div
                  key={team.team}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ 
                    scale: 1.02,
                    y: -5,
                    transition: { duration: 0.2 }
                  }}
                  className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg p-5 shadow-lg hover:shadow-xl transition-shadow duration-300 h-24 flex items-center"
                  style={{
                    borderLeft: `4px solid ${team.driver_color || '#ff0000'}`,
                  }}
                >
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center">
                      <motion.div 
                        className="text-3xl font-bold mr-4"
                        style={{ color: team.driver_color || '#ff0000' }}
                        whileHover={{ scale: 1.1 }}
                      >
                        {index + 1}
                      </motion.div>
                      <div className="flex items-center space-x-4">
                        <div className="relative w-12 h-12 bg-gray-800 rounded-lg p-1">
                          <Image
                            src={`/images/teams/${team.team.toLowerCase().replace(/\s+/g, '-')}.png`}
                            alt={`${team.team} logo`}
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
                            className="text-2xl font-medium"
                            style={{ 
                              color: team.driver_color || '#ff0000',
                              fontFamily: 'Genos, sans-serif',
                              fontWeight: '700',
                              letterSpacing: '0.5px'
                            }}
                          >
                            {team.team}
                          </h3>
                          <p className="text-gray-400 text-sm" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{team.drivers.join(' / ')}</p>
                        </div>
                      </div>
                    </div>
                    <motion.div 
                      className="text-2xl font-bold text-white tracking-wider ml-auto"
                      whileHover={{ scale: 1.1 }}
                      style={{ fontFamily: 'Audiowide, sans-serif' }}
                    >
                      {team.total_points}
                      <span className="text-sm text-gray-400 ml-1" style={{ fontFamily: 'Genos, sans-serif' }}>pts</span>
                    </motion.div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Feature Categories */}
      <div className="bg-gray-900 py-12">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">Explore F1 Data</h2>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {featureCategories.map((category, index) => (
              <motion.div
                key={category.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-800 rounded-lg p-6 shadow-lg"
              >
                <div className="text-4xl mb-4">{category.icon}</div>
                <h3 className="text-xl font-semibold text-white mb-4">{category.title}</h3>
                <ul className="space-y-3">
                  {category.features.map((feature) => (
                    <li key={feature.name} className="text-gray-300">
                      <span className="text-red-500 mr-2">•</span>
                      {feature.name}
                      <p className="text-sm text-gray-400 mt-1">{feature.description}</p>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}