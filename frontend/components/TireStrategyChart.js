import { useEffect, useRef } from 'react';
import { Chart } from 'chart.js/auto';

const compoundColors = {
  'SOFT': '#FF3333',
  'MEDIUM': '#FFD700',
  'HARD': '#FFFFFF',
  'INTERMEDIATE': '#00FF00',
  'WET': '#0000FF'
};

// Team colors mapping
const teamColors = {
  'Red Bull Racing': '#0600EF',
  'Mercedes': '#00D2BE',
  'Ferrari': '#DC0000',
  'McLaren': '#FF8700',
  'Aston Martin': '#006F62',
  'Alpine': '#0090FF',
  'Williams': '#005AFF',
  'AlphaTauri': '#2B4562',
  'Alfa Romeo': '#900000',
  'Haas F1 Team': '#FFFFFF'
};

export default function TireStrategyChart({ data, raceName }) {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!data || !chartRef.current) return;

    // Destroy existing chart if it exists
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    try {
      const ctx = chartRef.current.getContext('2d');
      
      // Check if data is in the expected format
      if (typeof data !== 'object' || Object.keys(data).length === 0) {
        console.error('Invalid tire strategy data format');
        return;
      }
      
      // Prepare data for the chart
      const drivers = Object.keys(data);
      
      // Find the maximum number of laps for scaling
      let maxLaps = 0;
      drivers.forEach(driver => {
        const stints = data[driver];
        if (Array.isArray(stints) && stints.length > 0) {
          const lastStint = stints[stints.length - 1];
          if (lastStint && typeof lastStint.end_lap === 'number') {
            maxLaps = Math.max(maxLaps, lastStint.end_lap);
          }
        }
      });

      // Create datasets for each driver's stints
      const datasets = [];
      
      drivers.forEach(driver => {
        const stints = data[driver];
        if (!Array.isArray(stints)) return;
        
        stints.forEach(stint => {
          if (!stint || typeof stint.start_lap !== 'number' || typeof stint.end_lap !== 'number') return;
          
          datasets.push({
            label: driver,
            data: [{
              x: stint.start_lap,
              y: driver,
              width: stint.end_lap - stint.start_lap,
              compound: stint.compound
            }],
            backgroundColor: compoundColors[stint.compound] || '#808080',
            borderColor: '#000000',
            borderWidth: 1,
            barPercentage: 0.95,
            categoryPercentage: 0.95,
            stack: driver
          });
        });
      });

      // Only create the chart if we have valid datasets
      if (datasets.length > 0) {
        // Create the chart
        chartInstance.current = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: drivers,
            datasets: datasets
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: {
                display: true,
                text: `${raceName || 'Race'} Tire Strategy`,
                color: '#FFFFFF',
                font: {
                  size: 16
                }
              },
              legend: {
                display: false
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const data = context.raw;
                    return `${data.compound} (Laps ${data.x} to ${data.x + data.width})`;
                  }
                }
              }
            },
            scales: {
              x: {
                stacked: true,
                type: 'linear',
                position: 'bottom',
                min: 0,
                max: maxLaps,
                title: {
                  display: true,
                  text: 'Lap Number',
                  color: '#FFFFFF'
                },
                grid: {
                  color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                  color: '#FFFFFF',
                  stepSize: 5
                }
              },
              y: {
                stacked: true,
                title: {
                  display: true,
                  text: 'Driver',
                  color: '#FFFFFF'
                },
                grid: {
                  display: false
                },
                ticks: {
                  color: '#FFFFFF'
                }
              }
            }
          }
        });
      }
    } catch (error) {
      console.error('Error creating tire strategy chart:', error);
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data, raceName]);

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-gray-400">Tire strategy data is not available for this race.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="h-[600px]">
        <canvas ref={chartRef} />
      </div>
      <div className="mt-4 flex flex-wrap gap-4 justify-center">
        {Object.entries(compoundColors).map(([compound, color]) => (
          <div key={compound} className="flex items-center">
            <div
              className="w-4 h-4 mr-2 border border-gray-600"
              style={{ backgroundColor: color }}
            />
            <span className="text-gray-300">{compound}</span>
          </div>
        ))}
      </div>
    </div>
  );
} 