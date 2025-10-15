import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { DemandDataPoint } from '../types';

interface DemandForecastChartProps {
  data: DemandDataPoint[];
}

export function DemandForecastChart({ data }: DemandForecastChartProps) {
  // Safety check
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <p className="text-gray-600">No demand forecast data available</p>
      </div>
    );
  }

  // Format data for Recharts
  const chartData = data.map(point => ({
    time: new Date(point.timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      hour12: true
    }),
    demand: Math.round(point.demand_mw),
    forecast: point.is_forecast ? Math.round(point.demand_mw) : null,
    actual: !point.is_forecast ? Math.round(point.demand_mw) : null,
    fullTimestamp: point.timestamp
  }));

  // Find the transition point between actual and forecast
  const forecastStartIndex = data.findIndex(point => point.is_forecast);
  const currentDemand = forecastStartIndex > 0 ? data[forecastStartIndex - 1].demand_mw : data[0].demand_mw;

  return (
    <div className="bg-white rounded-xl shadow-lg p-3 sm:p-6">
      <div className="mb-3 sm:mb-4">
        <h3 className="text-base sm:text-xl font-bold text-gray-800">System Demand - Last 24h & Next 30h</h3>
        <p className="text-xs sm:text-sm text-gray-600 mt-1">
          Blue line shows last 24 hours historical, orange line shows CAISO 30-hour forecast
        </p>
      </div>

      <ResponsiveContainer width="100%" height={300} className="sm:h-[400px]">
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="time" 
            angle={-45}
            textAnchor="end"
            height={80}
            tick={{ fontSize: 9 }}
            interval={Math.floor(chartData.length / 6)} // Show fewer labels on mobile
            className="sm:text-[11px]"
          />
          <YAxis 
            label={{ value: 'Demand (MW)', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
            tick={{ fontSize: 10 }}
            width={45}
            className="sm:text-xs sm:w-[60px]"
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '12px'
            }}
            formatter={(value: number) => [`${value.toLocaleString()} MW`, '']}
            labelStyle={{ fontWeight: 'bold', marginBottom: '8px' }}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          
          {/* Reference line at current demand */}
          <ReferenceLine 
            y={currentDemand} 
            stroke="#9ca3af" 
            strokeDasharray="5 5"
            label={{ value: 'Current', position: 'right', fill: '#6b7280' }}
          />

          {/* Historical/Actual data */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#0066CC"
            strokeWidth={2}
            dot={false}
            name="Historical"
            connectNulls={false}
          />

          {/* Forecast data */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#f97316"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Forecast"
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div className="bg-blue-50 rounded-lg p-3">
          <p className="text-sm text-gray-600">Current Demand</p>
          <p className="text-xl font-bold text-blue-600">
            {Math.round(currentDemand).toLocaleString()} MW
          </p>
        </div>
        <div className="bg-green-50 rounded-lg p-3">
          <p className="text-sm text-gray-600">Forecast Range</p>
          <p className="text-xl font-bold text-green-600">48 hrs</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-3">
          <p className="text-sm text-gray-600">Data Points</p>
          <p className="text-xl font-bold text-purple-600">{data.length}</p>
        </div>
      </div>
    </div>
  );
}
