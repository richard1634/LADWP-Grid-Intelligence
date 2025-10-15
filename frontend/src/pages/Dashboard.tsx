import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../api/client';
import { GridStatusCards } from '../components/GridStatusCards';
import { DemandForecastChart } from '../components/DemandForecastChart';
import { PriceChart } from '../components/PriceChart';
import { MLAnomalyChart } from '../components/MLAnomalyChart';
import { AnomalyRecommendations } from '../components/AnomalyRecommendations';
import { DemoModeToggle } from '../components/DemoModeToggle';

// Tab type definition
type TabType = 'demand' | 'price';

// Sample anomalies for portfolio demonstration
const generateSampleAnomalies = () => {
  const now = new Date();
  return [
    {
      timestamp: new Date(now.getTime() + 2 * 60 * 60 * 1000).toISOString(),
      demand_mw: 7200,
      predicted_demand: 3200,
      confidence: 89.5,
      severity: 'critical',
      is_anomaly: true,
      time_str: new Date(now.getTime() + 2 * 60 * 60 * 1000).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      date_str: new Date(now.getTime() + 2 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    },
    {
      timestamp: new Date(now.getTime() + 5 * 60 * 60 * 1000).toISOString(),
      demand_mw: 1850,
      predicted_demand: 3400,
      confidence: 76.2,
      severity: 'high',
      is_anomaly: true,
      time_str: new Date(now.getTime() + 5 * 60 * 60 * 1000).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      date_str: new Date(now.getTime() + 5 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    },
    {
      timestamp: new Date(now.getTime() + 8 * 60 * 60 * 1000).toISOString(),
      demand_mw: 4200,
      predicted_demand: 2900,
      confidence: 68.3,
      severity: 'medium',
      is_anomaly: true,
      time_str: new Date(now.getTime() + 8 * 60 * 60 * 1000).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      date_str: new Date(now.getTime() + 8 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    }
  ];
};

export function Dashboard() {
  const [refreshInterval, setRefreshInterval] = useState<number | false>(300000); // 5 minutes
  const [demoMode, setDemoMode] = useState(false);
  const [isGeneratingSamples, setIsGeneratingSamples] = useState(false);
  const [sampleAnomalies] = useState(generateSampleAnomalies());
  const [activeTab, setActiveTab] = useState<TabType>('demand');

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

  const handleGenerateSamples = async () => {
    setIsGeneratingSamples(true);
    // Simulate generation delay for UX
    await new Promise(resolve => setTimeout(resolve, 1000));
    setDemoMode(true);
    setIsGeneratingSamples(false);
  };

  const handleClearSamples = () => {
    setDemoMode(false);
  };

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

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="container mx-auto px-6">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('demand')}
              className={`py-4 px-2 border-b-2 font-semibold text-sm transition-colors ${
                activeTab === 'demand'
                  ? 'border-ladwp-blue text-ladwp-blue'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ⚡ Demand Forecast & AI Analysis
            </button>
            <button
              onClick={() => setActiveTab('price')}
              className={`py-4 px-2 border-b-2 font-semibold text-sm transition-colors ${
                activeTab === 'price'
                  ? 'border-ladwp-blue text-ladwp-blue'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              💰 Price Analysis
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 space-y-12">
        {/* Data Source Information Banner */}
        <section className="bg-blue-50 border-2 border-blue-200 rounded-xl shadow-lg">
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className="text-4xl">📍</div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-ladwp-blue mb-2">
                  Grid Coverage & Data Sources
                </h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="font-semibold text-gray-800 mb-1">🗺️ LADWP Service Territory</p>
                    <ul className="text-gray-700 space-y-1 ml-4">
                      <li>• <strong>Location:</strong> Los Angeles, California</li>
                      <li>• <strong>Coverage:</strong> 465 square miles</li>
                      <li>• <strong>Customers:</strong> 1.5M+ electric customers</li>
                      <li>• <strong>LADWP Peak Load:</strong> ~6,200 MW</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-800 mb-1">📊 Real-Time Data Sources</p>
                    <ul className="text-gray-700 space-y-1 ml-4">
                      <li>• <strong>Demand Data:</strong> CAISO OASIS - LADWP TAC Area Load</li>
                      <li>• <strong>Price Data:</strong> CAISO LMP - LADWP nodes (DLAP_LADWP) averaged</li>
                      <li>• <strong>Update Frequency:</strong> 5-minute real-time intervals</li>
                      <li>• <strong>ML Predictions:</strong> LADWP historical patterns (month-specific)</li>
                    </ul>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-blue-200">
                  <p className="text-xs text-gray-600 mb-2">
                    <strong>✅ Data Verification:</strong> All demand forecasts are LADWP-specific, filtered from CAISO's TAC area data (typical range: 2,000-6,200 MW). 
                    Price data is averaged across LADWP pricing nodes (DLAP_LADWP) for representative energy costs. 
                    ML predictions use historical LADWP patterns specific to October 2025 operating conditions.
                  </p>
                  <p className="text-xs text-gray-500 italic">
                    <strong>Why CAISO has LADWP data:</strong> Although LADWP operates independently, it interconnects with the CAISO grid for reliability and market participation. 
                    CAISO tracks all interconnected loads for grid coordination, making this data available via their public OASIS API for transparency and operational planning.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Demand Forecast & AI Analysis Tab */}
        {activeTab === 'demand' && (
          <>
            {/* Section 1: Current Grid Status */}
            <GridStatusCards data={gridStatus} isLoading={gridLoading} />

            {/* Section 2: Demand Forecast */}
            <section>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-ladwp-blue">
              📊 LADWP Demand Forecast - Last 24 Hours & Next 30 Hours
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              LADWP-specific load data from CAISO TAC area (typical range: 2,000-6,200 MW). 
              Historical data (blue) shows last 24 hours of actual measured demand, forecast (orange) shows CAISO Day-Ahead Market predictions up to 30 hours ahead.
            </p>
          </div>
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

        {/* Section 2.5: AI-Powered Analysis (Integrated) */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-ladwp-blue">
              🤖 AI-Powered Grid Intelligence
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Machine learning model trained on historical LADWP demand patterns using <strong>October 2025</strong> month-specific data. 
              Detects unusual demand anomalies and generates intelligent recommendations using GPT-3.5 for proactive grid management.
            </p>
          </div>

          {/* Demo Mode Toggle */}
          {!mlLoading && mlPredictions && mlPredictions.predictions && (
            (() => {
              const realAnomalies = mlPredictions.predictions.filter(p => 
                p.is_anomaly || p.severity !== 'normal'
              );
              
              // Show demo toggle only when there are no real anomalies
              return realAnomalies.length === 0 ? (
                <DemoModeToggle
                  onGenerateSamples={handleGenerateSamples}
                  onClearSamples={handleClearSamples}
                  hasSamples={demoMode}
                  isGenerating={isGeneratingSamples}
                />
              ) : null;
            })()
          )}

          {/* Two-Column Layout: Chart + Recommendations */}
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Left Column: ML Anomaly Chart */}
            <div>
              <div className="mb-3">
                <h3 className="text-lg font-semibold text-gray-800">📊 Anomaly Detection</h3>
                <p className="text-xs text-gray-600">ML forecast analysis with anomaly highlighting</p>
              </div>
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
            </div>

            {/* Right Column: AI Recommendations */}
            <div>
              <div className="mb-3">
                <h3 className="text-lg font-semibold text-gray-800">💡 AI Recommendations</h3>
                <p className="text-xs text-gray-600">Intelligent insights and actionable guidance</p>
              </div>
              {mlLoading ? (
                <div className="bg-white rounded-xl p-8 text-center">
                  <div className="animate-pulse">Loading anomalies...</div>
                </div>
              ) : mlPredictions && mlPredictions.predictions ? (
                (() => {
                  // Extract anomalies from predictions array
                  const realAnomalies = mlPredictions.predictions.filter(p => 
                    p.is_anomaly || p.severity !== 'normal'
                  );
                  
                  // Use demo samples if demo mode is active and no real anomalies
                  const displayAnomalies = (demoMode && realAnomalies.length === 0) 
                    ? sampleAnomalies 
                    : realAnomalies;
                  
                  return displayAnomalies.length > 0 ? (
                    <AnomalyRecommendations anomalies={displayAnomalies as any} />
                  ) : (
                    <div className="bg-green-50 border-2 border-green-200 rounded-xl p-8 text-center">
                      <span className="text-5xl mb-3 block">✅</span>
                      <p className="text-xl font-bold text-green-800 mb-2">No Anomalies Detected</p>
                      <p className="text-sm text-green-600">
                        System is operating normally. Click "Generate Sample Scenarios" above to create fake demo anomalies for showcasing AI capabilities.
                      </p>
                    </div>
                  );
                })()
              ) : (
                <div className="bg-green-50 border-2 border-green-200 rounded-xl p-8 text-center">
                  <span className="text-5xl mb-3 block">✅</span>
                  <p className="text-xl font-bold text-green-800 mb-2">No Anomalies Detected</p>
                  <p className="text-sm text-green-600">
                    System is operating normally. Click "Generate Sample Scenarios" above to create fake demo anomalies for showcasing AI capabilities.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>
          </>
        )}

        {/* Price Analysis Tab */}
        {activeTab === 'price' && (
          <>
            {/* Section 3: Price Analysis */}
            <section>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-ladwp-blue">
              💰 Real-Time Energy Prices
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              CAISO Locational Marginal Pricing (LMP) for LADWP grid nodes. 
              Prices averaged across all LADWP nodes and updated every 5 minutes. Red dots indicate price spikes (&gt;2.5σ above average).
            </p>
          </div>
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
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="container mx-auto px-6 py-6">
          <div className="grid md:grid-cols-3 gap-6 text-sm text-gray-600">
            <div>
              <h4 className="font-semibold text-ladwp-blue mb-2">📡 Data Sources</h4>
              <ul className="space-y-1">
                <li>• <strong>Grid Operator:</strong> CAISO (California ISO)</li>
                <li>• <strong>API:</strong> OASIS Real-Time Market Data</li>
                <li>• <strong>Load Data:</strong> LADWP TAC Area (SLD_FCST filtered)</li>
                <li>• <strong>Price Nodes:</strong> LADWP DLAP (averaged)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-ladwp-blue mb-2">🗺️ Service Area</h4>
              <ul className="space-y-1">
                <li>• <strong>Location:</strong> Los Angeles, California</li>
                <li>• <strong>Territory:</strong> 465 sq mi (1,204 km²)</li>
                <li>• <strong>Customers:</strong> 1.5M+ electric customers</li>
                <li>• <strong>Typical Load:</strong> 2,000-4,000 MW (off-peak) | ~6,200 MW (peak)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-ladwp-blue mb-2">⚙️ Technical Details</h4>
              <ul className="space-y-1">
                <li>• <strong>Update Frequency:</strong> 5-minute intervals</li>
                <li>• <strong>Forecast Horizon:</strong> 30 hours ahead (CAISO DAM)</li>
                <li>• <strong>Historical Window:</strong> Last 24 hours</li>
                <li>• <strong>ML Model:</strong> Month-specific (October 2025)</li>
              </ul>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-gray-200 text-center text-xs text-gray-500">
            <p>
              LADWP Grid Intelligence Dashboard v2.0 | React + TypeScript + FastAPI | 
              Real-time data from CAISO OASIS API
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
