import { useState } from 'react';

export default function Header({ onYearChange, onRoundChange, onViewChange }) {
  const [selectedYear, setSelectedYear] = useState(2024);
  const [selectedRound, setSelectedRound] = useState(1);
  const [selectedView, setSelectedView] = useState('race');
  const years = Array.from({ length: 5 }, (_, i) => 2024 - i);
  const rounds = Array.from({ length: 24 }, (_, i) => i + 1);

  const handleYearChange = (e) => {
    const year = Number(e.target.value);
    setSelectedYear(year);
    onYearChange?.(year);
  };

  const handleRoundChange = (e) => {
    const round = Number(e.target.value);
    setSelectedRound(round);
    onRoundChange?.(round);
  };

  const handleViewChange = (view) => {
    setSelectedView(view);
    onViewChange?.(view);
  };

  const navItems = [
    { id: 'race', label: 'Race' },
    { id: 'qualifying', label: 'Qualifying' },
    { id: 'standings', label: 'Standings' },
    { id: 'driver', label: 'Driver Stats' }
  ];

  return (
    <header className="bg-black border-b border-red-600">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col space-y-4 py-4">
          {/* Top row with logo and filters */}
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-red-600">F1 Dashboard</h1>
              <div className="hidden md:flex items-center space-x-2 text-gray-400">
                <span>Season</span>
                <select
                  value={selectedYear}
                  onChange={handleYearChange}
                  className="bg-gray-900 text-white border border-red-600 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  {years.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
                <span>Round</span>
                <select
                  value={selectedRound}
                  onChange={handleRoundChange}
                  className="bg-gray-900 text-white border border-red-600 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  {rounds.map((round) => (
                    <option key={round} value={round}>
                      Round {round}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Navigation tabs */}
          <div className="flex space-x-4 border-t border-gray-800 pt-4 overflow-x-auto">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleViewChange(item.id)}
                className={`px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${
                  selectedView === item.id
                    ? 'bg-red-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Mobile filters */}
          <div className="md:hidden flex items-center space-x-2 text-gray-400">
            <span>Season</span>
            <select
              value={selectedYear}
              onChange={handleYearChange}
              className="bg-gray-900 text-white border border-red-600 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
            <span>Round</span>
            <select
              value={selectedRound}
              onChange={handleRoundChange}
              className="bg-gray-900 text-white border border-red-600 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              {rounds.map((round) => (
                <option key={round} value={round}>
                  Round {round}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </header>
  );
} 