"""
ML-Based Anomaly Detection - Phase 2 Step 3

Uses Isolation Forest algorithm to detect unusual grid behavior patterns.
This is more sophisticated than simple statistical thresholds.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import pickle
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """ML-based anomaly detection using Isolation Forest."""
    
    def __init__(self, db_path: str = None):
        """Initialize with database path."""
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "historical_data" / "ladwp_grid_data.db"
        
        self.db_path = Path(db_path)
        self.models_dir = Path(__file__).parent / "trained_models"
        self.models_dir.mkdir(exist_ok=True)
        
        self.price_model = None
        self.demand_model = None
        self.price_scaler = StandardScaler()
        self.demand_scaler = StandardScaler()
        
    def load_and_prepare_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load data and engineer features for ML."""
        logger.info("📂 Loading data from database...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Check if prices table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        has_prices = cursor.fetchone() is not None
        
        # Load prices if table exists
        if has_prices:
            prices_df = pd.read_sql_query("""
                SELECT timestamp, price, congestion, energy, loss
                FROM prices
                ORDER BY timestamp
            """, conn)
            prices_df['timestamp'] = pd.to_datetime(prices_df['timestamp'])
        else:
            prices_df = pd.DataFrame()
            logger.warning("⚠️  No prices table found - will train on demand only")
        
        # Load demand
        demand_df = pd.read_sql_query("""
            SELECT timestamp, demand_mw
            FROM demand
            ORDER BY timestamp
        """, conn)
        demand_df['timestamp'] = pd.to_datetime(demand_df['timestamp'])
        
        conn.close()
        
        logger.info(f"✅ Loaded {len(prices_df)} price records, {len(demand_df)} demand records")
        
        return prices_df, demand_df
    
    def engineer_features(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """
        Create features for anomaly detection.
        
        Features include:
        - Time-based: hour, day_of_week, is_weekend
        - Value-based: current value, rolling averages, rate of change
        - Statistical: z-score within recent window
        """
        df = df.copy()
        
        # Time features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['day_of_month'] = df['timestamp'].dt.day
        
        # Cyclical encoding for hour (24-hour cycle)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Cyclical encoding for day of week (7-day cycle)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Seasonal features (helps model understand Aug vs Sep vs Oct patterns)
        df['month'] = df['timestamp'].dt.month
        df['week_of_year'] = df['timestamp'].dt.isocalendar().week
        df['is_summer'] = df['month'].isin([6, 7, 8, 9]).astype(int)  # Jun-Sep
        df['is_winter'] = df['month'].isin([12, 1, 2]).astype(int)  # Dec-Feb
        
        # Rolling statistics (looking back 24 hours for prices, fewer for demand)
        window = 288 if target_col == 'price' else 24  # 288 = 24 hours of 5-min data
        
        df[f'{target_col}_rolling_mean'] = df[target_col].rolling(window=window, min_periods=1).mean()
        df[f'{target_col}_rolling_std'] = df[target_col].rolling(window=window, min_periods=1).std()
        df[f'{target_col}_rolling_min'] = df[target_col].rolling(window=window, min_periods=1).min()
        df[f'{target_col}_rolling_max'] = df[target_col].rolling(window=window, min_periods=1).max()
        
        # Rate of change
        df[f'{target_col}_diff'] = df[target_col].diff()
        df[f'{target_col}_pct_change'] = df[target_col].pct_change()
        
        # Z-score relative to recent window
        df[f'{target_col}_zscore'] = (df[target_col] - df[f'{target_col}_rolling_mean']) / (df[f'{target_col}_rolling_std'] + 1e-8)
        
        # Fill NaN values (from rolling calculations)
        df = df.fillna(method='bfill').fillna(method='ffill')
        
        return df
    
    def train_price_anomaly_detector(self, contamination: float = 0.05):
        """
        Train Isolation Forest for price anomaly detection.
        
        Args:
            contamination: Expected proportion of anomalies (default 5%)
        """
        logger.info("=" * 60)
        logger.info("TRAINING PRICE ANOMALY DETECTOR")
        logger.info("=" * 60)
        
        # Load and prepare data
        prices_df, _ = self.load_and_prepare_data()
        prices_df = self.engineer_features(prices_df, 'price')
        
        # Select features for training
        feature_cols = [
            'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'is_weekend',
            'price', 'congestion', 'energy', 'loss',
            'price_rolling_mean', 'price_rolling_std',
            'price_rolling_min', 'price_rolling_max',
            'price_diff', 'price_pct_change', 'price_zscore'
        ]
        
        X = prices_df[feature_cols].copy()
        
        logger.info(f"📊 Training on {len(X)} samples with {len(feature_cols)} features")
        logger.info(f"   Features: {', '.join(feature_cols[:5])}... (+{len(feature_cols)-5} more)")
        
        # Scale features
        X_scaled = self.price_scaler.fit_transform(X)
        
        # Train Isolation Forest
        logger.info(f"🤖 Training Isolation Forest (contamination={contamination})...")
        self.price_model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1  # Use all CPU cores
        )
        
        self.price_model.fit(X_scaled)
        
        # Evaluate on training data
        predictions = self.price_model.predict(X_scaled)
        anomaly_scores = self.price_model.score_samples(X_scaled)
        
        n_anomalies = (predictions == -1).sum()
        anomaly_pct = n_anomalies / len(predictions) * 100
        
        logger.info(f"✅ Training complete!")
        logger.info(f"   Detected {n_anomalies} anomalies ({anomaly_pct:.1f}%)")
        logger.info(f"   Anomaly score range: {anomaly_scores.min():.3f} to {anomaly_scores.max():.3f}")
        
        # Save model and scaler
        model_path = self.models_dir / "price_anomaly_detector.pkl"
        scaler_path = self.models_dir / "price_scaler.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.price_model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.price_scaler, f)
        
        logger.info(f"💾 Model saved to: {model_path}")
        
        # Save feature names for later use
        feature_info = {
            'feature_columns': feature_cols,
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(X),
            'contamination': contamination,
            'n_anomalies_detected': int(n_anomalies)
        }
        
        with open(self.models_dir / "price_model_info.json", 'w') as f:
            json.dump(feature_info, f, indent=2)
        
        return predictions, anomaly_scores
    
    def train_demand_anomaly_detector(self, contamination: float = 0.05):
        """
        Train Isolation Forest for demand anomaly detection.
        
        Args:
            contamination: Expected proportion of anomalies (default 5%)
        """
        logger.info("=" * 60)
        logger.info("TRAINING DEMAND ANOMALY DETECTOR")
        logger.info("=" * 60)
        
        # Load and prepare data
        _, demand_df = self.load_and_prepare_data()
        demand_df = self.engineer_features(demand_df, 'demand_mw')
        
        # Select features for training (includes seasonal features for better pattern recognition)
        # Note: Removed rolling stats and zscore because they compare across seasons
        # which causes October (cooler) to look anomalous compared to August/September (hotter)
        feature_cols = [
            'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'is_weekend',
            'month', 'week_of_year', 'is_summer', 'is_winter',  # Seasonal context
            'demand_mw',
            'demand_mw_diff', 'demand_mw_pct_change'  # Rate of change features only
        ]
        
        X = demand_df[feature_cols].copy()
        
        logger.info(f"📊 Training on {len(X)} samples with {len(feature_cols)} features")
        
        # Scale features
        X_scaled = self.demand_scaler.fit_transform(X)
        
        # Train Isolation Forest
        logger.info(f"🤖 Training Isolation Forest (contamination={contamination})...")
        self.demand_model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1
        )
        
        self.demand_model.fit(X_scaled)
        
        # Evaluate
        predictions = self.demand_model.predict(X_scaled)
        anomaly_scores = self.demand_model.score_samples(X_scaled)
        
        n_anomalies = (predictions == -1).sum()
        anomaly_pct = n_anomalies / len(predictions) * 100
        
        logger.info(f"✅ Training complete!")
        logger.info(f"   Detected {n_anomalies} anomalies ({anomaly_pct:.1f}%)")
        logger.info(f"   Anomaly score range: {anomaly_scores.min():.3f} to {anomaly_scores.max():.3f}")
        
        # Save model and scaler
        model_path = self.models_dir / "demand_anomaly_detector.pkl"
        scaler_path = self.models_dir / "demand_scaler.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.demand_model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.demand_scaler, f)
        
        logger.info(f"💾 Model saved to: {model_path}")
        
        # Save feature info
        feature_info = {
            'feature_columns': feature_cols,
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(X),
            'contamination': contamination,
            'n_anomalies_detected': int(n_anomalies)
        }
        
        with open(self.models_dir / "demand_model_info.json", 'w') as f:
            json.dump(feature_info, f, indent=2)
        
        return predictions, anomaly_scores
    
    def load_models(self):
        """Load trained models from disk."""
        logger.info("📂 Loading trained models...")
        
        # Load price model
        with open(self.models_dir / "price_anomaly_detector.pkl", 'rb') as f:
            self.price_model = pickle.load(f)
        with open(self.models_dir / "price_scaler.pkl", 'rb') as f:
            self.price_scaler = pickle.load(f)
        
        # Load demand model
        with open(self.models_dir / "demand_anomaly_detector.pkl", 'rb') as f:
            self.demand_model = pickle.load(f)
        with open(self.models_dir / "demand_scaler.pkl", 'rb') as f:
            self.demand_scaler = pickle.load(f)
        
        logger.info("✅ Models loaded successfully")
    
    def detect_price_anomaly(self, price_data: dict) -> dict:
        """
        Detect if current price is anomalous using trained model.
        
        Args:
            price_data: Dict with keys: timestamp, price, congestion, energy, loss
        
        Returns:
            Dict with is_anomaly, anomaly_score, confidence
        """
        if self.price_model is None:
            self.load_models()
        
        # Load feature info
        with open(self.models_dir / "price_model_info.json", 'r') as f:
            feature_info = json.load(f)
        
        # Engineer features (simplified for single prediction)
        # In production, you'd need recent historical context
        # For now, we'll use the provided values
        
        timestamp = pd.to_datetime(price_data['timestamp'])
        hour = timestamp.hour
        dow = timestamp.dayofweek
        
        # Create feature vector (matching training features)
        features = {
            'hour_sin': np.sin(2 * np.pi * hour / 24),
            'hour_cos': np.cos(2 * np.pi * hour / 24),
            'dow_sin': np.sin(2 * np.pi * dow / 7),
            'dow_cos': np.cos(2 * np.pi * dow / 7),
            'is_weekend': int(dow in [5, 6]),
            'price': price_data['price'],
            'congestion': price_data.get('congestion', 0),
            'energy': price_data.get('energy', 0),
            'loss': price_data.get('loss', 0),
            # Rolling features would need historical context
            # Using current price as approximation for demo
            'price_rolling_mean': price_data['price'],
            'price_rolling_std': 10,  # Default std
            'price_rolling_min': price_data['price'] - 20,
            'price_rolling_max': price_data['price'] + 20,
            'price_diff': 0,
            'price_pct_change': 0,
            'price_zscore': 0
        }
        
        X = pd.DataFrame([features])
        X_scaled = self.price_scaler.transform(X)
        
        # Predict
        prediction = self.price_model.predict(X_scaled)[0]
        anomaly_score = self.price_model.score_samples(X_scaled)[0]
        
        # Convert to interpretable format
        is_anomaly = prediction == -1
        
        # Confidence (higher absolute score = more confident)
        confidence = min(abs(anomaly_score) * 100, 100)
        
        return {
            'is_anomaly': bool(is_anomaly),
            'anomaly_score': float(anomaly_score),
            'confidence': round(confidence, 1),
            'severity': 'high' if is_anomaly and confidence > 80 else ('medium' if is_anomaly else 'normal')
        }


def main():
    """Train anomaly detectors (demand only if no price data)."""
    detector = AnomalyDetector()
    
    # Check if we have price data
    prices_df, demand_df = detector.load_and_prepare_data()
    
    if not prices_df.empty:
        # Train price anomaly detector
        price_predictions, price_scores = detector.train_price_anomaly_detector(contamination=0.05)
        print("\n")
    else:
        print("⚠️  No price data available, skipping price anomaly detector\n")
    
    # Train demand anomaly detector (20% contamination to handle seasonal transitions)
    # Higher rate needed because Aug (3,189 MW) vs Oct (2,514 MW) creates natural variation
    demand_predictions, demand_scores = detector.train_demand_anomaly_detector(contamination=0.20)
    
    print("\n" + "=" * 60)
    print("ML ANOMALY DETECTION MODELS TRAINED")
    print("=" * 60)
    print("\nModels ready for real-time anomaly detection!")
    print("\nNext Steps:")
    print("   1. Generate future anomaly predictions")
    print("   2. Integrate with dashboard for live alerts")
    print("   3. Train price spike prediction model (Step 4)")
    print("=" * 60)


if __name__ == "__main__":
    main()
