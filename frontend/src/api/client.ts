import axios from 'axios';
import type {
  GridStatus,
  DemandDataPoint,
  PriceDataPoint,
  MLPredictions,
  Recommendations,
  APIResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('[API Error]', error);
    if (error.response) {
      // Server responded with error status
      console.error('Response error:', error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('No response received');
    } else {
      // Request setup error
      console.error('Request error:', error.message);
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Grid Status
  getGridStatus: async (): Promise<GridStatus> => {
    const { data } = await apiClient.get<APIResponse<GridStatus>>('/api/grid-status');
    return data.data;
  },

  // Demand Forecast
  getDemandForecast: async (date?: string): Promise<DemandDataPoint[]> => {
    const params = date ? { date } : {};
    const { data } = await apiClient.get<APIResponse<DemandDataPoint[]>>(
      '/api/demand-forecast',
      { params }
    );
    return data.data;
  },

  // Prices
  getPrices: async (hoursBack: number = 6): Promise<PriceDataPoint[]> => {
    const { data } = await apiClient.get<APIResponse<PriceDataPoint[]>>('/api/prices', {
      params: { hours_back: hoursBack },
    });
    return data.data;
  },

  // ML Predictions
  getMLPredictions: async (month?: string): Promise<MLPredictions | null> => {
    const params = month ? { month } : {};
    const { data } = await apiClient.get<APIResponse<MLPredictions>>(
      '/api/ml-predictions',
      { params }
    );
    return data.success ? data.data : null;
  },

  // Recommendations
  getRecommendations: async (month?: string): Promise<Recommendations | null> => {
    const params = month ? { month } : {};
    const { data} = await apiClient.get<APIResponse<Recommendations>>(
      '/api/recommendations',
      { params }
    );
    return data.success ? data.data : null;
  },

  // Health Check
  healthCheck: async (): Promise<boolean> => {
    try {
      await apiClient.get('/api/health');
      return true;
    } catch {
      return false;
    }
  },
};

export default apiClient;
