import { Fragment, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function RaceResultsModal({ isOpen, onClose, raceName, results }) {
  // Prevent background scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-2 sm:p-4 overflow-y-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-3xl max-h-[80vh] p-3 sm:p-6 bg-gray-900 rounded-lg shadow-xl my-4 mx-2 sm:mx-4 overflow-y-auto"
          >
            <button
              onClick={onClose}
              className="absolute top-1 right-1 sm:top-2 sm:right-2 text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="space-y-3 sm:space-y-4">
              <h2 className="text-lg sm:text-2xl font-bold text-white text-center">{raceName}</h2>

              {results && results.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-700">
                    <thead>
                      <tr className="text-left text-gray-300">
                        <th className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">Pos</th>
                        <th className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">Driver</th>
                        <th className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">Team</th>
                        <th className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">Gained</th>
                        <th className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">Stops</th>
                        <th className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">Points</th>
                        {results[0].sprint_position !== undefined && (
                          <>
                            <th className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">Sprint Pos</th>
                            <th className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">Sprint Pts</th>
                          </>
                        )}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                      {results.map((result, index) => (
                        <tr key={index} className="text-white hover:bg-gray-700 transition-colors">
                          <td className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">{result.position}</td>
                          <td className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">
                            <div className="flex items-center">
                              <div
                                className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full mr-1 sm:mr-2"
                                style={{ backgroundColor: result.team_color || '#ff0000' }}
                              />
                              {result.driver}
                            </div>
                          </td>
                          <td className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">{result.team}</td>
                          <td className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">
                            <span className={result.positions_gained > 0 ? 'text-green-500' : result.positions_gained < 0 ? 'text-red-500' : 'text-gray-400'}>
                              {result.positions_gained > 0 ? `+${result.positions_gained}` : result.positions_gained}
                            </span>
                          </td>
                          <td className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">{result.pit_stops || 0}</td>
                          <td className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">{result.points}</td>
                          {result.sprint_position !== undefined && (
                            <>
                              <td className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">{result.sprint_position || '-'}</td>
                              <td className="px-1 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm">{result.sprint_points || '-'}</td>
                            </>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-400">No results available</p>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
} 