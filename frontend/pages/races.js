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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {races.map((race) => (
              <button
                key={race.round}
                onClick={() => setSelectedRace(race)}
                className={`p-4 rounded-lg text-left transition-all duration-200 ${
                  selectedRace?.round === race.round
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <div className="font-semibold">{race.name}</div>
                <div className="text-sm text-gray-400">{race.date}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Position Changes Graph */}
        {selectedRace && (
          <div className="bg-gray-800 rounded-lg p-6">
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
      </div>
    </Layout>
  );
} 