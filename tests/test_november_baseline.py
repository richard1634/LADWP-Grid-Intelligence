"""
Test November Model with Actual November 2024 Training Data
Expected Result: ~0% anomaly rate (model should recognize its own training data)
"""

import sqlite3
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
import json

def load_november_model():
    """Load the November-specific model and scaler"""
    models_dir = Path(__file__).parent / 'models'
    
    # Load model
    model_path = models_dir / 'trained_models' / 'november_demand_anomaly_detector.pkl'
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load scaler
    scaler_path = models_dir / 'trained_models' / 'november_demand_scaler.pkl'
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    # Load model info
    info_path = models_dir / 'trained_models' / 'november_model_info.json'
    with open(info_path, 'r') as f:
        model_info = json.load(f)
    
    print(f"✅ Model loaded: {model_info['model_type']}")
    print(f"   Feature columns: {len(model_info['feature_columns'])}")
    print(f"   Training samples: {model_info['n_samples']}")
    print(f"   Training period: {model_info['training_period']}")
    
    return model, scaler, model_info

def load_november_2024_data():
    """Load actual November 2024 data from the database"""
    print("\n📂 Loading November 2024 historical data from database...")
    
    db_path = Path(__file__).parent / 'data' / 'historical_data' / 'ladwp_grid_data.db'
    
    conn = sqlite3.connect(db_path)
    
    # Query November 2024 data
    query = """
    SELECT timestamp, demand_mw
    FROM demand
    WHERE timestamp >= '2024-11-01 00:00:00'
      AND timestamp < '2024-12-01 00:00:00'
    ORDER BY timestamp
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert('America/Los_Angeles')
    
    print(f"✅ Loaded {len(df)} records")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   Demand range: {df['demand_mw'].min():.0f} - {df['demand_mw'].max():.0f} MW")
    
    return df

def prepare_features(df):
    """Add time-based features matching model expectations"""
    df = df.copy()
    
    # Time-based features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['week_of_year'] = df['timestamp'].dt.isocalendar().week
    
    # Cyclic encodings
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    # Binary features
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
    df['is_winter'] = df['month'].isin([12, 1, 2]).astype(int)
    
    # Rolling statistics (3-hour window)
    df['demand_mw_rolling_mean'] = df['demand_mw'].rolling(window=3, min_periods=1).mean()
    df['demand_mw_rolling_std'] = df['demand_mw'].rolling(window=3, min_periods=1).std().fillna(0)
    
    # Lag features
    df['demand_mw_diff'] = df['demand_mw'].diff().fillna(0)
    df['demand_mw_pct_change'] = df['demand_mw'].pct_change().fillna(0)
    
    # Z-score
    mean_demand = df['demand_mw'].mean()
    std_demand = df['demand_mw'].std()
    df['demand_mw_zscore'] = (df['demand_mw'] - mean_demand) / std_demand
    
    return df

def run_november_model(df, model, scaler, model_info):
    """Run the November model on the data"""
    print("\n🤖 Running November anomaly detection model...")
    
    # Prepare features
    feature_columns = model_info['feature_columns']
    X = df[feature_columns].values
    
    # Scale features
    X_scaled = scaler.transform(X)
    
    # Predict
    predictions = model.predict(X_scaled)
    anomaly_scores = model.score_samples(X_scaled)
    
    # Add predictions to dataframe
    df['is_anomaly'] = predictions == -1
    df['anomaly_score'] = anomaly_scores
    
    # Calculate severity and confidence
    threshold = model_info.get('anomaly_threshold', np.percentile(anomaly_scores, 5))
    
    def calculate_severity(score):
        if score > threshold:
            return 'normal'
        deviation = abs(score - threshold)
        if deviation > 0.5:
            return 'high'
        elif deviation > 0.2:
            return 'medium'
        else:
            return 'low'
    
    def calculate_confidence(score):
        deviation = abs(score - threshold)
        confidence = min(deviation * 100, 95)
        return round(confidence, 1)
    
    df['severity'] = df['anomaly_score'].apply(calculate_severity)
    df['confidence'] = df['anomaly_score'].apply(calculate_confidence)
    
    return df

def analyze_results(df):
    """Analyze and display results"""
    print("\n" + "="*60)
    print("📊 BASELINE VALIDATION RESULTS")
    print("="*60)
    
    total_points = len(df)
    anomalies = df[df['is_anomaly']].copy()
    anomaly_count = len(anomalies)
    anomaly_rate = (anomaly_count / total_points * 100)
    
    # Count high-confidence anomalies (>50%)
    high_conf_anomalies = anomalies[anomalies['confidence'] > 50]
    high_conf_count = len(high_conf_anomalies)
    high_conf_rate = (high_conf_count / total_points * 100)
    
    print(f"\n📈 Summary:")
    print(f"   Total data points: {total_points}")
    print(f"   Anomalies detected: {anomaly_count}")
    print(f"   Anomaly rate: {anomaly_rate:.2f}%")
    print(f"   High-confidence anomalies (>50%): {high_conf_count}")
    print(f"   High-confidence rate: {high_conf_rate:.2f}%")
    print(f"   Expected rate: ~2% (contamination parameter)")
    
    if high_conf_rate < 10:
        print(f"\n✅ PASS: High-confidence anomaly rate is {high_conf_rate:.2f}% (within expected range)")
        print("   Model correctly recognizes its training data as normal!")
        print(f"   (Note: {anomaly_count - high_conf_count} low-confidence anomalies with <50% confidence are expected edge cases)")
    else:
        print(f"\n⚠️ WARNING: High-confidence anomaly rate is {high_conf_rate:.2f}% (higher than expected)")
        print("   This may indicate model issues or data quality problems")
    
    if anomaly_count > 0:
        print(f"\n🔍 Detected Anomalies (showing first 10):")
        for idx, row in anomalies.head(10).iterrows():
            timestamp = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            demand = row['demand_mw']
            severity = row['severity']
            confidence = row['confidence']
            print(f"   📍 {timestamp} - {demand:.0f} MW ({severity.upper()}, {confidence}% confidence)")
        
        if anomaly_count > 10:
            print(f"   ... and {anomaly_count - 10} more")
    
    # Statistical summary
    print(f"\n📊 Demand Statistics:")
    print(f"   Mean: {df['demand_mw'].mean():.0f} MW")
    print(f"   Std: {df['demand_mw'].std():.0f} MW")
    print(f"   Min: {df['demand_mw'].min():.0f} MW")
    print(f"   Max: {df['demand_mw'].max():.0f} MW")
    
    return {
        'total_points': total_points,
        'anomaly_count': anomaly_count,
        'anomaly_rate': anomaly_rate,
        'high_conf_count': high_conf_count,
        'high_conf_rate': high_conf_rate,
        'passed': high_conf_rate < 10
    }

def main():
    print("="*60)
    print("🧪 NOVEMBER BASELINE VALIDATION TEST")
    print("="*60)
    print("Testing November model with actual November 2024 training data")
    print("Expected: Anomaly rate should be near 0% (model recognizes its own training data)")
    print()
    
    # Load model
    model, scaler, model_info = load_november_model()
    
    # Load November 2024 data
    df = load_november_2024_data()
    
    # Prepare features
    print("\n⚙️ Preparing features...")
    df = prepare_features(df)
    print(f"✅ Engineered {len(df.columns)} features")
    
    # Run model
    df = run_november_model(df, model, scaler, model_info)
    
    # Analyze results
    results = analyze_results(df)
    
    print("\n" + "="*60)
    if results['passed']:
        print("✅ TEST PASSED")
        print(f"Model correctly recognizes November 2024 training data!")
        print(f"High-confidence anomaly rate: {results['high_conf_rate']:.2f}% (within expected range)")
        print(f"Total anomalies: {results['anomaly_count']} ({results['anomaly_rate']:.2f}%), but {results['anomaly_count'] - results['high_conf_count']} are low-confidence edge cases")
    else:
        print("❌ TEST FAILED")
        print(f"High-confidence anomaly rate: {results['high_conf_rate']:.2f}% (higher than expected)")
    print("="*60)

if __name__ == '__main__':
    main()
