export interface GridStatus {
  demand_mw: number;
  demand_trend: number | string;
  avg_price_per_mwh: number;
  price_delta: number;
  stress: {
    level: 'Normal' | 'Moderate' | 'High' | 'Critical';
    score: number;
    factors: string[];
  };
  timestamp: string;
}

export interface DemandDataPoint {
  timestamp: string;
  demand_mw: number;
  area?: string;
  is_forecast?: boolean;
}

export interface PriceDataPoint {
  timestamp: string;
  price: number;
  congestion: number;
  energy: number;
  loss: number;
  node: string;
  is_spike?: boolean;
}

export interface MLPrediction {
  timestamp: string;
  demand_mw?: number;
  predicted_demand?: number; // Alternative field name
  is_anomaly: boolean;
  confidence: number;
  severity: 'low' | 'medium' | 'high' | 'critical' | 'normal';
  anomaly_score?: number;
}

export interface MLPredictions {
  total_points: number;
  anomalies_detected: number;
  anomaly_rate: number;
  model_type: string;
  month: string;
  generated_at: string;
  predictions: MLPrediction[];
}

export interface RecommendationAction {
  icon: string;
  action: string;
  details: string;
  estimated_savings?: string;
  timeframe?: string;
}

export interface Recommendation {
  anomaly: {
    timestamp: string;
    demand_mw: number;
    severity: string;
    confidence: number;
    time_str: string;
    date_str: string;
  } | null;
  analysis?: {
    anomaly_type: string;
    primary_diagnosis: string;
    root_causes: string[];
    contributing_factors: string[];
    deviation_pct: number;
    expected_demand: number;
    actual_demand: number;
    direction: string;
    current_price: number;
  };
  recommendation: {
    priority: 'LOW' | 'MEDIUM' | 'HIGH';
    urgency: string;
    title: string;
    why: string;
    actions: RecommendationAction[];
    impact?: {
      financial: string;
      financial_type: string;
      reliability_risk: string;
      magnitude_mw: number;
      duration_estimate: string;
    };
    confidence?: number;
    time_sensitive?: boolean;
  };
}

export interface Recommendations {
  total_anomalies: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
  month?: string;
  generated_at?: string;
  recommendations: Recommendation[];
}

export interface APIResponse<T> {
  success: boolean;
  data: T;
  count?: number;
  message?: string;
  error?: string;
}
