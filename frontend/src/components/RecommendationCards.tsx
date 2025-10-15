import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, AlertTriangle, Info } from 'lucide-react';
import type { Recommendations } from '../types';
import { Badge } from './ui/Badge';

interface RecommendationCardsProps {
  data: Recommendations;
}

export function RecommendationCards({ data }: RecommendationCardsProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Safety check
  if (!data || !data.recommendations) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <p className="text-gray-600">No recommendations available</p>
      </div>
    );
  }

  const toggleExpanded = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getPriorityColor = (priority?: string) => {
    if (!priority) return 'slate';
    switch (priority.toLowerCase()) {
      case 'high':
        return 'red';
      case 'medium':
        return 'orange';
      case 'low':
        return 'blue';
      default:
        return 'slate';
    }
  };

  const getPriorityIcon = (priority?: string) => {
    if (!priority) return '⚪';
    switch (priority.toLowerCase()) {
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

  // Sort recommendations by priority
  const sortedRecommendations = [...data.recommendations].sort((a, b) => {
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    const aPriority = priorityOrder[(a.recommendation?.priority?.toLowerCase() || 'low') as keyof typeof priorityOrder] ?? 3;
    const bPriority = priorityOrder[(b.recommendation?.priority?.toLowerCase() || 'low') as keyof typeof priorityOrder] ?? 3;
    return aPriority - bPriority;
  });

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-lg p-4 text-center">
          <p className="text-sm text-gray-600">Total Anomalies</p>
          <p className="text-3xl font-bold text-gray-800">{data.total_anomalies}</p>
        </div>
        <div className="bg-red-50 rounded-xl shadow-lg p-4 text-center border-2 border-red-200">
          <p className="text-sm text-gray-600">High Priority</p>
          <p className="text-3xl font-bold text-red-600">{data.high_priority}</p>
        </div>
        <div className="bg-orange-50 rounded-xl shadow-lg p-4 text-center border-2 border-orange-200">
          <p className="text-sm text-gray-600">Medium Priority</p>
          <p className="text-3xl font-bold text-orange-600">{data.medium_priority}</p>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-3">
        {sortedRecommendations.length === 0 ? (
          <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6 text-center">
            <span className="text-4xl mb-2 block">✅</span>
            <p className="text-lg font-semibold text-green-800">No Recommendations</p>
            <p className="text-sm text-green-600 mt-1">
              System is operating normally with no anomalies detected
            </p>
          </div>
        ) : (
          sortedRecommendations.map((rec, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200"
            >
              {/* Card Header */}
              <button
                onClick={() => toggleExpanded(index)}
                className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 text-left">
                  <span className="text-2xl">{getPriorityIcon(rec.recommendation.priority)}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-gray-800">{rec.recommendation.title}</h4>
                      <Badge variant={getPriorityColor(rec.recommendation.priority) as any}>
                        {rec.recommendation.priority}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-1">
                      {rec.anomaly ? `${rec.anomaly.time_str} - ${rec.anomaly.demand_mw.toFixed(0)} MW` : 'General Recommendation'}
                    </p>
                  </div>
                </div>
                <div className="ml-4">
                  {expandedId === index ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </button>

              {/* Expanded Content */}
              <AnimatePresence>
                {expandedId === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="border-t border-gray-200 bg-gray-50"
                  >
                    <div className="p-4 space-y-4">
                      {/* Why / Description */}
                      <div>
                        <h5 className="text-sm font-semibold text-gray-700 mb-2">Analysis</h5>
                        <div className="text-sm text-gray-700 whitespace-pre-line bg-white rounded-lg p-3 border border-gray-200">
                          {rec.recommendation.why}
                        </div>
                      </div>

                      {/* Anomaly Details */}
                      {rec.analysis && (
                        <div>
                          <h5 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                            <Info className="w-4 h-4" />
                            Anomaly Details
                          </h5>
                          <div className="bg-white rounded-lg p-3 border border-gray-200 space-y-2">
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              {rec.analysis.anomaly_type && (
                                <div>
                                  <span className="text-gray-600">Type:</span>
                                  <span className="ml-2 font-medium">{rec.analysis.anomaly_type.replace(/_/g, ' ')}</span>
                                </div>
                              )}
                              {rec.analysis.deviation_pct !== undefined && (
                                <div>
                                  <span className="text-gray-600">Deviation:</span>
                                  <span className="ml-2 font-medium">{rec.analysis.deviation_pct.toFixed(1)}%</span>
                                </div>
                              )}
                              {rec.analysis.expected_demand !== undefined && (
                                <div>
                                  <span className="text-gray-600">Expected:</span>
                                  <span className="ml-2 font-medium">{rec.analysis.expected_demand.toFixed(0)} MW</span>
                                </div>
                              )}
                              {rec.analysis.actual_demand !== undefined && (
                                <div>
                                  <span className="text-gray-600">Actual:</span>
                                  <span className="ml-2 font-medium">{rec.analysis.actual_demand.toFixed(0)} MW</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      {rec.recommendation.actions && rec.recommendation.actions.length > 0 && (
                        <div>
                          <h5 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4" />
                            Recommended Actions
                          </h5>
                          <ul className="space-y-2">
                            {rec.recommendation.actions.map((action, i) => (
                              <li key={i} className="text-sm bg-white rounded-lg p-3 border border-gray-200">
                                <div className="flex items-start gap-2">
                                  <span className="text-xl">{action.icon}</span>
                                  <div className="flex-1">
                                    <p className="font-medium text-gray-800">{action.action}</p>
                                    <p className="text-gray-600 text-xs mt-1">{action.details}</p>
                                    {action.timeframe && (
                                      <p className="text-xs text-ladwp-blue mt-1">⏱️ {action.timeframe}</p>
                                    )}
                                  </div>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Timestamp & Impact */}
                      <div className="pt-2 border-t border-gray-200 space-y-2">
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {rec.anomaly && (
                            <>
                              <div>
                                <span className="text-gray-500">Detected:</span>
                                <span className="ml-1 font-medium">{rec.anomaly.date_str} at {rec.anomaly.time_str}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Severity:</span>
                                <span className="ml-1 font-medium capitalize">{rec.anomaly.severity}</span>
                              </div>
                            </>
                          )}
                          {rec.recommendation.impact && (
                            <>
                              <div>
                                <span className="text-gray-500">Financial Impact:</span>
                                <span className="ml-1 font-medium">{rec.recommendation.impact.financial}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Reliability Risk:</span>
                                <span className="ml-1 font-medium">{rec.recommendation.impact.reliability_risk}</span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
