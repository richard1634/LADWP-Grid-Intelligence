"""
Generate Mock November Data

Creates realistic November forecast data by:
1. Analyzing actual November model patterns
2. Generating synthetic November-like demand values
3. Running November model to verify low anomaly rate
"""

import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "models"))

def load_november_model():
    """Load November model and get typical patterns"""
    print("📂 Loading November model...")
    
    base_path = Path(__file__).parent / "models" / "trained_models"
    
    with open(base_path / "november_demand_anomaly_detector.pkl", 'rb') as f:
        model = pickle.load(f)
    
    with open(base_path / "november_demand_scaler.pkl", 'rb') as f:
        scaler = pickle.load(f)
    
    with open(base_path / "november_model_info.json", 'r') as f:
        info = json.load(f)
    
    print(f"✅ Model loaded: {info.get('model_type')}")
    print(f"   Feature columns: {len(info.get('feature_columns', []))}")
    
    return model, scaler, info


def generate_november_demand_pattern():
    """Generate realistic November demand patterns"""
    print("\n📊 Generating November demand patterns...")
    
    # November characteristics for LADWP:
    # - Cooler weather (60-70°F typical)
    # - Less AC usage than summer
    # - Some heating starts (especially mornings/evenings)
    # - Typical range: 1,900-2,800 MW
    # - Peak around 6-7 PM (people get home, turn on heat/lights)
    
    # Generate 30 hours of November data (next day forecast)
    start_time = datetime(2025, 11, 1, 12, 0, 0)  # Noon November 1st
    
    data_points = []
    
    for hour in range(30):
        timestamp = start_time + timedelta(hours=hour)
        hour_of_day = timestamp.hour
        
        # Base demand by time of day (November patterns)
        if 0 <= hour_of_day < 6:  # Late night/early morning
            base_demand = 1950 + np.random.normal(0, 50)
        elif 6 <= hour_of_day < 9:  # Morning rise
            base_demand = 2100 + (hour_of_day - 6) * 80 + np.random.normal(0, 60)
        elif 9 <= hour_of_day < 12:  # Late morning
            base_demand = 2350 + np.random.normal(0, 70)
        elif 12 <= hour_of_day < 17:  # Afternoon
            base_demand = 2400 + np.random.normal(0, 80)
        elif 17 <= hour_of_day < 20:  # Evening peak
            base_demand = 2600 + (hour_of_day - 17) * 60 + np.random.normal(0, 90)
        else:  # Night
            base_demand = 2200 - (hour_of_day - 20) * 50 + np.random.normal(0, 60)
        
        # Add some realistic variation
        demand = max(1800, min(3000, base_demand))  # Clamp to realistic range
        
        data_points.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'demand_mw': round(demand, 2),
            'hour': hour_of_day,
            'day_of_week': timestamp.weekday(),
            'month': 11
        })
    
    print(f"✅ Generated {len(data_points)} November forecast points")
    print(f"   Range: {min(p['demand_mw'] for p in data_points):.0f} - {max(p['demand_mw'] for p in data_points):.0f} MW")
    
    return data_points


def add_sample_anomaly(data_points):
    """Add one realistic November anomaly to test detection"""
    print("\n🔴 Adding sample November anomaly...")
    
    # Find evening peak hour (around 6-7 PM)
    for i, point in enumerate(data_points):
        hour = datetime.strptime(point['timestamp'], '%Y-%m-%d %H:%M:%S').hour
        if hour == 18:  # 6 PM
            # Create an unusually high demand spike for November
            original_demand = point['demand_mw']
            point['demand_mw'] = 3850.0  # Way above normal November peak
            point['_is_test_anomaly'] = True
            point['_original_demand'] = original_demand
            
            print(f"   📍 Injected at: {point['timestamp']}")
            print(f"   📊 Changed: {original_demand:.0f} → {point['demand_mw']:.0f} MW")
            print(f"   💡 Scenario: Unexpected cold snap + major event")
            break
    
    return data_points


def prepare_features(data_points, feature_columns):
    """Prepare features matching the November model's expectations"""
    print("\n🔧 Preparing features...")
    
    df = pd.DataFrame(data_points)
    
    # Add time-based features that the model expects
    df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp_dt'].dt.hour
    df['day_of_week'] = df['timestamp_dt'].dt.dayofweek
    df['month'] = df['timestamp_dt'].dt.month
    df['day'] = df['timestamp_dt'].dt.day
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Add rolling statistics (using same window as original training)
    df['demand_rolling_mean_6h'] = df['demand_mw'].rolling(window=6, min_periods=1).mean()
    df['demand_rolling_std_6h'] = df['demand_mw'].rolling(window=6, min_periods=1).std().fillna(0)
    df['demand_rolling_min_6h'] = df['demand_mw'].rolling(window=6, min_periods=1).min()
    df['demand_rolling_max_6h'] = df['demand_mw'].rolling(window=6, min_periods=1).max()
    
    # Add lag features
    df['demand_lag_1h'] = df['demand_mw'].shift(1).fillna(df['demand_mw'].iloc[0])
    df['demand_lag_2h'] = df['demand_mw'].shift(2).fillna(df['demand_mw'].iloc[0])
    df['demand_lag_24h'] = df['demand_mw'].shift(24).fillna(df['demand_mw'].iloc[0])
    
    # Rate of change
    df['demand_rate_of_change'] = df['demand_mw'].diff().fillna(0)
    df['demand_rate_of_change_pct'] = df['demand_mw'].pct_change().fillna(0) * 100
    
    # Ensure all required features exist
    for col in feature_columns:
        if col not in df.columns:
            print(f"   ⚠️  Missing feature: {col}, filling with default")
            df[col] = 0
    
    print(f"✅ Features prepared: {len(feature_columns)} columns")
    
    return df


def run_november_model(data_points, model, scaler, info):
    """Run November model on the mock data"""
    print("\n🤖 Running November anomaly detection model...")
    
    feature_columns = info['feature_columns']
    df = prepare_features(data_points, feature_columns)
    
    # Extract features
    X = df[feature_columns].values
    
    # Scale features
    X_scaled = scaler.transform(X)
    
    # Predict anomalies
    predictions = model.predict(X_scaled)
    anomaly_scores = model.score_samples(X_scaled)
    
    # Add results back to dataframe
    df['is_anomaly'] = (predictions == -1)
    df['anomaly_score'] = anomaly_scores
    
    # Determine severity based on anomaly score
    df['severity'] = 'normal'
    df.loc[df['is_anomaly'], 'severity'] = 'medium'
    
    # High severity for very negative scores
    df.loc[(df['is_anomaly']) & (df['anomaly_score'] < -0.5), 'severity'] = 'high'
    
    # Critical for extreme scores
    df.loc[(df['is_anomaly']) & (df['anomaly_score'] < -0.8), 'severity'] = 'critical'
    
    # Calculate confidence (convert score to 0-100 scale)
    df['confidence'] = np.abs(df['anomaly_score']) * 100
    df['confidence'] = df['confidence'].clip(0, 100)
    
    anomaly_count = df['is_anomaly'].sum()
    anomaly_rate = (anomaly_count / len(df)) * 100
    
    print(f"\n📊 Detection Results:")
    print(f"   Total points: {len(df)}")
    print(f"   Anomalies detected: {anomaly_count}")
    print(f"   Anomaly rate: {anomaly_rate:.1f}%")
    
    if anomaly_count > 0:
        print(f"\n🔴 Detected Anomalies:")
        for idx, row in df[df['is_anomaly']].iterrows():
            timestamp = row['timestamp']
            demand = row['demand_mw']
            severity = row['severity']
            confidence = row['confidence']
            is_test = row.get('_is_test_anomaly', False)
            marker = "🧪 TEST" if is_test else "🔍 REAL"
            print(f"   {marker} {timestamp} - {demand:.0f} MW ({severity.upper()}, {confidence:.1f}% confidence)")
    
    return df


def save_mock_predictions(df):
    """Save mock November predictions to JSON"""
    print("\n💾 Saving mock November predictions...")
    
    # Prepare output format
    predictions = []
    for _, row in df.iterrows():
        pred = {
            "timestamp": row['timestamp'],
            "demand_mw": float(row['demand_mw']),
            "is_anomaly": bool(row['is_anomaly']),
            "anomaly_score": float(row['anomaly_score']),
            "severity": row['severity'],
            "confidence": float(row['confidence']),
            "explanation": "Mock November forecast data for testing"
        }
        
        if row.get('_is_test_anomaly'):
            pred['explanation'] = "Simulated November anomaly: Unexpected cold snap causing heating surge"
            pred['predicted_demand'] = float(row['_original_demand'])
        
        predictions.append(pred)
    
    output = {
        "generated_at": datetime.now().isoformat(),
        "model_type": "november_mock_test",
        "model_month": "november",
        "forecast_period": f"{df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}",
        "total_points": len(predictions),
        "anomalies_detected": int(df['is_anomaly'].sum()),
        "anomaly_rate": float((df['is_anomaly'].sum() / len(df)) * 100),
        "predictions": predictions
    }
    
    # Save to file
    output_path = Path(__file__).parent / "models" / "predictions" / "november_mock_predictions.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved to: {output_path.name}")
    
    return output_path


def main():
    print("\n" + "="*70)
    print("🧪 GENERATING MOCK NOVEMBER DATA")
    print("="*70)
    
    # Load November model
    model, scaler, info = load_november_model()
    
    # Generate realistic November demand patterns
    data_points = generate_november_demand_pattern()
    
    # Add one sample anomaly for testing
    data_points = add_sample_anomaly(data_points)
    
    # Run November model on mock data
    results_df = run_november_model(data_points, model, scaler, info)
    
    # Save predictions
    output_path = save_mock_predictions(results_df)
    
    print("\n" + "="*70)
    print("✅ MOCK NOVEMBER DATA GENERATION COMPLETE")
    print("="*70)
    print("\n💡 Next Steps:")
    print("   1. Review the predictions in: november_mock_predictions.json")
    print("   2. Copy to november_predictions.json to test dashboard:")
    print("      Copy-Item november_mock_predictions.json november_predictions.json")
    print("   3. Mock November 1st by temporarily changing system date")
    print("   4. Dashboard will show November model with realistic data!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
