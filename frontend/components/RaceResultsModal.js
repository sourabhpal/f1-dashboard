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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-4xl p-6 mx-4 bg-gray-900 rounded-lg shadow-xl"
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white">{raceName}</h2>

              {results && results.length > 0 ? (
                <table className="min-w-full divide-y divide-gray-700">
                  <thead>
                    <tr className="text-left text-gray-300">
                      <th className="px-4 py-3">Pos</th>
                      <th className="px-4 py-3">Driver</th>
                      <th className="px-4 py-3">Team</th>
                      <th className="px-4 py-3">Gained</th>
                      <th className="px-4 py-3">Stops</th>
                      <th className="px-4 py-3">Points</th>
                      {results[0].sprint_position !== undefined && (
                        <>
                          <th className="px-4 py-3">Sprint Pos</th>
                          <th className="px-4 py-3">Sprint Pts</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {results.map((result, index) => (
                      <tr key={index} className="text-white hover:bg-gray-700 transition-colors">
                        <td className="px-4 py-3">{result.position}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center">
                            <div
                              className="w-3 h-3 rounded-full mr-2"
                              style={{ backgroundColor: result.team_color || '#ff0000' }}
                            />
                            {result.driver}
                          </div>
                        </td>
                        <td className="px-4 py-3">{result.team}</td>
                        <td className="px-4 py-3">
                          <span className={result.positions_gained > 0 ? 'text-green-500' : result.positions_gained < 0 ? 'text-red-500' : 'text-gray-400'}>
                            {result.positions_gained > 0 ? `+${result.positions_gained}` : result.positions_gained}
                          </span>
                        </td>
                        <td className="px-4 py-3">{result.pit_stops || 0}</td>
                        <td className="px-4 py-3">{result.points}</td>
                        {result.sprint_position !== undefined && (
                          <>
                            <td className="px-4 py-3">{result.sprint_position || '-'}</td>
                            <td className="px-4 py-3">{result.sprint_points || '-'}</td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
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