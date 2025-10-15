"""
Generate Predictions Using Month-Specific Models

Creates prediction files for each month's model so the dashboard
can auto-select the appropriate predictions.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import pickle
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from caiso_api_client import CAISOClient
from models.anomaly_detector import AnomalyDetector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MonthlyPredictor:
    """Generate predictions for all monthly models"""
    
    def __init__(self):
        self.caiso_client = CAISOClient()
        self.detector = AnomalyDetector()
        # Use parent.parent to get to root directory from scripts/
        root_dir = Path(__file__).parent.parent
        self.models_dir = root_dir / "models" / "trained_models"
        self.predictions_dir = root_dir / "models" / "predictions"
        self.predictions_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = root_dir / "data" / "historical_data" / "ladwp_grid_data.db"
        
        self.months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
    
    def load_model(self, month_name):
        """Load model and scaler for a specific month"""
        model_path = self.models_dir / f"{month_name}_demand_anomaly_detector.pkl"
        scaler_path = self.models_dir / f"{month_name}_demand_scaler.pkl"
        info_path = self.models_dir / f"{month_name}_model_info.json"
        
        if not model_path.exists():
            return None, None, None
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        with open(info_path, 'r') as f:
            model_info = json.load(f)
        
        return model, scaler, model_info
    
    def get_forecast(self, hours_ahead=48):
        """Get CAISO forecast"""
        logger.info(f"📡 Fetching CAISO forecast for next {hours_ahead} hours...")
        
        df = self.caiso_client.get_system_demand(date=None, hours_ahead=hours_ahead)
        
        if df.empty:
            return pd.DataFrame()
        
        # Filter and standardize
        if 'TAC_AREA_NAME' in df.columns:
            df = df[df['TAC_AREA_NAME'] == 'LADWP'].copy()
        
        if 'MW' in df.columns:
            df['demand_mw'] = pd.to_numeric(df['MW'], errors='coerce')
        
        # Get hourly averages
        df = df.groupby(df['timestamp'].dt.floor('h')).agg({
            'demand_mw': 'mean',
            'timestamp': 'first'
        }).reset_index(drop=True)
        
        # Filter for future only
        now = datetime.now(df['timestamp'].dt.tz)
        df = df[df['timestamp'] > now].copy()
        
        return df
    
    def predict_with_model(self, month_name, forecast_df):
        """Generate predictions using month-specific model"""
        logger.info(f"🤖 Generating predictions for {month_name.capitalize()}...")
        
        # Load model
        model, scaler, model_info = self.load_model(month_name)
        
        if model is None:
            logger.error(f"❌ Model not found for {month_name}")
            return None
        
        # Load historical context for rolling stats
        conn = sqlite3.connect(self.db_path)
        historical_df = pd.read_sql_query("""
            SELECT timestamp, demand_mw
            FROM demand
            ORDER BY timestamp DESC
            LIMIT 48
        """, conn)
        conn.close()
        
        historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp'], utc=True).dt.tz_convert('America/Los_Angeles')
        historical_df = historical_df.sort_values('timestamp')
        
        # Ensure timezone consistency
        if forecast_df['timestamp'].dt.tz is None:
            forecast_df['timestamp'] = forecast_df['timestamp'].dt.tz_localize('America/Los_Angeles')
        
        # Combine for rolling calculations
        combined_df = pd.concat([historical_df, forecast_df], ignore_index=True)
        
        # Engineer features
        combined_df = self.detector.engineer_features(combined_df, 'demand_mw')
        
        # Extract forecast portion
        forecast_with_features = combined_df.iloc[len(historical_df):].copy()
        forecast_with_features = forecast_with_features.reset_index(drop=True)
        
        # Prepare features
        feature_cols = model_info['feature_columns']
        X = forecast_with_features[feature_cols].copy()
        X_scaled = scaler.transform(X)
        
        # Predict
        predictions = model.predict(X_scaled)
        anomaly_scores = model.score_samples(X_scaled)
        
        forecast_with_features['is_anomaly'] = predictions == -1
        forecast_with_features['anomaly_score'] = anomaly_scores
        forecast_with_features['confidence'] = np.abs(anomaly_scores) * 100
        forecast_with_features['confidence'] = forecast_with_features['confidence'].clip(0, 100)
        
        # Calculate severity
        def calculate_severity(row):
            if not row['is_anomaly']:
                return 'normal'
            elif row['confidence'] > 80:
                return 'critical'
            elif row['confidence'] > 60:
                return 'high'
            else:
                return 'medium'
        
        forecast_with_features['severity'] = forecast_with_features.apply(calculate_severity, axis=1)
        
        # Save predictions
        n_anomalies = forecast_with_features['is_anomaly'].sum()
        anomaly_pct = n_anomalies / len(forecast_with_features) * 100 if len(forecast_with_features) > 0 else 0
        
        predictions_data = {
            'generated_at': datetime.now().isoformat(),
            'model_type': f'{month_name}_specific',
            'model_month': month_name,
            'forecast_period': f"{forecast_with_features['timestamp'].min()} to {forecast_with_features['timestamp'].max()}",
            'total_points': len(forecast_with_features),
            'anomalies_detected': int(n_anomalies),
            'anomaly_rate': float(anomaly_pct),
            'predictions': []
        }
        
        for _, row in forecast_with_features.iterrows():
            pred = {
                'timestamp': row['timestamp'].isoformat(),
                'demand_mw': float(row['demand_mw']),
                'is_anomaly': bool(row['is_anomaly']),
                'severity': row['severity'],
                'confidence': float(row['confidence'])
            }
            predictions_data['predictions'].append(pred)
        
        output_path = self.predictions_dir / f"{month_name}_predictions.json"
        with open(output_path, 'w') as f:
            json.dump(predictions_data, f, indent=2)
        
        logger.info(f"✅ {month_name.capitalize()}: {len(forecast_with_features)} points, {n_anomalies} anomalies ({anomaly_pct:.1f}%)")
        logger.info(f"💾 Saved to: {output_path}")
        
        return predictions_data
    
    def generate_all(self):
        """Generate predictions for all available models"""
        logger.info("=" * 70)
        logger.info("GENERATE PREDICTIONS FOR ALL MONTHLY MODELS")
        logger.info("=" * 70)
        logger.info("")
        
        # Get forecast once (same for all models)
        forecast_df = self.get_forecast(hours_ahead=48)
        
        if forecast_df.empty:
            logger.error("❌ Could not fetch forecast data")
            return
        
        logger.info(f"✅ Forecast loaded: {len(forecast_df)} points")
        logger.info("")
        
        results = {}
        
        for month_name in self.months:
            try:
                predictions = self.predict_with_model(month_name, forecast_df.copy())
                if predictions:
                    results[month_name] = 'Success'
                else:
                    results[month_name] = 'Model not found'
            except Exception as e:
                logger.error(f"❌ Error for {month_name}: {e}")
                results[month_name] = f'Error: {e}'
            
            logger.info("")
        
        # Summary
        logger.info("=" * 70)
        logger.info("PREDICTION GENERATION SUMMARY")
        logger.info("=" * 70)
        
        successful = sum(1 for r in results.values() if r == 'Success')
        
        for month_name, status in results.items():
            status_icon = "✅" if status == "Success" else "⚠️" if "not found" in status else "❌"
            logger.info(f"{status_icon} {month_name.capitalize():12s} - {status}")
        
        logger.info("")
        logger.info(f"✅ Predictions generated: {successful}/12")
        logger.info("")
        logger.info("🎉 Dashboard will now auto-select predictions by current month!")


def main():
    predictor = MonthlyPredictor()
    predictor.generate_all()


if __name__ == "__main__":
    main()
