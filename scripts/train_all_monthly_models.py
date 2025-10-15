"""
Train Month-Specific Anomaly Detection Models

Trains a separate Isolation Forest model for each month using only that
month's historical data. This eliminates seasonal bias.

For each month:
1. Load data for that month only
2. Engineer features
3. Train Isolation Forest (contamination=0.05)
4. Save model, scaler, and metadata

Models will be saved as:
- models/trained_models/january_demand_anomaly_detector.pkl
- models/trained_models/february_demand_anomaly_detector.pkl
- etc.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import pickle
import logging
import sys
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.append(str(Path(__file__).parent))
from models.anomaly_detector import AnomalyDetector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MonthlyModelTrainer:
    """Train anomaly detection models for each month"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "data" / "historical_data" / "ladwp_grid_data.db"
        self.models_dir = Path(__file__).parent / "models" / "trained_models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.detector = AnomalyDetector()
        
        self.months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
    
    def load_month_data(self, month_num):
        """Load all data for a specific month (from any year)"""
        month_name = self.months[month_num - 1]
        
        logger.info(f"📂 Loading {month_name.capitalize()} data...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get all data where month matches
        df = pd.read_sql_query("""
            SELECT timestamp, demand_mw
            FROM demand
            WHERE CAST(strftime('%m', timestamp) AS INTEGER) = ?
            ORDER BY timestamp
        """, conn, params=(month_num,))
        
        conn.close()
        
        if df.empty:
            logger.warning(f"⚠️  No data found for {month_name}")
            return None
        
        # Convert to datetime with UTC=True to handle mixed timezones (DST transitions)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        # Convert to Pacific time
        df['timestamp'] = df['timestamp'].dt.tz_convert('America/Los_Angeles')
        
        logger.info(f"✅ Loaded {len(df)} records for {month_name.capitalize()}")
        logger.info(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        logger.info(f"   Average: {df['demand_mw'].mean():.0f} MW")
        
        return df
    
    def train_month_model(self, month_num, contamination=0.02):
        """Train model for a specific month (contamination=0.02 means expect 2% anomalies)"""
        month_name = self.months[month_num - 1]
        
        logger.info("=" * 70)
        logger.info(f"TRAINING MODEL FOR {month_name.upper()}")
        logger.info("=" * 70)
        
        # Load data
        df = self.load_month_data(month_num)
        
        if df is None or len(df) < 100:
            logger.error(f"❌ Insufficient data for {month_name} (need at least 100 records)")
            return False
        
        # Engineer features
        logger.info("🔧 Engineering features...")
        df = self.detector.engineer_features(df, 'demand_mw')
        
        # Select features (include rolling stats since we're training on same-month data)
        feature_cols = [
            'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'is_weekend',
            'month', 'week_of_year', 'is_summer', 'is_winter',
            'demand_mw',
            'demand_mw_rolling_mean', 'demand_mw_rolling_std',
            'demand_mw_diff', 'demand_mw_pct_change', 'demand_mw_zscore'
        ]
        
        X = df[feature_cols].copy()
        
        logger.info(f"📊 Training on {len(X)} samples with {len(feature_cols)} features")
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train Isolation Forest with adjusted parameters to reduce overfitting
        logger.info(f"🤖 Training Isolation Forest (contamination={contamination})...")
        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=200,  # More trees for better generalization
            max_samples=min(256, len(X)),  # Limit subsample size
            max_features=0.8,  # Use 80% of features per tree
            bootstrap=True,  # Enable bootstrap sampling
            n_jobs=-1
        )
        
        model.fit(X_scaled)
        
        # Evaluate on training data
        predictions = model.predict(X_scaled)
        anomaly_scores = model.score_samples(X_scaled)
        
        n_anomalies = (predictions == -1).sum()
        anomaly_pct = n_anomalies / len(predictions) * 100
        
        logger.info(f"✅ Training complete!")
        logger.info(f"   Detected {n_anomalies} anomalies ({anomaly_pct:.1f}%)")
        logger.info(f"   Anomaly score range: {anomaly_scores.min():.3f} to {anomaly_scores.max():.3f}")
        
        # Save model
        model_path = self.models_dir / f"{month_name}_demand_anomaly_detector.pkl"
        scaler_path = self.models_dir / f"{month_name}_demand_scaler.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        
        logger.info(f"💾 Model saved to: {model_path}")
        
        # Save model info
        model_info = {
            'month': month_name,
            'month_number': month_num,
            'feature_columns': feature_cols,
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(X),
            'contamination': contamination,
            'n_anomalies_detected': int(n_anomalies),
            'training_period': f'{df["timestamp"].min()} to {df["timestamp"].max()}',
            'avg_demand': float(df['demand_mw'].mean()),
            'std_demand': float(df['demand_mw'].std()),
            'min_demand': float(df['demand_mw'].min()),
            'max_demand': float(df['demand_mw'].max()),
            'model_type': 'month_specific'
        }
        
        info_path = self.models_dir / f"{month_name}_model_info.json"
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"📄 Model info saved to: {info_path}")
        
        return True
    
    def train_all(self, contamination=0.05):
        """Train models for all 12 months"""
        logger.info("=" * 70)
        logger.info("TRAIN MONTH-SPECIFIC ANOMALY DETECTION MODELS")
        logger.info("=" * 70)
        logger.info("")
        logger.info(f"Strategy: Train separate model for each month")
        logger.info(f"Contamination rate: {contamination*100}%")
        logger.info(f"Models to train: 12 (one per month)")
        logger.info("")
        
        results = {}
        
        for month_num in range(1, 13):
            month_name = self.months[month_num - 1]
            
            try:
                success = self.train_month_model(month_num, contamination)
                results[month_name] = 'Success' if success else 'Failed'
            except Exception as e:
                logger.error(f"❌ Error training {month_name}: {e}")
                results[month_name] = f'Error: {e}'
            
            logger.info("")
        
        # Summary
        logger.info("=" * 70)
        logger.info("TRAINING SUMMARY")
        logger.info("=" * 70)
        
        successful = sum(1 for r in results.values() if r == 'Success')
        
        for month_name, status in results.items():
            status_icon = "✅" if status == "Success" else "❌"
            logger.info(f"{status_icon} {month_name.capitalize():12s} - {status}")
        
        logger.info("")
        logger.info(f"✅ Models trained: {successful}/12")
        
        if successful == 12:
            logger.info("")
            logger.info("🎉 ALL MODELS TRAINED SUCCESSFULLY!")
            logger.info("")
            logger.info("Next steps:")
            logger.info("  1. Update dashboard.py to auto-select model by current month")
            logger.info("  2. Test predictions for each month")
            logger.info("  3. Monitor model performance over time")
        
        return results


def main():
    trainer = MonthlyModelTrainer()
    trainer.train_all(contamination=0.02)  # 2% expected anomalies (more conservative)


if __name__ == "__main__":
    main()
