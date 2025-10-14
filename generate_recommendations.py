"""
Generate Smart Recommendations for LADWP Grid Operations
Phase 3 - Combines ML predictions with price forecasts
"""

import json
import os
from datetime import datetime
import pandas as pd

from recommendation_engine import RecommendationEngine
from price_forecast import PriceForecast


def load_current_predictions(month: int = None) -> list:
    """
    Load the current month's predictions.
    
    Args:
        month: Month number (1-12). If None, uses current month.
        
    Returns:
        List of prediction dicts
    """
    if month is None:
        month = datetime.now().month
    
    month_names = [
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december'
    ]
    
    prediction_file = f'models/predictions/{month_names[month-1]}_predictions.json'
    
    if not os.path.exists(prediction_file):
        raise FileNotFoundError(f"Prediction file not found: {prediction_file}")
    
    with open(prediction_file, 'r') as f:
        data = json.load(f)
    
    return data['predictions']


def get_current_demand() -> float:
    """
    Get current demand from latest data point.
    In production, this would query real-time SCADA/CAISO data.
    
    Returns:
        Current demand in MW
    """
    # For now, use the latest prediction as proxy
    predictions = load_current_predictions()
    if predictions:
        return predictions[0]['demand_mw']
    return 1000.0  # Default fallback


def get_battery_status() -> float:
    """
    Get current battery state of charge.
    In production, this would query battery management system.
    
    Returns:
        Battery SOC (0-1)
    """
    # Simulated - in production this would be real data
    # Typically batteries are kept at 50-60% for flexibility
    return 0.55


def generate_and_save_recommendations(output_path: str = 'data/recommendations.json'):
    """
    Generate recommendations and save to JSON file.
    
    Args:
        output_path: Path to save recommendations JSON
    """
    print("🔮 Generating Smart Recommendations...")
    print("="*70)
    
    # Step 1: Load predictions
    print("\n1️⃣  Loading ML predictions...")
    predictions = load_current_predictions()
    current_month = datetime.now().strftime('%B')
    print(f"   ✅ Loaded {len(predictions)} predictions for {current_month}")
    
    # Step 2: Generate price forecast
    print("\n2️⃣  Generating price forecast...")
    price_forecaster = PriceForecast(volatility=0.12)
    price_forecast = price_forecaster.generate_forecast(hours=48)
    print(f"   ✅ Generated 48-hour price forecast")
    
    # Step 3: Get current system status
    print("\n3️⃣  Getting current system status...")
    current_demand = get_current_demand()
    battery_soc = get_battery_status()
    print(f"   ✅ Current demand: {current_demand:.1f} MW")
    print(f"   ✅ Battery SOC: {battery_soc*100:.0f}%")
    
    # Step 4: Generate recommendations
    print("\n4️⃣  Running recommendation engine...")
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(
        predictions=predictions,
        price_forecast=price_forecast,
        current_demand=current_demand,
        battery_soc=battery_soc
    )
    print(f"   ✅ Generated {len(recommendations)} recommendations")
    
    # Step 5: Calculate total potential value
    total_savings = sum(rec['estimated_savings'] for rec in recommendations)
    high_priority_count = sum(1 for rec in recommendations if rec['priority'] == 'HIGH')
    
    print("\n5️⃣  Summary Statistics:")
    print(f"   💰 Total Potential Savings: ${total_savings:,.2f}")
    print(f"   🔴 High Priority Actions: {high_priority_count}")
    if recommendations:
        print(f"   📊 Average Confidence: {sum(rec['confidence'] for rec in recommendations)/len(recommendations)*100:.1f}%")
    else:
        print(f"   📊 Average Confidence: N/A (no recommendations)")
    
    # Step 6: Save to file
    print(f"\n6️⃣  Saving recommendations to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'current_demand_mw': current_demand,
        'battery_soc': battery_soc,
        'total_recommendations': len(recommendations),
        'total_potential_savings': total_savings,
        'high_priority_count': high_priority_count,
        'recommendations': recommendations
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"   ✅ Recommendations saved successfully")
    
    # Step 7: Display top recommendations
    print("\n" + "="*70)
    print("🎯 TOP RECOMMENDATIONS")
    print("="*70)
    
    for i, rec in enumerate(recommendations[:5], 1):
        priority_symbol = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
        action_symbol = {
            'DEMAND_RESPONSE': '📉',
            'BATTERY_DISCHARGE': '🔋',
            'BATTERY_CHARGE': '⚡',
            'LOAD_SHIFT': '🔄',
            'MAINTENANCE_CHECK': '🔧',
            'PRICE_ARBITRAGE': '💰'
        }
        
        print(f"\n{i}. {priority_symbol.get(rec['priority'], '⚪')} {rec['title']} {action_symbol.get(rec['action'], '')}")
        print(f"   Reason: {rec['reason']}")
        print(f"   Action: {rec['details']}")
        print(f"   When: {rec['time_window']}")
        print(f"   💰 Savings: ${rec['estimated_savings']:,.2f}")
        print(f"   ✓ Confidence: {rec['confidence']*100:.0f}%")
    
    print("\n" + "="*70)
    print("✅ Recommendation generation complete!")
    print(f"📂 View full details in: {output_path}")
    print("="*70)
    
    return recommendations


if __name__ == "__main__":
    # Generate recommendations
    recommendations = generate_and_save_recommendations()
    
    print(f"\n🚀 Next steps:")
    print(f"   1. Review recommendations in the dashboard")
    print(f"   2. Implement high-priority actions")
    print(f"   3. Track actual savings vs estimates")
    print(f"   4. Re-run hourly or when conditions change")
