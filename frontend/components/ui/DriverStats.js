import { motion } from 'framer-motion';

export default function DriverStats({ driver, stats }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-900 rounded-lg border border-red-600 overflow-hidden"
    >
      <div className="p-4">
        <div className="flex items-center space-x-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center">
            <span className="text-2xl font-bold text-red-500">{driver.number}</span>
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">{driver.name}</h3>
            <p className="text-gray-400">{driver.team}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="bg-gray-800 p-4 rounded-lg"
          >
            <p className="text-gray-400 text-sm">Wins</p>
            <p className="text-2xl font-bold text-red-500">{stats.wins}</p>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="bg-gray-800 p-4 rounded-lg"
          >
            <p className="text-gray-400 text-sm">Poles</p>
            <p className="text-2xl font-bold text-red-500">{stats.poles}</p>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="bg-gray-800 p-4 rounded-lg"
          >
            <p className="text-gray-400 text-sm">Fastest Laps</p>
            <p className="text-2xl font-bold text-red-500">{stats.fastestLaps}</p>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="bg-gray-800 p-4 rounded-lg"
          >
            <p className="text-gray-400 text-sm">Points</p>
            <p className="text-2xl font-bold text-red-500">{stats.points}</p>
          </motion.div>
        </div>

        <div className="mt-6">
          <h4 className="text-lg font-semibold text-white mb-3">Season Performance</h4>
          <div className="space-y-2">
            {stats.raceResults.map((result, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between p-2 bg-gray-800 rounded"
              >
                <span className="text-gray-400">{result.race}</span>
                <span className={`font-bold ${
                  result.position === 1 ? 'text-yellow-400' :
                  result.position === 2 ? 'text-gray-300' :
                  result.position === 3 ? 'text-amber-700' :
                  'text-white'
                }`}>
                  P{result.position}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
} 