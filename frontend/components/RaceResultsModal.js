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
          className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/80 overflow-y-auto"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="relative w-full max-w-4xl max-h-[90vh] my-4 bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-2xl overflow-hidden flex flex-col"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-3 sm:p-4 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
              <h2 className="text-lg sm:text-xl font-bold text-white truncate pr-4">{raceName} Results</h2>
              <button
                onClick={onClose}
                className="p-1 rounded-full hover:bg-gray-700 text-gray-400 hover:text-white transition-colors flex-shrink-0"
              >
                <XMarkIcon className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
            </div>

            {/* Results Table */}
            <div className="overflow-x-auto flex-grow">
              <table className="w-full">
                <thead className="sticky top-0 bg-gray-800 z-10">
                  <tr>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-400 whitespace-nowrap">Pos</th>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-400 whitespace-nowrap">Driver</th>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-400 whitespace-nowrap">Team</th>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-400 whitespace-nowrap">Points</th>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-400 whitespace-nowrap">Grid</th>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-400 whitespace-nowrap">Gained</th>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-400 whitespace-nowrap">Pits</th>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs sm:text-sm font-medium text-gray-400 whitespace-nowrap">Fastest Lap</th>
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
                      <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm font-medium text-white whitespace-nowrap">
                        {result.position}
                      </td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <div
                            className="w-2 h-2 sm:w-3 sm:h-3 rounded-full mr-1 sm:mr-2"
                            style={{ backgroundColor: result.driver_color }}
                          />
                          <span className="text-xs sm:text-sm font-medium text-white">
                            {result.driver_name}
                          </span>
                        </div>
                      </td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm whitespace-nowrap">
                        <span style={{ color: result.driver_color }}>{result.team}</span>
                      </td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm font-medium text-white whitespace-nowrap">{result.points}</td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm text-gray-400 whitespace-nowrap">{result.qualifying_position}</td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm text-gray-400 whitespace-nowrap">
                        {result.positions_gained > 0 ? '+' : ''}{result.positions_gained}
                      </td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm text-gray-400 whitespace-nowrap">{result.pit_stops}</td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm text-gray-400 whitespace-nowrap">{result.fastest_lap_time}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile-friendly scroll indicator */}
            <div className="md:hidden p-2 text-center text-gray-400 text-xs sm:text-sm border-t border-gray-700 bg-gray-800">
              <span className="inline-flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
                </svg>
                Scroll horizontally to see all columns
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
} 