"""
Future Demand Anomaly Predictor - Phase 2 Step 4

Uses CAISO's demand forecast and ML anomaly detection to predict
which future time periods will have unusual demand patterns.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from caiso_api_client import CAISOClient

# Import from same directory
sys.path.append(str(Path(__file__).parent))
from anomaly_detector import AnomalyDetector
from baseline_patterns import BaselinePatterns

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FutureAnomalyPredictor:
    """Predict anomalies in future demand using CAISO forecasts."""
    
    def __init__(self):
        """Initialize with CAISO client and anomaly detector."""
        self.caiso_client = CAISOClient()
        self.anomaly_detector = AnomalyDetector()
        self.anomaly_detector.load_models()
        
        # Load baseline patterns for comparison
        self.baseline = BaselinePatterns()
        try:
            self.baseline.load_patterns()
        except:
            logger.warning("Baseline patterns not found, run baseline_patterns.py first")
            self.baseline = None
    
    def get_future_forecast(self, hours_ahead: int = 48) -> pd.DataFrame:
        """
        Get CAISO's demand forecast for LADWP.
        
        Args:
            hours_ahead: How many hours ahead to forecast (default: 48)
        
        Returns:
            DataFrame with timestamp and forecasted demand_mw
        """
        logger.info(f"📡 Fetching CAISO forecast for next {hours_ahead} hours...")
        
        # Get CAISO forecast
        forecast_df = self.caiso_client.get_system_demand(hours_ahead=hours_ahead)
        
        if forecast_df is None or forecast_df.empty:
            logger.error("No forecast data available")
            return pd.DataFrame()
        
        # Filter to LADWP only
        forecast_df = forecast_df[forecast_df['TAC_AREA_NAME'] == 'LADWP'].copy()
        
        # Convert MW to numeric
        forecast_df['demand_mw'] = pd.to_numeric(forecast_df['MW'], errors='coerce')
        
        # Filter to future only
        now = datetime.now(self.caiso_client.pacific_tz)
        forecast_df['timestamp'] = pd.to_datetime(forecast_df['timestamp'])
        forecast_df = forecast_df[forecast_df['timestamp'] > now].copy()
        
        # Sort by timestamp
        forecast_df = forecast_df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"✅ Loaded {len(forecast_df)} future forecast points")
        logger.info(f"   Range: {forecast_df['timestamp'].min()} to {forecast_df['timestamp'].max()}")
        
        return forecast_df[['timestamp', 'demand_mw']]
    
    def predict_future_anomalies(self, hours_ahead: int = 48) -> pd.DataFrame:
        """
        Predict which future time periods will have anomalous demand.
        
        Args:
            hours_ahead: How many hours ahead to predict (default: 48)
        
        Returns:
            DataFrame with predictions including anomaly flags and scores
        """
        logger.info("=" * 70)
        logger.info("PREDICTING FUTURE DEMAND ANOMALIES")
        logger.info("=" * 70)
        
        # Get CAISO forecast
        forecast_df = self.get_future_forecast(hours_ahead)
        
        if forecast_df.empty:
            logger.error("No forecast data available")
            return pd.DataFrame()
        
        # CRITICAL: Load recent historical data to compute rolling statistics correctly
        # Rolling stats need past data to work properly for future predictions
        logger.info("📂 Loading recent historical data for rolling statistics...")
        db_path = Path(__file__).parent.parent / "data" / "historical_data" / "ladwp_grid_data.db"
        conn = sqlite3.connect(db_path)
        
        # Get last 48 hours of historical data for rolling window calculations
        historical_df = pd.read_sql_query("""
            SELECT timestamp, demand_mw
            FROM demand
            ORDER BY timestamp DESC
            LIMIT 48
        """, conn)
        conn.close()
        
        historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp'], utc=True).dt.tz_convert('America/Los_Angeles')
        historical_df = historical_df.sort_values('timestamp')  # Sort ascending
        
        # Ensure forecast_df also has timezone-aware timestamps
        if forecast_df['timestamp'].dt.tz is None:
            forecast_df['timestamp'] = forecast_df['timestamp'].dt.tz_localize('America/Los_Angeles')
        
        # Combine historical + forecast for proper rolling calculations
        combined_df = pd.concat([historical_df, forecast_df], ignore_index=True)
        logger.info(f"   Combined {len(historical_df)} historical + {len(forecast_df)} forecast points")
        
        # Engineer features on combined data (rolling stats will use historical context)
        combined_df = self.anomaly_detector.engineer_features(combined_df, 'demand_mw')
        
        # Extract only the forecast portion (after historical data)
        forecast_df = combined_df.iloc[len(historical_df):].copy()
        forecast_df = forecast_df.reset_index(drop=True)
        
        # Load feature info
        model_info_path = Path(__file__).parent / "trained_models" / "demand_model_info.json"
        with open(model_info_path, 'r') as f:
            model_info = json.load(f)
        
        # Prepare features for prediction
        feature_cols = model_info['feature_columns']
        X = forecast_df[feature_cols].copy()
        
        # Scale features
        X_scaled = self.anomaly_detector.demand_scaler.transform(X)
        
        # Predict anomalies
        logger.info("🤖 Running anomaly detection on future forecast...")
        predictions = self.anomaly_detector.demand_model.predict(X_scaled)
        anomaly_scores = self.anomaly_detector.demand_model.score_samples(X_scaled)
        
        # Add predictions to dataframe
        forecast_df['is_anomaly'] = predictions == -1
        forecast_df['anomaly_score'] = anomaly_scores
        forecast_df['confidence'] = np.abs(anomaly_scores) * 100
        forecast_df['confidence'] = forecast_df['confidence'].clip(0, 100)
        
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
        
        forecast_df['severity'] = forecast_df.apply(calculate_severity, axis=1)
        
        # NOTE: Removed baseline comparison - anomalies are now based purely on
        # the ML model detecting unusual patterns in CAISO's forecasts themselves,
        # not comparing to historical averages
        
        # Summary statistics
        n_anomalies = forecast_df['is_anomaly'].sum()
        anomaly_pct = n_anomalies / len(forecast_df) * 100
        
        logger.info(f"✅ Prediction complete!")
        logger.info(f"   Total forecast points: {len(forecast_df)}")
        logger.info(f"   Predicted anomalies: {n_anomalies} ({anomaly_pct:.1f}%)")
        
        if n_anomalies > 0:
            logger.info(f"   Severity breakdown:")
            severity_counts = forecast_df[forecast_df['is_anomaly']]['severity'].value_counts()
            for severity, count in severity_counts.items():
                logger.info(f"      {severity}: {count}")
        
        return forecast_df
    
    def get_anomaly_alerts(self, forecast_df: pd.DataFrame) -> list:
        """
        Generate actionable alerts for predicted anomalies.
        
        Args:
            forecast_df: DataFrame with anomaly predictions
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        anomalies = forecast_df[forecast_df['is_anomaly']].copy()
        
        for idx, row in anomalies.iterrows():
            alert = {
                'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'time_until': self._format_time_until(row['timestamp']),
                'demand_mw': round(row['demand_mw'], 0),
                'severity': row['severity'],
                'confidence': round(row['confidence'], 1),
                'anomaly_score': round(row['anomaly_score'], 3),
                'explanation': 'Unusual forecast pattern detected by ML model'
            }
            
            alerts.append(alert)
        
        return alerts
    
    def _format_time_until(self, timestamp: pd.Timestamp) -> str:
        """Format time until future timestamp."""
        now = datetime.now(self.caiso_client.pacific_tz)
        delta = timestamp - now
        
        hours = delta.total_seconds() / 3600
        
        if hours < 1:
            return f"{int(delta.total_seconds() / 60)} minutes"
        elif hours < 24:
            return f"{int(hours)} hours"
        else:
            days = int(hours / 24)
            remaining_hours = int(hours % 24)
            return f"{days}d {remaining_hours}h"
    
    def save_predictions(self, forecast_df: pd.DataFrame, filename: str = None):
        """Save predictions to JSON file for dashboard integration."""
        if filename is None:
            filename = f"future_anomaly_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_dir = Path(__file__).parent / "predictions"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / filename
        
        # Prepare data for JSON
        predictions = {
            'generated_at': datetime.now().isoformat(),
            'forecast_points': len(forecast_df),
            'anomaly_count': int(forecast_df['is_anomaly'].sum()),
            'predictions': []
        }
        
        for idx, row in forecast_df.iterrows():
            point = {
                'timestamp': row['timestamp'].isoformat(),
                'demand_mw': float(row['demand_mw']),
                'is_anomaly': bool(row['is_anomaly']),
                'anomaly_score': float(row['anomaly_score']),
                'severity': row['severity'],
                'confidence': float(row['confidence']),
                'explanation': 'ML model detected unusual CAISO forecast pattern'
            }
            
            predictions['predictions'].append(point)
        
        with open(output_path, 'w') as f:
            json.dump(predictions, f, indent=2)
        
        logger.info(f"💾 Predictions saved to: {output_path}")
        
        return output_path


def main():
    """Run future anomaly prediction."""
    predictor = FutureAnomalyPredictor()
    
    # Predict anomalies in next 48 hours
    forecast_df = predictor.predict_future_anomalies(hours_ahead=48)
    
    if forecast_df.empty:
        print("\n❌ No forecast data available")
        return
    
    # Get alerts
    alerts = predictor.get_anomaly_alerts(forecast_df)
    
    # Display results
    print("\n" + "=" * 70)
    print("FUTURE DEMAND ANOMALY PREDICTIONS")
    print("=" * 70)
    
    if len(alerts) == 0:
        print("\n✅ No anomalies predicted in the next 48 hours")
        print(f"   All {len(forecast_df)} forecast points appear normal")
    else:
        print(f"\n🚨 {len(alerts)} ANOMALIES PREDICTED:")
        print("-" * 70)
        
        for i, alert in enumerate(alerts[:10], 1):  # Show top 10
            print(f"\n{i}. {alert['timestamp']} (in {alert['time_until']})")
            print(f"   CAISO Forecast: {alert['demand_mw']:.0f} MW")
            print(f"   Severity: {alert['severity'].upper()}")
            print(f"   Confidence: {alert['confidence']:.1f}%")
            print(f"   Reason: Unusual forecast pattern detected by ML model")
        
        if len(alerts) > 10:
            print(f"\n   ... and {len(alerts) - 10} more anomalies")
        
        # Show severity breakdown
        severity_counts = pd.Series([a['severity'] for a in alerts]).value_counts()
        print(f"\n📊 SEVERITY BREAKDOWN:")
        for severity, count in severity_counts.items():
            print(f"   {severity.capitalize()}: {count}")
        
        # Timeline of anomalies
        print(f"\n📅 ANOMALY TIMELINE:")
        for alert in alerts[:5]:
            emoji = "🔴" if alert['severity'] == 'critical' else "🟡" if alert['severity'] == 'high' else "🟠"
            print(f"   {emoji} {alert['timestamp']} - {alert['demand_mw']:.0f} MW ({alert['severity']})")
    
    # Save predictions
    output_path = predictor.save_predictions(forecast_df, "latest_predictions.json")
    
    print("\n" + "=" * 70)
    print("✅ PREDICTIONS COMPLETE")
    print("=" * 70)
    print(f"\n💾 Data saved to: {output_path}")
    print(f"\n💡 Integration Notes:")
    print("   - These predictions can be displayed on your dashboard")
    print("   - Update every hour for latest CAISO forecast")
    print("   - Use for proactive grid management")
    print("   - Set up alerts for critical severity anomalies")


if __name__ == "__main__":
    main()
