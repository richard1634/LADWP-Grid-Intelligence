import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { PriceDataPoint } from '../types';

interface PriceChartProps {
  data: PriceDataPoint[];
}

export function PriceChart({ data }: PriceChartProps) {
  // Safety check
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <p className="text-gray-600">No price data available</p>
      </div>
    );
  }

  // Sort by timestamp
  const sortedData = [...data].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Format data for Recharts
  const chartData = sortedData.map(point => ({
    time: new Date(point.timestamp).toLocaleString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }),
    price: Number(point.price.toFixed(2)),
    isSpike: point.is_spike,
    fullTimestamp: point.timestamp
  }));

  // Calculate statistics
  const prices = chartData.map(d => d.price);
  const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
  const maxPrice = Math.max(...prices);
  const minPrice = Math.min(...prices);
  const spikeCount = chartData.filter(d => d.isSpike).length;

  return (
    <div className="bg-white rounded-xl shadow-lg p-3 sm:p-6">
      <div className="mb-3 sm:mb-4">
        <h3 className="text-base sm:text-xl font-bold text-gray-800">Real-Time Energy Prices</h3>
        <p className="text-xs sm:text-sm text-gray-600 mt-1">
          Last 6 hours | Red dots indicate price spikes
        </p>
      </div>

      <ResponsiveContainer width="100%" height={300} className="sm:h-[400px]">
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="time" 
            angle={-45}
            textAnchor="end"
            height={70}
            tick={{ fontSize: 9 }}
            className="sm:text-[11px]"
          />
          <YAxis 
            label={{ value: 'Price ($/MWh)', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
            tick={{ fontSize: 10 }}
            domain={[0, 'auto']}
            width={50}
            className="sm:text-xs sm:w-[60px]"
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '12px'
            }}
            formatter={(value: number, name: string) => {
              if (name === 'price') return [`$${value}/MWh`, 'Price'];
              return [value, name];
            }}
            labelStyle={{ fontWeight: 'bold', marginBottom: '8px' }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          
          {/* Average price reference line */}
          <ReferenceLine 
            y={avgPrice} 
            stroke="#9ca3af" 
            strokeDasharray="5 5"
            label={{ 
              value: `Avg: $${avgPrice.toFixed(2)}`, 
              position: 'right', 
              fill: '#6b7280',
              fontSize: 11
            }}
          />

          {/* Main price line */}
          <Line
            type="monotone"
            dataKey="price"
            stroke="#0066CC"
            strokeWidth={2}
            dot={(props: any) => {
              const { cx, cy, payload } = props;
              if (payload.isSpike) {
                return (
                  <circle 
                    cx={cx} 
                    cy={cy} 
                    r={6} 
                    fill="#ef4444" 
                    stroke="#dc2626"
                    strokeWidth={2}
                  />
                );
              }
              return (
                <circle 
                  cx={cx} 
                  cy={cy} 
                  r={3} 
                  fill="#0066CC"
                />
              );
            }}
            name="Energy Price"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-4 gap-4 text-center">
        <div className="bg-blue-50 rounded-lg p-3">
          <p className="text-sm text-gray-600">Average Price</p>
          <p className="text-xl font-bold text-blue-600">${avgPrice.toFixed(2)}</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3">
          <p className="text-sm text-gray-600">Min Price</p>
          <p className="text-xl font-bold text-green-600">${minPrice.toFixed(2)}</p>
        </div>
        <div className="bg-orange-50 rounded-lg p-3">
          <p className="text-sm text-gray-600">Max Price</p>
          <p className="text-xl font-bold text-orange-600">${maxPrice.toFixed(2)}</p>
        </div>
        <div className={`rounded-lg p-3 ${spikeCount > 0 ? 'bg-red-50' : 'bg-gray-50'}`}>
          <p className="text-sm text-gray-600">Price Spikes</p>
          <p className={`text-xl font-bold ${spikeCount > 0 ? 'text-red-600' : 'text-gray-600'}`}>
            {spikeCount}
          </p>
        </div>
      </div>

      {spikeCount > 0 && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-red-800">
            ⚠️ {spikeCount} price spike{spikeCount > 1 ? 's' : ''} detected in the last 6 hours
          </p>
          <p className="text-xs text-red-600 mt-1">
            Price spikes may indicate grid stress or high demand periods
          </p>
        </div>
      )}
    </div>
  );
}
