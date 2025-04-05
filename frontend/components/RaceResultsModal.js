import { motion, AnimatePresence } from 'framer-motion';
import { useEffect } from 'react';

const RaceResultsModal = ({ isOpen, onClose, raceName, results }) => {
  // Prevent background scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-hidden">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 flex-shrink-0">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">{raceName} - Race Results</h2>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="overflow-y-auto flex-grow px-6 pb-6">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="sticky top-0 bg-gray-800 z-10">
                  <tr className="text-left text-sm font-medium text-gray-400">
                    <th className="px-4 py-3">Pos</th>
                    <th className="px-4 py-3">Driver</th>
                    <th className="px-4 py-3">Team</th>
                    <th className="px-4 py-3">Grid</th>
                    <th className="px-4 py-3">Gained</th>
                    <th className="px-4 py-3">Points</th>
                    <th className="px-4 py-3">Pits</th>
                    <th className="px-4 py-3">Fastest Lap</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {results?.map((result, index) => (
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
                      <td className="px-4 py-3">
                        <span style={{ color: result.team_color || '#ff0000' }}>
                          {result.team}
                        </span>
                      </td>
                      <td className="px-4 py-3">{result.grid}</td>
                      <td className="px-4 py-3">
                        <span className={result.positions_gained > 0 ? 'text-green-500' : result.positions_gained < 0 ? 'text-red-500' : ''}>
                          {result.positions_gained > 0 ? '+' : ''}{result.positions_gained}
                        </span>
                      </td>
                      <td className="px-4 py-3">{result.points}</td>
                      <td className="px-4 py-3">{result.pit_stops}</td>
                      <td className="px-4 py-3">{result.fastest_lap}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default RaceResultsModal; 