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
import { API_URL } from '../config';
import YearSelect from '../components/YearSelect';

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
  const [selectedYear, setSelectedYear] = useState(2025);
  const [raceData, setRaceData] = useState(null);
  const [availableYears, setAvailableYears] = useState([2025, 2024, 2023, 2022]);

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
    const fetchRaces = async () => {
      try {
        const response = await fetch(`${API_URL}/schedule/${selectedYear}`);
        if (!response.ok) throw new Error('Failed to fetch races');
        const data = await response.json();
        setRaces(data);
      } catch (err) {
        console.error('Error fetching races:', err);
        setError(err.message);
      }
    };

    fetchRaces();
  }, [selectedYear]);

  useEffect(() => {
    const fetchPositionData = async () => {
      if (!selectedRace) return;

      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_URL}/race/${selectedYear}/${selectedRace.round}/positions`);
        if (!response.ok) throw new Error('Failed to fetch position data');
        const data = await response.json();
        setPositionData(data);
      } catch (err) {
        console.error('Error fetching position data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPositionData();
  }, [selectedRace, selectedYear]);

  useEffect(() => {
    const fetchTeamPaceData = async () => {
      if (!selectedRace) return;

      setLoadingPace(true);
      setPaceError(null);
      try {
        const response = await fetch(`${API_URL}/race/${selectedYear}/${selectedRace.round}/team-pace`);
        if (!response.ok) throw new Error('Failed to fetch team pace data');
        const data = await response.json();
        setTeamPaceData(data);
      } catch (err) {
        console.error('Error fetching team pace data:', err);
        setPaceError(err.message);
      } finally {
        setLoadingPace(false);
      }
    };

    fetchTeamPaceData();
  }, [selectedRace, selectedYear]);

  useEffect(() => {
    const fetchTireStrategyData = async () => {
      if (!selectedRace) return;

      setLoadingStrategy(true);
      setStrategyError(null);
      try {
        const response = await fetch(`${API_URL}/race/${selectedYear}/${selectedRace.round}/tire-strategy`);
        if (!response.ok) throw new Error('Failed to fetch tire strategy data');
        const data = await response.json();
        setTireStrategyData(data);
      } catch (err) {
        console.error('Error fetching tire strategy data:', err);
        setStrategyError(err.message);
      } finally {
        setLoadingStrategy(false);
      }
    };

    fetchTireStrategyData();
  }, [selectedRace, selectedYear]);

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
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-white" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>F1 Race Data</h1>
          <YearSelect
            value={selectedYear}
            onChange={setSelectedYear}
            years={availableYears}
          />
        </div>

        {/* Race Selection */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>Select Race</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {races.map((race) => (
              <button
                key={race.round}
                onClick={() => setSelectedRace(race)}
                className={`p-4 rounded-lg text-left transition-all ${
                  selectedRace?.round === race.round
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                <h3 className="font-bold mb-1" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{race.name}</h3>
                <p className="text-sm" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>{race.date}</p>
              </button>
            ))}
          </div>
        </div>

        {selectedRace && (
          <div className="space-y-8">
            {/* Position Chart */}
            <div>
              <h2 className="text-2xl font-bold text-white mb-4" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>Race Positions</h2>
              {loading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
                </div>
              ) : error ? (
                <div className="bg-red-900/50 text-white p-4 rounded-lg">
                  <p>Error: {error}</p>
                </div>
              ) : (
                <div className="bg-gray-800 p-4 rounded-lg">
                  <Line data={chartData} options={chartOptions} />
                </div>
              )}
            </div>

            {/* Team Pace Chart */}
            <div>
              <h2 className="text-2xl font-bold text-white mb-4" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>Team Pace Comparison</h2>
              {loadingPace ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
                </div>
              ) : paceError ? (
                <div className="bg-red-900/50 text-white p-4 rounded-lg">
                  <p>Error: {paceError}</p>
                </div>
              ) : (
                <div className="bg-gray-800 p-4 rounded-lg">
                  <Line data={paceChartData} options={paceChartOptions} />
                </div>
              )}
            </div>

            {/* Tire Strategy Chart */}
            <div>
              <h2 className="text-2xl font-bold text-white mb-4" style={{ fontFamily: 'Roboto Variable, sans-serif' }}>Tire Strategy</h2>
              {loadingStrategy ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
                </div>
              ) : strategyError ? (
                <div className="bg-red-900/50 text-white p-4 rounded-lg">
                  <p>Error: {strategyError}</p>
                </div>
              ) : (
                <div className="bg-gray-800 p-4 rounded-lg">
                  <TireStrategyChart data={tireStrategyData} />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
} 