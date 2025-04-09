export default function TeamStandings({ standings }) {
  return (
    <div className="bg-gray-900 rounded-lg border border-red-600 overflow-hidden">
      <div className="p-4">
        <h3 className="text-xl font-bold text-red-500 mb-4">Constructor Standings</h3>
        <div className="space-y-2">
          {standings?.map((team, index) => (
            <div
              key={team.team}
              className="flex items-center justify-between p-3 bg-gray-800 rounded-lg"
            >
              <div className="flex items-center space-x-4">
                <span className="text-2xl font-bold text-red-500 w-8">{index + 1}</span>
                <div>
                  <p className="text-white font-medium">{team.team}</p>
                  <p className="text-gray-400 text-sm">
                    {team.wins} wins • {team.podiums} podiums
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-white font-bold text-lg">{team.total_points}</p>
                <div className="text-xs text-gray-400">
                  <span>Race: {team.points}</span>
                  {team.sprint_points > 0 && (
                    <span className="ml-2">Sprint: {team.sprint_points}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 