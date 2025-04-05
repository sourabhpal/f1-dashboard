import { motion } from 'framer-motion';

export default function PitStopStrategy({ strategy }) {
  const tireColors = {
    'SOFT': '#FF0000',
    'MEDIUM': '#FFA500',
    'HARD': '#FFFFFF',
    'INTERMEDIATE': '#00FF00',
    'WET': '#0000FF'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-900 rounded-lg border border-red-600 overflow-hidden"
    >
      <div className="p-4">
        <h3 className="text-xl font-bold text-red-500 mb-4">Pit Stop Strategy</h3>
        
        {/* Race Progress Bar */}
        <div className="relative h-2 bg-gray-800 rounded-full mb-6">
          <div 
            className="absolute h-full bg-red-600 rounded-full"
            style={{ width: `${(strategy.currentLap / strategy.totalLaps) * 100}%` }}
          />
          <div className="absolute top-0 left-0 w-full h-full flex justify-between px-2">
            {strategy.pitStops.map((stop, index) => (
              <div
                key={index}
                className="w-1 h-4 bg-white -mt-1"
                style={{ left: `${(stop.lap / strategy.totalLaps) * 100}%` }}
              />
            ))}
          </div>
        </div>

        {/* Pit Stop Details */}
        <div className="space-y-4">
          {strategy.pitStops.map((stop, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gray-800 p-4 rounded-lg"
            >
              <div className="flex justify-between items-center mb-2">
                <span className="text-white font-medium">Pit Stop {index + 1}</span>
                <span className="text-gray-400">Lap {stop.lap}</span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div
                    className="w-6 h-6 rounded-full"
                    style={{ backgroundColor: tireColors[stop.oldTire] }}
                  />
                  <span className="text-gray-400">→</span>
                  <div
                    className="w-6 h-6 rounded-full"
                    style={{ backgroundColor: tireColors[stop.newTire] }}
                  />
                </div>
                <span className="text-white">{stop.duration}s</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Tire Usage Summary */}
        <div className="mt-6">
          <h4 className="text-lg font-semibold text-white mb-3">Tire Usage</h4>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(strategy.tireUsage).map(([tire, laps]) => (
              <motion.div
                key={tire}
                whileHover={{ scale: 1.02 }}
                className="bg-gray-800 p-3 rounded-lg text-center"
              >
                <div
                  className="w-8 h-8 rounded-full mx-auto mb-2"
                  style={{ backgroundColor: tireColors[tire] }}
                />
                <p className="text-gray-400 text-sm">{tire}</p>
                <p className="text-white font-bold">{laps} laps</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
} 