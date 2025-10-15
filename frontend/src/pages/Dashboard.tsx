import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../api/client';
import { GridStatusCards } from '../components/GridStatusCards';
import { DemandForecastChart } from '../components/DemandForecastChart';
import { PriceChart } from '../components/PriceChart';
import { MLAnomalyChart } from '../components/MLAnomalyChart';
import { RecommendationCards } from '../components/RecommendationCards';

export function Dashboard() {
  const [refreshInterval, setRefreshInterval] = useState<number | false>(300000); // 5 minutes

  // Fetch grid status
  const { data: gridStatus, isLoading: gridLoading } = useQuery({
    queryKey: ['gridStatus'],
    queryFn: api.getGridStatus,
    refetchInterval: refreshInterval,
  });

  // Fetch demand forecast
  const { data: demandData, isLoading: demandLoading } = useQuery({
    queryKey: ['demandForecast'],
    queryFn: () => api.getDemandForecast(),
    refetchInterval: refreshInterval,
  });

  // Fetch price data
  const { data: priceData, isLoading: priceLoading } = useQuery({
    queryKey: ['prices'],
    queryFn: () => api.getPrices(6),
    refetchInterval: refreshInterval,
  });

  // Fetch ML predictions
  const { data: mlPredictions, isLoading: mlLoading } = useQuery({
    queryKey: ['mlPredictions'],
    queryFn: () => api.getMLPredictions(),
    refetchInterval: 600000, // 10 minutes
  });

  // Fetch recommendations
  const { data: recommendations, isLoading: recsLoading } = useQuery({
    queryKey: ['recommendations'],
    queryFn: () => api.getRecommendations(),
    refetchInterval: 600000, // 10 minutes
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-md border-b-4 border-ladwp-accent">
        <div className="container mx-auto px-6 py-6">
          <div>
            <h1 className="text-3xl font-bold text-ladwp-blue border-b-4 border-ladwp-accent pb-2 inline-block">
              ⚡ Los Angeles Department of Water & Power
            </h1>
            <h2 className="text-xl font-semibold text-ladwp-light-blue mt-2">
              Real-Time Grid Intelligence Dashboard
            </h2>
            <p className="text-gray-600 mt-2">
              Live CAISO grid monitoring with predictive analytics for operational excellence
            </p>
          </div>
          
          <div className="flex gap-4 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-gray-700">Connected to CAISO OASIS</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-700">Last Update:</span>
              <span className="font-semibold text-gray-900">
                {gridStatus?.timestamp ? new Date(gridStatus.timestamp).toLocaleTimeString() : '--:--:--'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-700">Refresh:</span>
              <select
                value={refreshInterval === false ? 'manual' : refreshInterval}
                onChange={(e) => {
                  const value = e.target.value;
                  setRefreshInterval(value === 'manual' ? false : parseInt(value));
                }}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="manual">Manual</option>
                <option value="30000">30 seconds</option>
                <option value="60000">1 minute</option>
                <option value="300000">5 minutes</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 space-y-12">
        {/* Section 1: Current Grid Status */}
        <GridStatusCards data={gridStatus} isLoading={gridLoading} />

        {/* Section 2: Demand Forecast */}
        <section>
          <h2 className="text-2xl font-bold text-ladwp-blue mb-4">
            📊 System Demand Forecast - Next 48 Hours
          </h2>
          {demandLoading ? (
            <div className="bg-white rounded-xl p-8 text-center">
              <div className="animate-pulse">Loading demand forecast...</div>
            </div>
          ) : demandData && demandData.length > 0 ? (
            <DemandForecastChart data={demandData} />
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
              <p className="text-yellow-800">⚠️ Unable to fetch demand forecast data</p>
            </div>
          )}
        </section>

        {/* Section 2.5: ML Anomaly Detection */}
        <section>
          <h2 className="text-2xl font-bold text-ladwp-blue mb-4">
            🤖 AI-Powered Forecast Analysis
          </h2>
          {mlLoading ? (
            <div className="bg-white rounded-xl p-8 text-center">
              <div className="animate-pulse">Loading ML predictions...</div>
            </div>
          ) : mlPredictions ? (
            <MLAnomalyChart data={mlPredictions} />
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <p className="text-blue-800">ℹ️ ML predictions not available</p>
            </div>
          )}
        </section>

        {/* Section 2.6: Smart Recommendations */}
        <section>
          <h2 className="text-2xl font-bold text-ladwp-blue mb-4">
            💡 Smart Recommendations
          </h2>
          {recsLoading ? (
            <div className="bg-white rounded-xl p-8 text-center">
              <div className="animate-pulse">Loading recommendations...</div>
            </div>
          ) : recommendations && recommendations.recommendations ? (
            <RecommendationCards data={recommendations} />
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
              <p className="text-green-800">✅ No recommendations - system operating normally</p>
            </div>
          )}
        </section>

        {/* Section 3: Price Analysis */}
        <section>
          <h2 className="text-2xl font-bold text-ladwp-blue mb-4">
            💰 Real-Time Energy Prices
          </h2>
          {priceLoading ? (
            <div className="bg-white rounded-xl p-8 text-center">
              <div className="animate-pulse">Loading price data...</div>
            </div>
          ) : priceData && priceData.length > 0 ? (
            <PriceChart data={priceData} />
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
              <p className="text-yellow-800">⚠️ Unable to fetch price data</p>
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="container mx-auto px-6 py-6 text-center text-gray-600 text-sm">
          <p>
            <strong>Data Source:</strong> CAISO OASIS API (Real-time) | 
            <strong className="ml-2">Updates:</strong> Live 5-minute interval data | 
            <strong className="ml-2">Coverage:</strong> LADWP service territory
          </p>
          <p className="mt-2">
            LADWP Grid Intelligence Dashboard v2.0 - React + TypeScript + FastAPI
          </p>
        </div>
      </footer>
    </div>
  );
}
