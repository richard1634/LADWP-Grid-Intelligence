"""
FastAPI server for LADWP Grid Intelligence Dashboard
Exposes existing Python logic as REST API for React frontend
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from pathlib import Path
import json
import pytz
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import existing modules
from caiso_api_client import (
    CAISOClient,
    calculate_price_volatility,
    detect_price_spikes,
    calculate_grid_stress_score
)
from llm_recommendation_engine import LLMRecommendationEngine

app = FastAPI(title="LADWP Grid Intelligence API", version="2.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:5175",
        "https://*.onrender.com",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app",
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
    """Get demand data: last 24 hours historical + 30 hours CAISO forecast"""
    try:
        if date:
            selected_date = datetime.fromisoformat(date)
            demand_df = client.get_system_demand(date=selected_date, hours_ahead=54)
        else:
            # Get 54 hours from start of day (catches last 24h historical + 30h forecast)
            demand_df = client.get_system_demand(hours_ahead=54)
        
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
        
        # Filter to last 24 hours of historical + all future forecasts
        cutoff_time = current_time - timedelta(hours=24)
        demand_df = demand_df[demand_df['timestamp'] >= cutoff_time]
        
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

def _generate_fallback_recommendations(anomalies: list) -> list:
    """Generate simple fallback recommendations when LLM is not available"""
    recommendations = []
    
    for anomaly in anomalies[:5]:  # Limit to top 5 anomalies
        demand = anomaly.get('demand_mw', 0)
        predicted = anomaly.get('predicted_demand', demand)
        confidence = anomaly.get('confidence', 0.0)
        severity = anomaly.get('severity', 'medium')
        
        # Format timestamp
        ts = anomaly.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            time_str = dt.strftime('%I:%M %p')
            date_str = dt.strftime('%b %d, %Y')
        except:
            time_str = "Unknown"
            date_str = "Unknown"
        
        # Determine priority and create recommendation
        is_spike = demand > predicted if predicted else demand > 6000
        priority = "HIGH" if confidence > 80 or demand > 7000 else "MEDIUM"
        
        rec = {
            "timestamp": ts,
            "anomaly": {
                "timestamp": ts,
                "demand_mw": demand,
                "severity": severity,
                "confidence": confidence,
                "time_str": time_str,
                "date_str": date_str
            },
            "analysis": {
                "source": "rule-based",
                "model": "fallback",
                "generated_at": datetime.now().isoformat()
            },
            "recommendation": {
                "priority": priority,
                "urgency": "immediate" if demand > 7000 else "normal",
                "title": f"{'🚨' if priority == 'HIGH' else '⚠️'} Demand Anomaly Detected - {demand:,.0f} MW",
                "why": f"Demand of {demand:,.0f} MW {'significantly exceeds' if is_spike else 'is below'} predicted level of {predicted:,.0f} MW.",
                "actions": [
                    {
                        "icon": "🔍",
                        "action": "Verify Data Accuracy",
                        "details": "Confirm reading with SCADA systems",
                        "timeframe": "Immediately"
                    },
                    {
                        "icon": "⚡",
                        "action": "Assess Grid Stability",
                        "details": "Check substation loading and voltage levels",
                        "timeframe": "Within 5 minutes"
                    }
                ],
                "impact": {
                    "financial": f"Estimated ${abs(demand - predicted) * 50:,.0f}/hour impact",
                    "financial_type": "high_cost" if is_spike else "potential_savings",
                    "reliability_risk": "HIGH" if demand > 7000 else "MEDIUM",
                    "magnitude_mw": abs(demand - predicted),
                    "duration_estimate": "Unknown"
                },
                "confidence": confidence,
                "time_sensitive": demand > 7000
            }
        }
        recommendations.append(rec)
    
    return recommendations

@app.get("/api/recommendations")
async def get_recommendations(month: str = None, use_llm: bool = False):
    """Get AI-powered smart recommendations based on grid data and ML predictions"""
    try:
        if not month:
            month = datetime.now().strftime('%B').lower()
        
        # Load ML predictions file
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
            predictions_data = json.load(f)
        
        # Extract predictions and anomalies
        predictions_list = predictions_data.get('predictions', [])
        anomalies = [p for p in predictions_list 
                    if p.get('is_anomaly') or p.get('severity') != 'normal']
        
        # Get current demand (use average from predictions as proxy)
        current_demand = sum(p.get('demand_mw', 0) for p in predictions_list[:10]) / min(len(predictions_list), 10)
        
        # Get price forecast (try to load or use placeholder)
        price_forecast = []
        try:
            price_df = client.get_real_time_prices(hours_back=6)
            if price_df is not None and not price_df.empty:
                # Convert to list of dicts
                for _, row in price_df.iterrows():
                    price_forecast.append({
                        'timestamp': row.get('timestamp', datetime.now()).isoformat() if 'timestamp' in row else datetime.now().isoformat(),
                        'price_per_mwh': float(row.get('LMP_PRC', 50.0))
                    })
        except:
            # Use placeholder if price fetch fails
            for i in range(24):
                price_forecast.append({
                    'timestamp': (datetime.now() + timedelta(hours=i)).isoformat(),
                    'price_per_mwh': 50.0
                })
        
        # Generate recommendations using LLM or fallback
        if use_llm and os.getenv("OPENAI_API_KEY"):
            try:
                llm_engine = LLMRecommendationEngine()
                recommendations = llm_engine.generate_recommendations(
                    predictions=predictions_list,
                    price_forecast=price_forecast,
                    current_demand=current_demand,
                    anomalies=anomalies
                )
            except Exception as llm_error:
                print(f"LLM generation failed: {llm_error}")
                # Fall back to simple recommendations
                recommendations = _generate_fallback_recommendations(anomalies)
        else:
            # Use fallback if LLM not configured
            recommendations = _generate_fallback_recommendations(anomalies)
        
        # Count priorities
        high_priority = sum(1 for r in recommendations if r.get('recommendation', {}).get('priority') == 'HIGH')
        medium_priority = sum(1 for r in recommendations if r.get('recommendation', {}).get('priority') == 'MEDIUM')
        low_priority = sum(1 for r in recommendations if r.get('recommendation', {}).get('priority') == 'LOW')
        
        result = {
            "generated_at": predictions_data.get('generated_at'),
            "month": predictions_data.get('model_month', month),
            "total_anomalies": len(anomalies),
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "recommendations": recommendations,
            "llm_powered": use_llm and os.getenv("OPENAI_API_KEY") is not None
        }
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-anomaly-recommendation")
async def generate_anomaly_recommendation(request: Request):
    """Generate AI-powered recommendation for a single anomaly"""
    try:
        body = await request.json()
        anomaly = body.get('anomaly')
        
        if not anomaly:
            raise HTTPException(status_code=400, detail="Anomaly data required")
        
        # Get current demand context
        current_demand = anomaly.get('demand_mw', 3000.0)
        predicted_demand = anomaly.get('predicted_demand', current_demand * 0.9)
        
        # Get price forecast context
        price_forecast = []
        try:
            price_df = client.get_real_time_prices(hours_back=6)
            if price_df is not None and not price_df.empty:
                for _, row in price_df.iterrows():
                    price_forecast.append({
                        'timestamp': row.get('timestamp', datetime.now()).isoformat() if 'timestamp' in row else datetime.now().isoformat(),
                        'price_per_mwh': float(row.get('LMP_PRC', 50.0))
                    })
        except:
            # Use placeholder if price fetch fails
            for i in range(24):
                price_forecast.append({
                    'timestamp': (datetime.now() + timedelta(hours=i)).isoformat(),
                    'price_per_mwh': 50.0
                })
        
        # Check if API key is configured
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"
            )
        
        # Generate LLM recommendation
        try:
            llm_engine = LLMRecommendationEngine()
            
            # Create predictions context (just this anomaly with some normal values for context)
            predictions_context = [anomaly]
            for i in range(5):
                predictions_context.append({
                    'timestamp': (datetime.now() + timedelta(hours=i+1)).isoformat(),
                    'demand_mw': predicted_demand,
                    'is_anomaly': False
                })
            
            recommendations = llm_engine.generate_recommendations(
                predictions=predictions_context,
                price_forecast=price_forecast,
                current_demand=current_demand,
                anomalies=[anomaly]  # Single anomaly
            )
            
            # Return just the first recommendation (for this anomaly)
            if recommendations and len(recommendations) > 0:
                rec = recommendations[0].get('recommendation', {})
                return {
                    "success": True,
                    "data": rec
                }
            else:
                raise Exception("No recommendation generated")
                
        except Exception as llm_error:
            print(f"LLM generation failed: {llm_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate AI recommendation: {str(llm_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating recommendation: {e}")
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
    import os
    
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting LADWP Grid Intelligence API Server...")
    print("📊 Backend: Python + FastAPI")
    print("🎨 Frontend: React + TypeScript")
    print(f"🌐 API: http://localhost:{port}")
    print(f"📚 Docs: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
