import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { MLPredictions } from '../types';
import { Badge } from './ui/Badge';

interface MLAnomalyChartProps {
  data: MLPredictions;
}

export function MLAnomalyChart({ data }: MLAnomalyChartProps) {
  // Safety check
  if (!data || !data.predictions || data.predictions.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <p className="text-gray-600">No ML prediction data available</p>
      </div>
    );
  }

  // Format predictions for line chart
  const chartData = data.predictions.map((pred, index) => {
    const date = new Date(pred.timestamp);
    return {
      index: index + 1,
      dateValue: date.getTime(), // Numeric timestamp for plotting
      value: pred.demand_mw || pred.predicted_demand || 0,
      isAnomaly: pred.is_anomaly,
      confidence: pred.confidence, // Already stored as percentage (0-100)
      timestamp: date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      }),
      dateLabel: date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    };
  });

  // Custom dot component - only show dots for anomalies
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (payload.isAnomaly) {
      return (
        <circle
          cx={cx}
          cy={cy}
          r={6}
          fill="#ef4444"
          stroke="#fff"
          strokeWidth={2}
        />
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-gray-800">ML Anomaly Detection</h3>
          <p className="text-sm text-gray-600 mt-1">
            Machine learning predictions with anomaly highlighting
          </p>
        </div>
        <Badge variant={data.anomalies_detected > 0 ? 'error' : 'success'}>
          {data.model_type}
        </Badge>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-600">Total Points</p>
          <p className="text-2xl font-bold text-blue-600">{data.total_points}</p>
        </div>
        <div className="bg-red-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-600">Anomalies</p>
          <p className="text-2xl font-bold text-red-600">{data.anomalies_detected}</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-600">Anomaly Rate</p>
          <p className="text-2xl font-bold text-purple-600">{data.anomaly_rate.toFixed(1)}%</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <p className="text-sm text-gray-600">Avg Confidence</p>
          <p className="text-2xl font-bold text-green-600">
            {(data.predictions.reduce((sum, p) => sum + p.confidence, 0) / data.predictions.length).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Line Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="dateValue" 
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: 'numeric'
              });
            }}
            label={{ value: 'Date & Time', position: 'insideBottom', offset: -10, style: { fontSize: 12 } }}
            tick={{ fontSize: 10, textAnchor: 'end' }}
            angle={-45}
            height={60}
          />
          <YAxis 
            dataKey="value"
            label={{ value: 'Predicted Demand (MW)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
            tick={{ fontSize: 11 }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '12px'
            }}
            formatter={(value: any, name: string) => {
              if (name === 'Demand') return [`${Number(value).toFixed(0)} MW`, 'Predicted Demand'];
              return [value, name];
            }}
            labelFormatter={(_label, payload) => {
              if (payload && payload.length > 0) {
                return payload[0].payload.timestamp;
              }
              return '';
            }}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '10px' }}
            payload={[
              { value: 'Demand Forecast', type: 'line', color: '#3b82f6' },
              { value: 'Detected Anomaly', type: 'circle', color: '#ef4444' },
            ]}
          />
          
          {/* Single continuous line with anomaly dots */}
          <Line 
            type="monotone"
            dataKey="value"
            name="Demand"
            stroke="#3b82f6"
            strokeWidth={2.5}
            dot={<CustomDot />}
            activeDot={{ r: 6 }}
            connectNulls={true}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Anomaly Alert */}
      {data.anomalies_detected > 0 && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-2xl mr-3">⚠️</span>
            <div>
              <p className="font-semibold text-red-800">
                {data.anomalies_detected} Anomal{data.anomalies_detected > 1 ? 'ies' : 'y'} Detected
              </p>
              <p className="text-sm text-red-600 mt-1">
                The ML model has identified unusual patterns in demand predictions. 
                This may indicate potential grid stress or unexpected load changes.
              </p>
            </div>
          </div>
        </div>
      )}

      {data.anomalies_detected === 0 && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-2xl mr-3">✅</span>
            <div>
              <p className="font-semibold text-green-800">
                No Anomalies Detected
              </p>
              <p className="text-sm text-green-600 mt-1">
                All predictions fall within normal operating parameters. Grid behavior is as expected.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
