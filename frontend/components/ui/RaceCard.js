export default function RaceCard({ race }) {
  return (
    <div className="bg-gray-900 rounded-lg border border-red-600 overflow-hidden">
      <div className="p-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-xl font-bold text-red-500">{race.race_name}</h3>
            <p className="text-gray-400">{race.location}</p>
            <p className="text-gray-400">{race.date}</p>
          </div>
          <div className="text-right">
            <span className="inline-block px-3 py-1 text-sm font-semibold text-white bg-red-600 rounded-full">
              Round {race.round}
            </span>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="bg-gray-800 p-3 rounded">
            <p className="text-sm text-gray-400">Country</p>
            <p className="text-white font-medium">{race.country}</p>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <p className="text-sm text-gray-400">Event</p>
            <p className="text-white font-medium">{race.event}</p>
          </div>
        </div>
      </div>
    </div>
  );
} 