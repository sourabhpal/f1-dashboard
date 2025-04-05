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

    const ctx = chartRef.current.getContext('2d');
    
    // Prepare data for the chart
    const drivers = Object.keys(data);
    
    // Find the maximum number of laps for scaling
    let maxLaps = 0;
    drivers.forEach(driver => {
      const stints = data[driver];
      if (stints.length > 0) {
        const lastStint = stints[stints.length - 1];
        maxLaps = Math.max(maxLaps, lastStint.end_lap);
      }
    });

    // Create datasets for each driver's stints
    const datasets = [];
    
    drivers.forEach(driver => {
      const stints = data[driver];
      stints.forEach(stint => {
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
            text: `${raceName} Tire Strategy`,
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

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data, raceName]);

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