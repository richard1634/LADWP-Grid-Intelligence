import { useState } from 'react';
import { AnomalyRecommendationCard } from './AnomalyRecommendationCard';
import * as api from '../api/client';

interface Anomaly {
  timestamp: string;
  demand_mw: number;
  predicted_demand: number;
  confidence: number;
  severity: string;
  time_str?: string;
  date_str?: string;
}

interface AnomalyRecommendationsProps {
  anomalies: Anomaly[];
}

export function AnomalyRecommendations({ anomalies }: AnomalyRecommendationsProps) {
  const [generatingAll, setGeneratingAll] = useState(false);
  const [generatedCount, setGeneratedCount] = useState(0);

  const handleGenerateRecommendation = async (anomaly: Anomaly) => {
    // Call API to generate recommendation for this specific anomaly
    try {
      const response = await api.generateAnomalyRecommendation(anomaly);
      return response;
    } catch (error) {
      console.error('Failed to generate recommendation:', error);
      throw new Error('Failed to generate AI recommendation. Please try again.');
    }
  };

  const handleGenerateAll = async () => {
    setGeneratingAll(true);
    setGeneratedCount(0);

    // Trigger generation for all anomalies sequentially
    for (let i = 0; i < anomalies.length; i++) {
      try {
        // Click the button for this anomaly card
        const buttons = document.querySelectorAll('[data-anomaly-generate-btn]');
        if (buttons[i]) {
          (buttons[i] as HTMLButtonElement).click();
          setGeneratedCount(i + 1);
          // Wait a bit between requests to avoid overwhelming the API
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      } catch (error) {
        console.error(`Failed to generate recommendation for anomaly ${i}:`, error);
      }
    }

    setGeneratingAll(false);
  };

  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="bg-green-50 border-2 border-green-200 rounded-xl p-8 text-center">
        <span className="text-5xl mb-3 block">✅</span>
        <p className="text-xl font-bold text-green-800 mb-2">No Anomalies Detected</p>
        <p className="text-sm text-green-600">
          System is operating normally. No recommendations needed at this time.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border-2 border-purple-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold text-gray-800 mb-2">
              🔍 Detected Anomalies
            </h3>
            <p className="text-sm text-gray-600">
              Click "Get AI Analysis" on any anomaly to generate intelligent recommendations powered by GPT-3.5
            </p>
          </div>
          {anomalies.length > 1 && (
            <button
              onClick={handleGenerateAll}
              disabled={generatingAll}
              className={`
                px-6 py-3 rounded-lg font-semibold transition-all transform
                ${generatingAll
                  ? 'bg-gray-300 text-gray-600 cursor-wait'
                  : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white hover:scale-105 shadow-lg'
                }
              `}
            >
              {generatingAll 
                ? `Generating ${generatedCount}/${anomalies.length}...` 
                : '🤖 Analyze All Anomalies'
              }
            </button>
          )}
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <p className="text-sm text-gray-600 mb-1">Total Anomalies</p>
            <p className="text-3xl font-bold text-gray-800">{anomalies.length}</p>
          </div>
          <div className="bg-red-50 rounded-lg p-4 text-center border border-red-200">
            <p className="text-sm text-gray-600 mb-1">Critical</p>
            <p className="text-3xl font-bold text-red-600">
              {anomalies.filter(a => a.severity.toLowerCase() === 'critical').length}
            </p>
          </div>
          <div className="bg-orange-50 rounded-lg p-4 text-center border border-orange-200">
            <p className="text-sm text-gray-600 mb-1">High</p>
            <p className="text-3xl font-bold text-orange-600">
              {anomalies.filter(a => a.severity.toLowerCase() === 'high').length}
            </p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 text-center border border-yellow-200">
            <p className="text-sm text-gray-600 mb-1">Medium/Low</p>
            <p className="text-3xl font-bold text-yellow-600">
              {anomalies.filter(a => ['medium', 'low'].includes(a.severity.toLowerCase())).length}
            </p>
          </div>
        </div>
      </div>

      {/* Anomaly Cards */}
      <div className="space-y-4">
        {anomalies
          .sort((a, b) => {
            // Sort by severity: critical > high > medium > low
            const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
            const aSeverity = severityOrder[a.severity.toLowerCase() as keyof typeof severityOrder] ?? 4;
            const bSeverity = severityOrder[b.severity.toLowerCase() as keyof typeof severityOrder] ?? 4;
            if (aSeverity !== bSeverity) return aSeverity - bSeverity;
            // Then by confidence (descending)
            return b.confidence - a.confidence;
          })
          .map((anomaly, index) => (
            <AnomalyRecommendationCard
              key={`${anomaly.timestamp}-${index}`}
              anomaly={anomaly}
              index={index}
              onGenerateRecommendation={handleGenerateRecommendation}
            />
          ))
        }
      </div>
    </div>
  );
}
