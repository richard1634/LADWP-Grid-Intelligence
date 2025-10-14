"""
RETRAIN ALL MODELS WITH CORRECT DATA
====================================
This script retrains all ML models with the correct LADWP scale data (2,500 MW avg)
"""
import subprocess
import sys

print("=" * 80)
print("RETRAINING PIPELINE")
print("=" * 80)

# Step 1: Verify database
print("\n[1/4] Verifying database...")
result = subprocess.run([sys.executable, "db_check.py"], capture_output=True, text=True)
print(result.stdout)
if "DATABASE READY" not in result.stdout:
    print("❌ Database verification failed!")
    sys.exit(1)

# Step 2: Retrain baseline patterns
print("\n[2/4] Retraining baseline patterns...")
result = subprocess.run([sys.executable, "models/baseline_patterns.py"], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"❌ Error: {result.stderr}")
    sys.exit(1)

# Step 3: Retrain anomaly detector
print("\n[3/4] Retraining anomaly detector...")
result = subprocess.run([sys.executable, "models/anomaly_detector.py"], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"❌ Error: {result.stderr}")
    sys.exit(1)

# Step 4: Generate future predictions
print("\n[4/4] Generating future anomaly predictions...")
result = subprocess.run([sys.executable, "models/future_anomaly_predictor.py"], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"❌ Error: {result.stderr}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL MODELS RETRAINED SUCCESSFULLY!")
print("=" * 80)
print("\nNext step: Visualize predictions")
print("Run: python visualize_future_anomalies.py")
