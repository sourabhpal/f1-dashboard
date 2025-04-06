// Function to format driver name with last name in uppercase
const formatDriverName = (fullName) => {
  if (!fullName) return '';
  const parts = fullName.split(' ');
  if (parts.length > 1) {
    const firstName = parts[0];
    const lastName = parts.slice(1).join(' ').toUpperCase();
    return `${firstName} ${lastName}`;
  }
  return fullName;
};

// Update the table row rendering
<tbody className="divide-y divide-gray-700">
  {standings.map((driver, index) => (
    <tr key={index} className="hover:bg-gray-700 transition-colors">
      <td className="px-4 py-3 text-white">{driver.position}</td>
      <td className="px-4 py-3">
        <div className="flex items-center">
          <div
            className="w-3 h-3 rounded-full mr-2"
            style={{ backgroundColor: driver.team_color || '#ff0000' }}
          />
          <span className="text-white" style={{ fontFamily: 'Audiowide, sans-serif' }}>
            {formatDriverName(driver.driver_name)}
          </span>
        </div>
      </td>
      <td className="px-4 py-3 text-white" style={{ fontFamily: 'Audiowide, sans-serif' }}>#{driver.driver_number}</td>
      <td className="px-4 py-3 text-white">{driver.team}</td>
      <td className="px-4 py-3 text-white">{driver.points}</td>
    </tr>
  ))}
</tbody> 