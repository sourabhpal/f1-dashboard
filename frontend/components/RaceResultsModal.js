import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';

export default function RaceResultsModal({ isOpen, onClose, raceName, results }) {
  if (!isOpen || !results) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="relative w-full max-w-4xl bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-2xl overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="text-xl font-bold text-white">{raceName} Results</h2>
              <button
                onClick={onClose}
                className="p-1 rounded-full hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Results Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-800">
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Pos</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Driver</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Team</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Points</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Grid</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Gained</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Pits</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Fastest Lap</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {results.map((result, index) => (
                    <motion.tr
                      key={result.driver_number}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="hover:bg-gray-800/50 transition-colors"
                    >
                      <td className="px-4 py-3 text-sm font-medium text-white">
                        {result.position}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center">
                          <div
                            className="w-3 h-3 rounded-full mr-2"
                            style={{ backgroundColor: result.driver_color }}
                          />
                          <span className="text-sm font-medium text-white">
                            {result.driver_name}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-400">{result.team}</td>
                      <td className="px-4 py-3 text-sm font-medium text-white">{result.points}</td>
                      <td className="px-4 py-3 text-sm text-gray-400">{result.qualifying_position}</td>
                      <td className="px-4 py-3 text-sm text-gray-400">
                        {result.positions_gained > 0 ? '+' : ''}{result.positions_gained}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-400">{result.pit_stops}</td>
                      <td className="px-4 py-3 text-sm text-gray-400">{result.fastest_lap_time}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile-friendly scroll indicator */}
            <div className="md:hidden p-2 text-center text-gray-400 text-sm border-t border-gray-700">
              Scroll horizontally to see all columns
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
} 