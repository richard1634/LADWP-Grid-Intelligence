"""
FastAPI server for LADWP Grid Intelligence Dashboard
Exposes existing Python logic as REST API for React frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from pathlib import Path
import json
import pytz
import pandas as pd

# Import existing modules
from caiso_api_client import (
    CAISOClient,
    calculate_price_volatility,
    detect_price_spikes,
    calculate_grid_stress_score
)

app = FastAPI(title="LADWP Grid Intelligence API", version="2.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize CAISO client
client = CAISOClient()

@app.get("/")
async def root():
    return {
        "message": "LADWP Grid Intelligence API",
        "version": "2.0.0",
        "status": "operational"
    }

@app.get("/api/grid-status")
async def get_grid_status():
    """Get current grid status with all metrics"""
    try:
        # Get current demand
        demand_df = client.get_system_demand()
        price_df = client.get_real_time_prices()
        
        if demand_df is None or demand_df.empty:
            raise HTTPException(status_code=503, detail="Unable to fetch demand data")
        
        # Calculate metrics
        current_demand = demand_df['MW'].iloc[-1] if 'MW' in demand_df.columns else 0
        avg_demand = demand_df['MW'].mean() if 'MW' in demand_df.columns else 0
        
        current_price = 0
        avg_price = 0
        price_delta = 0
        
        if price_df is not None and not price_df.empty and 'LMP_PRC' in price_df.columns:
            current_price = price_df['LMP_PRC'].iloc[-1]
            avg_price = price_df['LMP_PRC'].mean()
            price_delta = current_price - avg_price
        
        # Calculate grid stress
        stress = calculate_grid_stress_score(float(current_demand), float(avg_price))
        
        return {
            "success": True,
            "data": {
                "demand_mw": float(current_demand),
                "demand_trend": float(current_demand - avg_demand),
                "avg_price_per_mwh": float(avg_price),
                "price_delta": float(price_delta),
                "stress": stress,
                "timestamp": datetime.now(pytz.timezone('America/Los_Angeles')).isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/demand-forecast")
async def get_demand_forecast(date: str = None):
    """Get 48-hour demand forecast (historical + future predictions)"""
    try:
        if date:
            selected_date = datetime.fromisoformat(date)
            demand_df = client.get_system_demand(date=selected_date)
        else:
            demand_df = client.get_system_demand()
        
        if demand_df is None or demand_df.empty:
            raise HTTPException(status_code=503, detail="Unable to fetch demand forecast")
        
        # Ensure we have timestamp column
        if 'timestamp' not in demand_df.columns:
            if 'INTERVAL_START_GMT' in demand_df.columns:
                demand_df['timestamp'] = pd.to_datetime(demand_df['INTERVAL_START_GMT']).dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('America/Los_Angeles'))
            elif 'INTERVALSTARTTIME_GMT' in demand_df.columns:
                demand_df['timestamp'] = pd.to_datetime(demand_df['INTERVALSTARTTIME_GMT']).dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('America/Los_Angeles'))
            else:
                raise HTTPException(status_code=500, detail="No timestamp column found in data")
        
        # Sort by timestamp
        demand_df = demand_df.sort_values('timestamp')
        
        # Mark which data points are forecasts vs historical
        current_time = datetime.now(pytz.timezone('America/Los_Angeles'))
        demand_df['is_forecast'] = demand_df['timestamp'] > current_time
        
        # Filter to LADWP area if available
        if 'TAC_AREA_NAME' in demand_df.columns:
            # Get LADWP or first available area
            ladwp_data = demand_df[demand_df['TAC_AREA_NAME'].str.contains('LADWP', case=False, na=False)]
            if not ladwp_data.empty:
                demand_df = ladwp_data
            else:
                # Use first available area
                first_area = demand_df['TAC_AREA_NAME'].iloc[0]
                demand_df = demand_df[demand_df['TAC_AREA_NAME'] == first_area]
        
        # Convert to JSON-serializable format
        records = []
        for _, row in demand_df.iterrows():
            record = {
                "timestamp": row['timestamp'].isoformat(),
                "demand_mw": float(row['MW']) if 'MW' in row else 0,
                "is_forecast": bool(row['is_forecast']),
                "area": row.get('TAC_AREA_NAME', 'LADWP')
            }
            records.append(record)
        
        return {
            "success": True,
            "data": records,
            "count": len(records)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/prices")
async def get_prices(hours_back: int = 6):
    """Get real-time price data with spike detection"""
    try:
        price_df = client.get_real_time_prices(hours_back=hours_back)
        
        if price_df is None or price_df.empty:
            raise HTTPException(status_code=503, detail="Unable to fetch price data")
        
        # Ensure timestamp column exists
        if 'timestamp' not in price_df.columns:
            if 'INTERVALSTARTTIME_GMT' in price_df.columns:
                price_df['timestamp'] = pd.to_datetime(price_df['INTERVALSTARTTIME_GMT']).dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('America/Los_Angeles'))
            elif 'INTERVAL_START_GMT' in price_df.columns:
                price_df['timestamp'] = pd.to_datetime(price_df['INTERVAL_START_GMT']).dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('America/Los_Angeles'))
        
        # Sort by timestamp
        price_df = price_df.sort_values('timestamp')
        
        # Filter to LADWP nodes if available
        if 'NODE' in price_df.columns:
            # Get LADWP-related nodes
            ladwp_mask = price_df['NODE'].str.contains('LADWP', case=False, na=False)
            if ladwp_mask.any():
                price_df = price_df[ladwp_mask]
        
        # Group by timestamp and average prices across all nodes
        # This gives us one clean price per time interval
        if 'timestamp' in price_df.columns and len(price_df) > 0:
            # Build aggregation dict based on available columns
            agg_dict = {'LMP_PRC': 'mean'}
            if 'LMP_CONG_PRC' in price_df.columns:
                agg_dict['LMP_CONG_PRC'] = 'mean'
            if 'LMP_ENE_PRC' in price_df.columns:
                agg_dict['LMP_ENE_PRC'] = 'mean'
            if 'LMP_LOSS_PRC' in price_df.columns:
                agg_dict['LMP_LOSS_PRC'] = 'mean'
            
            grouped = price_df.groupby('timestamp').agg(agg_dict).reset_index()
            
            # Detect price spikes on the averaged data
            spikes_df = detect_price_spikes(grouped, threshold_std=2.5)
            spike_timestamps = set(spikes_df['timestamp'].values) if not spikes_df.empty else set()
            
            # Convert to JSON-serializable format
            records = []
            for _, row in grouped.iterrows():
                is_spike = row['timestamp'] in spike_timestamps
                record = {
                    "timestamp": row['timestamp'].isoformat(),
                    "price": float(row['LMP_PRC']),
                    "congestion": float(row.get('LMP_CONG_PRC', 0)),
                    "energy": float(row.get('LMP_ENE_PRC', 0)),
                    "loss": float(row.get('LMP_LOSS_PRC', 0)),
                    "node": "LADWP (averaged)",
                    "is_spike": bool(is_spike)
                }
                records.append(record)
        else:
            records = []
        
        return {
            "success": True,
            "data": records,
            "count": len(records)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml-predictions")
async def get_ml_predictions(month: str = None):
    """Get ML anomaly predictions for current/specified month"""
    try:
        if not month:
            month = datetime.now().strftime('%B').lower()
        
        predictions_file = Path(__file__).parent / "models" / "predictions" / f"{month}_predictions.json"
        
        if not predictions_file.exists():
            predictions_file = Path(__file__).parent / "models" / "predictions" / "latest_predictions.json"
        
        if not predictions_file.exists():
            return {
                "success": False,
                "data": None,
                "message": "Predictions not available"
            }
        
        with open(predictions_file, 'r') as f:
            predictions = json.load(f)
        
        return {
            "success": True,
            "data": predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
async def get_recommendations(month: str = None):
    """Get smart recommendations based on anomalies from ML predictions"""
    try:
        if not month:
            month = datetime.now().strftime('%B').lower()
        
        # Load ML predictions file (same source as /api/ml-predictions)
        predictions_file = Path(__file__).parent / "models" / "predictions" / f"{month}_predictions.json"
        
        if not predictions_file.exists():
            predictions_file = Path(__file__).parent / "models" / "predictions" / "latest_predictions.json"
        
        if not predictions_file.exists():
            return {
                "success": False,
                "data": None,
                "message": "Predictions not available"
            }
        
        with open(predictions_file, 'r') as f:
            predictions = json.load(f)
        
        # Extract anomalies from predictions
        anomalies = [p for p in predictions.get('predictions', []) 
                    if p.get('is_anomaly') or p.get('severity') != 'normal']
        
        # Generate recommendations from anomalies
        recommendations = []
        for anomaly in anomalies:
            rec = {
                "timestamp": anomaly.get('timestamp'),
                "anomaly": {
                    "timestamp": anomaly.get('timestamp'),
                    "demand_mw": anomaly.get('demand_mw'),
                    "severity": anomaly.get('severity', 'medium'),
                    "confidence": anomaly.get('confidence', 0.0)
                },
                "analysis": {
                    "anomaly_type": "demand_spike" if anomaly.get('demand_mw', 0) > 2500 else "demand_drop",
                    "root_causes": ["Detected by ML model"],
                    "context": f"Anomaly detected with {anomaly.get('confidence', 0)*100:.1f}% confidence"
                },
                "recommendation": {
                    "priority": "high" if anomaly.get('confidence', 0) > 0.8 else "medium",
                    "urgency": "immediate" if anomaly.get('confidence', 0) > 0.9 else "normal",
                    "title": f"Investigate {anomaly.get('severity', 'medium')} severity anomaly",
                    "why": "ML model detected unusual demand pattern",
                    "actions": [
                        "Monitor system stability",
                        "Check for external factors",
                        "Review operational logs"
                    ],
                    "impact": "Medium operational risk"
                }
            }
            recommendations.append(rec)
        
        result = {
            "generated_at": predictions.get('generated_at'),
            "month": predictions.get('model_month', month),
            "total_anomalies": len(anomalies),
            "recommendations": recommendations
        }
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint for old recommendation files
@app.get("/api/recommendations/legacy")
async def get_legacy_recommendations(month: str = None):
    """Get recommendations from old anomaly_recommendations.json files"""
    try:
        if not month:
            month = datetime.now().strftime('%B').lower()
        
        rec_file = Path(__file__).parent / "data" / f"{month}_anomaly_recommendations.json"
        
        if not rec_file.exists():
            rec_file = Path(__file__).parent / "data" / "anomaly_recommendations.json"
        
        if not rec_file.exists():
            return {
                "success": False,
                "data": None,
                "message": "Recommendations not available"
            }
        
        with open(rec_file, 'r') as f:
            recommendations = json.load(f)
        
        return {
            "success": True,
            "data": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(pytz.timezone('America/Los_Angeles')).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LADWP Grid Intelligence API Server...")
    print("📊 Backend: Python + FastAPI")
    print("🎨 Frontend: React + TypeScript")
    print("🌐 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
