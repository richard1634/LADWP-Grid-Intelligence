import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, AlertTriangle, Sparkles, Loader2 } from 'lucide-react';
import { Badge } from './ui/Badge';

interface Anomaly {
  timestamp: string;
  demand_mw: number;
  predicted_demand: number;
  confidence: number;
  severity: string;
  time_str?: string;
  date_str?: string;
}

interface AIRecommendation {
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  title: string;
  why: string;
  actions: Array<{
    icon: string;
    action: string;
    details: string;
    timeframe?: string;
  }>;
  impact?: {
    financial: string;
    reliability_risk: string;
  };
}

interface AnomalyRecommendationCardProps {
  anomaly: Anomaly;
  index: number;
  onGenerateRecommendation: (anomaly: Anomaly) => Promise<AIRecommendation>;
}

export function AnomalyRecommendationCard({ 
  anomaly, 
  index,
  onGenerateRecommendation 
}: AnomalyRecommendationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<AIRecommendation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'red';
      case 'high':
        return 'orange';
      case 'medium':
        return 'yellow';
      case 'low':
        return 'blue';
      default:
        return 'slate';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return '🚨';
      case 'high':
        return '🔴';
      case 'medium':
        return '🟡';
      case 'low':
        return '🔵';
      default:
        return '⚪';
    }
  };

  const formatTime = () => {
    if (anomaly.time_str && anomaly.date_str) {
      return `${anomaly.date_str} at ${anomaly.time_str}`;
    }
    try {
      const date = new Date(anomaly.timestamp);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return anomaly.timestamp;
    }
  };

  const handleGenerateRecommendation = async () => {
    if (recommendation) {
      setExpanded(!expanded);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const rec = await onGenerateRecommendation(anomaly);
      setRecommendation(rec);
      setExpanded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate recommendation');
    } finally {
      setLoading(false);
    }
  };

  // Calculate deviation if predicted_demand is available
  const hasPrediction = anomaly.predicted_demand !== undefined && anomaly.predicted_demand !== null;
  const deviation = hasPrediction 
    ? ((anomaly.demand_mw - anomaly.predicted_demand!) / anomaly.predicted_demand! * 100)
    : 0;
  const isSpike = deviation > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white rounded-xl shadow-lg overflow-hidden border-2 border-gray-200 hover:border-ladwp-blue transition-colors"
    >
      {/* Card Header */}
      <div className="p-4 bg-gradient-to-r from-gray-50 to-white">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            <span className="text-3xl mt-1">{getSeverityIcon(anomaly.severity)}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-bold text-gray-800 text-lg">
                  Anomaly Detected: {anomaly.demand_mw.toFixed(0)} MW
                </h4>
                <Badge variant={getSeverityColor(anomaly.severity) as any}>
                  {anomaly.severity}
                </Badge>
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                <p>📅 {formatTime()}</p>
                {hasPrediction && (
                  <>
                    <p>📊 Expected: {anomaly.predicted_demand!.toFixed(0)} MW</p>
                    <p className={isSpike ? 'text-red-600 font-semibold' : 'text-blue-600 font-semibold'}>
                      {isSpike ? '⬆️' : '⬇️'} Deviation: {Math.abs(deviation).toFixed(1)}% 
                      ({isSpike ? 'above' : 'below'} predicted)
                    </p>
                  </>
                )}
                {!hasPrediction && (
                  <p>🤖 Unusual pattern detected in CAISO forecast</p>
                )}
                <p>🎯 Confidence: {anomaly.confidence.toFixed(1)}%</p>
              </div>
            </div>
          </div>

          {/* AI Analysis Button */}
          <button
            data-anomaly-generate-btn
            onClick={handleGenerateRecommendation}
            disabled={loading}
            className={`
              px-4 py-2 rounded-lg font-semibold text-sm transition-all transform
              ${loading 
                ? 'bg-gray-300 text-gray-600 cursor-wait' 
                : recommendation
                  ? 'bg-green-500 hover:bg-green-600 text-white hover:scale-105'
                  : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white hover:scale-105 shadow-lg'
              }
            `}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </span>
            ) : recommendation ? (
              <span className="flex items-center gap-2">
                {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                {expanded ? 'Hide' : 'View'} AI Analysis
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Get AI Analysis
              </span>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* AI Recommendation Details */}
      <AnimatePresence>
        {expanded && recommendation && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t-2 border-purple-200 bg-gradient-to-br from-purple-50 to-blue-50"
          >
            <div className="p-6 space-y-4">
              {/* AI Badge */}
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-semibold text-purple-800 bg-purple-100 px-3 py-1 rounded-full">
                  🤖 AI-Powered Analysis
                </span>
              </div>

              {/* Title */}
              <div>
                <h5 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                  {recommendation.title}
                </h5>
              </div>

              {/* Analysis */}
              <div>
                <h5 className="text-sm font-semibold text-gray-700 mb-2">💡 Analysis</h5>
                <div className="text-sm text-gray-700 whitespace-pre-line bg-white rounded-lg p-4 border border-purple-200 shadow-sm">
                  {recommendation.why}
                </div>
              </div>

              {/* Actions */}
              {recommendation.actions && recommendation.actions.length > 0 && (
                <div>
                  <h5 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-orange-500" />
                    Recommended Actions
                  </h5>
                  <ul className="space-y-3">
                    {recommendation.actions.map((action, i) => (
                      <li key={i} className="bg-white rounded-lg p-4 border border-purple-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-start gap-3">
                          <span className="text-2xl">{action.icon}</span>
                          <div className="flex-1">
                            <p className="font-semibold text-gray-800 mb-1">{action.action}</p>
                            <p className="text-gray-600 text-sm mb-2">{action.details}</p>
                            {action.timeframe && (
                              <p className="text-xs text-purple-700 font-medium bg-purple-100 inline-block px-2 py-1 rounded">
                                ⏱️ {action.timeframe}
                              </p>
                            )}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Impact */}
              {recommendation.impact && (
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-purple-200">
                  <div className="bg-white rounded-lg p-3 border border-purple-200">
                    <span className="text-xs text-gray-600 block mb-1">Financial Impact</span>
                    <span className="text-sm font-semibold text-gray-800">{recommendation.impact.financial}</span>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-purple-200">
                    <span className="text-xs text-gray-600 block mb-1">Reliability Risk</span>
                    <span className="text-sm font-semibold text-gray-800">{recommendation.impact.reliability_risk}</span>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
