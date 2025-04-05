export default function QualifyingResults({ results }) {
  return (
    <div className="bg-gray-900 rounded-lg border border-red-600 overflow-hidden">
      <div className="p-4">
        <h3 className="text-xl font-bold text-red-500 mb-4">Qualifying Results</h3>
        <div className="space-y-2">
          {results?.map((result, index) => (
            <div
              key={result.driverId}
              className="flex items-center justify-between p-3 bg-gray-800 rounded-lg"
            >
              <div className="flex items-center space-x-4">
                <span className="text-2xl font-bold text-red-500 w-8">{index + 1}</span>
                <div>
                  <p className="text-white font-medium">{result.driverName}</p>
                  <p className="text-gray-400 text-sm">{result.team}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-white font-bold">{result.q3Time}</p>
                <p className="text-gray-400 text-sm">Q3</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 