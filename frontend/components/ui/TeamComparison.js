import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function TeamComparison({ teams }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-900 rounded-lg border border-red-600 overflow-hidden"
    >
      <div className="p-4">
        <h3 className="text-xl font-bold text-red-500 mb-4">Team Comparison</h3>

        {/* Team Performance Chart */}
        <div className="h-[300px] mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={teams}>
              <XAxis dataKey="name" stroke="#fff" />
              <YAxis stroke="#fff" />
              <Tooltip
                contentStyle={{ backgroundColor: "#222", color: "#fff" }}
                labelStyle={{ color: "#ff0000" }}
              />
              <Bar dataKey="points" fill="#ff0000" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Team Statistics Grid */}
        <div className="grid grid-cols-2 gap-4">
          {teams.map((team, index) => (
            <motion.div
              key={team.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gray-800 p-4 rounded-lg"
            >
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center">
                  <span className="text-lg font-bold text-red-500">{index + 1}</span>
                </div>
                <div>
                  <h4 className="text-white font-medium">{team.name}</h4>
                  <p className="text-gray-400 text-sm">{team.drivers.join(' / ')}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-gray-400 text-sm">Points</p>
                  <p className="text-white font-bold">{team.points}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Wins</p>
                  <p className="text-white font-bold">{team.wins}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Poles</p>
                  <p className="text-white font-bold">{team.poles}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Fastest Laps</p>
                  <p className="text-white font-bold">{team.fastestLaps}</p>
                </div>
              </div>

              {/* Team Progress */}
              <div className="mt-3">
                <div className="h-1 bg-gray-700 rounded-full">
                  <div
                    className="h-full bg-red-600 rounded-full"
                    style={{ width: `${(team.points / Math.max(...teams.map(t => t.points))) * 100}%` }}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
} 