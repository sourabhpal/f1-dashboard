import { useState, useEffect } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import TireStrategyChart from '../components/TireStrategyChart';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function Races() {
  const [races, setRaces] = useState([]);
  const [selectedRace, setSelectedRace] = useState(null);
  const [positionData, setPositionData] = useState(null);
  const [teamPaceData, setTeamPaceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingPace, setLoadingPace] = useState(false);
  const [error, setError] = useState(null);
  const [paceError, setPaceError] = useState(null);
  const [tireStrategyData, setTireStrategyData] = useState(null);
  const [loadingStrategy, setLoadingStrategy] = useState(false);
  const [strategyError, setStrategyError] = useState(null);

  useEffect(() => {
    const fetchRaces = async () => {
      try {
        const response = await fetch('http://localhost:8000/schedule/2025');
        if (!response.ok) throw new Error('Failed to fetch races');
        const data = await response.json();
        setRaces(data);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchRaces();
  }, []);

  useEffect(() => {
    const fetchPositionData = async () => {
      if (!selectedRace) return;

      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8000/race/2025/${selectedRace.round}/positions`);
        if (!response.ok) throw new Error('Failed to fetch position data');
        const data = await response.json();
        setPositionData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPositionData();
  }, [selectedRace]);

  useEffect(() => {
    const fetchTeamPaceData = async () => {
      if (!selectedRace) return;

      setLoadingPace(true);
      setPaceError(null);
      try {
        const response = await fetch(`http://localhost:8000/race/2025/${selectedRace.round}/team-pace`);
        if (!response.ok) throw new Error('Failed to fetch team pace data');
        const data = await response.json();
        setTeamPaceData(data);
      } catch (err) {
        setPaceError(err.message);
      } finally {
        setLoadingPace(false);
      }
    };

    fetchTeamPaceData();
  }, [selectedRace]);

  useEffect(() => {
    const fetchTireStrategyData = async () => {
      if (!selectedRace) return;

      setLoadingStrategy(true);
      setStrategyError(null);
      try {
        const response = await fetch(`http://localhost:8000/race/2025/${selectedRace.round}/tire-strategy`);
        if (!response.ok) throw new Error('Failed to fetch tire strategy data');
        const data = await response.json();
        setTireStrategyData(data);
      } catch (err) {
        setStrategyError(err.message);
      } finally {
        setLoadingStrategy(false);
      }
    };

    fetchTireStrategyData();
  }, [selectedRace]);

  const chartData = positionData ? {
    labels: positionData[Object.keys(positionData)[0]]?.lap_numbers || [],
    datasets: Object.entries(positionData).map(([abb, data]) => ({
      label: `${data.driver_name} (${data.team})`,
      data: data.positions,
      borderColor: data.color,
      backgroundColor: data.color,
      tension: 0.1,
      fill: false,
    })),
  } : null;

  const paceChartData = teamPaceData ? {
    labels: teamPaceData.lap_numbers || [],
    datasets: teamPaceData.teams.map(team => ({
      label: team.name,
      data: team.lap_times,
      borderColor: team.color,
      backgroundColor: team.color,
      tension: 0.1,
      fill: false,
    })),
  } : null;

  const chartOptions = {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      y: {
        reverse: true,
        min: 0.5,
        max: 20.5,
        ticks: {
          stepSize: 1,
        },
        title: {
          display: true,
          text: 'Position',
          color: '#fff',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Lap',
          color: '#fff',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
    },
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: '#fff',
        },
      },
    },
  };

  const paceChartOptions = {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      y: {
        title: {
          display: true,
          text: 'Lap Time (seconds)',
          color: '#fff',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        ticks: {
          color: '#fff',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Lap',
          color: '#fff',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        ticks: {
          color: '#fff',
        },
      },
    },
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: '#fff',
        },
      },
    },
  };

  return (
    <Layout>
      <Head>
        <title>Race Data - F1 Dashboard</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">Race Data</h1>

        {/* Race Selection */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Select a Race</h2>
          <div className="relative">
            <select
              value={selectedRace?.round || ''}
              onChange={(e) => {
                const race = races.find(r => r.round === parseInt(e.target.value));
                setSelectedRace(race);
              }}
              className="w-full bg-gray-700 text-white py-3 px-4 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="" disabled>Choose a race...</option>
              {races.map((race) => (
                <option key={race.round} value={race.round}>
                  {race.round}. {race.name} - {race.date}
                </option>
              ))}
            </select>
            <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        {/* Position Changes Graph */}
        {selectedRace && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">
              Position Changes - {selectedRace.name}
            </h2>
            {loading ? (
              <div className="text-white">Loading position data...</div>
            ) : error ? (
              <div className="text-red-500">Error: {error}</div>
            ) : chartData ? (
              <div className="h-[600px]">
                <Line data={chartData} options={chartOptions} />
              </div>
            ) : (
              <div className="text-white">No position data available</div>
            )}
          </div>
        )}

        {/* Team Pace Comparison Graph */}
        {selectedRace && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">
              Team Pace Comparison - {selectedRace.name}
            </h2>
            {loadingPace ? (
              <div className="text-white">Loading team pace data...</div>
            ) : paceError ? (
              <div className="text-red-500">Error: {paceError}</div>
            ) : paceChartData ? (
              <div className="h-[600px]">
                <Line data={paceChartData} options={paceChartOptions} />
              </div>
            ) : (
              <div className="text-white">No team pace data available</div>
            )}
          </div>
        )}

        {/* Tire Strategy Chart */}
        {selectedRace && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">
              Tire Strategy - {selectedRace.name}
            </h2>
            {loadingStrategy ? (
              <div className="text-white">Loading tire strategy data...</div>
            ) : strategyError ? (
              <div className="text-red-500">Error: {strategyError}</div>
            ) : tireStrategyData ? (
              <TireStrategyChart data={tireStrategyData} raceName={selectedRace.name} />
            ) : (
              <div className="text-white">No tire strategy data available</div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
} 