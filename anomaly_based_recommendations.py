"""
Anomaly-Based Recommendation Engine for LADWP Grid Intelligence
Generates specific recommendations for each detected anomaly with root cause analysis
"""

import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


class AnomalyAnalyzer:
    """
    Analyzes detected anomalies and generates specific recommendations.
    Links each anomaly to its root cause and actionable response.
    """
    
    def __init__(self):
        self.analysis_history = []
    
    def analyze_anomaly(
        self, 
        anomaly: Dict[str, Any],
        price_data: Dict[str, float],
        historical_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a single anomaly and generate recommendation.
        
        Args:
            anomaly: Dict with timestamp, demand_mw, severity, confidence
            price_data: Price info at anomaly time
            historical_pattern: Historical averages for context
            
        Returns:
            Dict with analysis and recommendation
        """
        timestamp = pd.to_datetime(anomaly['timestamp'])
        demand_mw = anomaly['demand_mw']
        severity = anomaly.get('severity', 'medium')
        confidence = anomaly.get('confidence', 0.5)
        
        # Determine anomaly type and root cause
        analysis = self._diagnose_anomaly(
            timestamp=timestamp,
            demand_mw=demand_mw,
            price_data=price_data,
            historical_pattern=historical_pattern
        )
        
        # Generate specific recommendation based on diagnosis
        recommendation = self._generate_recommendation(
            analysis=analysis,
            severity=severity,
            confidence=confidence,
            price_data=price_data
        )
        
        return {
            'anomaly': {
                'timestamp': timestamp.isoformat(),
                'demand_mw': demand_mw,
                'severity': severity,
                'confidence': confidence,
                'time_str': timestamp.strftime('%I:%M %p'),
                'date_str': timestamp.strftime('%b %d, %Y')
            },
            'analysis': analysis,
            'recommendation': recommendation
        }
    
    def _diagnose_anomaly(
        self,
        timestamp: datetime,
        demand_mw: float,
        price_data: Dict[str, float],
        historical_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Diagnose the root cause of the anomaly."""
        
        hour = timestamp.hour
        day_of_week = timestamp.strftime('%A')
        
        # Get expected demand for this time
        expected_demand = historical_pattern.get('hourly_avg', {}).get(hour, demand_mw * 0.9)
        deviation_pct = ((demand_mw - expected_demand) / expected_demand) * 100
        
        # Determine anomaly type
        if demand_mw > expected_demand:
            anomaly_type = "UNEXPECTED_SPIKE"
            direction = "above"
        else:
            anomaly_type = "UNEXPECTED_DROP"
            direction = "below"
        
        # Identify potential root causes
        root_causes = []
        contributing_factors = []
        
        # Time-based analysis
        if 14 <= hour <= 20:
            root_causes.append("Peak Hour Irregularity")
            contributing_factors.append(f"Occurred during typical peak period ({hour}:00)")
        elif 0 <= hour <= 5:
            root_causes.append("Off-Peak Abnormality")
            contributing_factors.append(f"Unusual activity during low-demand period ({hour}:00)")
        
        # Magnitude analysis
        if abs(deviation_pct) > 20:
            root_causes.append("Significant Load Deviation")
            contributing_factors.append(f"{abs(deviation_pct):.1f}% deviation from expected {expected_demand:.0f} MW")
        elif abs(deviation_pct) > 10:
            root_causes.append("Moderate Load Variation")
            contributing_factors.append(f"{abs(deviation_pct):.1f}% deviation from typical pattern")
        
        # Price correlation
        current_price = price_data.get('price_per_mwh', 100)
        if current_price > 150 and anomaly_type == "UNEXPECTED_SPIKE":
            root_causes.append("High Price + High Demand Event")
            contributing_factors.append(f"Elevated prices (${current_price:.2f}/MWh) concurrent with demand spike")
        elif current_price < 80 and anomaly_type == "UNEXPECTED_DROP":
            root_causes.append("Low Price Period with Reduced Load")
            contributing_factors.append(f"Low prices (${current_price:.2f}/MWh) with unexpected demand reduction")
        
        # Weather/event inference (based on magnitude and time)
        if anomaly_type == "UNEXPECTED_SPIKE" and abs(deviation_pct) > 15:
            if 12 <= hour <= 18:
                root_causes.append("Possible Weather-Driven Event")
                contributing_factors.append("Afternoon spike suggests potential heat wave or cooling demand")
            elif hour < 8:
                root_causes.append("Possible Industrial/Commercial Event")
                contributing_factors.append("Early morning spike suggests large facility startup")
        
        # Day of week patterns
        if day_of_week in ['Saturday', 'Sunday']:
            contributing_factors.append(f"Weekend anomaly on {day_of_week}")
        
        # Determine primary diagnosis
        primary_diagnosis = root_causes[0] if root_causes else "Unclassified Anomaly"
        
        return {
            'anomaly_type': anomaly_type,
            'primary_diagnosis': primary_diagnosis,
            'root_causes': root_causes,
            'contributing_factors': contributing_factors,
            'deviation_pct': deviation_pct,
            'expected_demand': expected_demand,
            'actual_demand': demand_mw,
            'direction': direction,
            'current_price': current_price
        }
    
    def _generate_recommendation(
        self,
        analysis: Dict[str, Any],
        severity: str,
        confidence: float,
        price_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate actionable recommendation based on analysis."""
        
        anomaly_type = analysis['anomaly_type']
        primary_diagnosis = analysis['primary_diagnosis']
        deviation_pct = analysis['deviation_pct']
        current_price = analysis['current_price']
        
        # Determine priority
        if severity == 'high' or abs(deviation_pct) > 20:
            priority = 'HIGH'
            urgency = 'Immediate action required'
        elif severity == 'medium' or abs(deviation_pct) > 10:
            priority = 'MEDIUM'
            urgency = 'Action recommended within 1 hour'
        else:
            priority = 'LOW'
            urgency = 'Monitor and plan response'
        
        # Generate specific actions based on anomaly type
        if anomaly_type == "UNEXPECTED_SPIKE":
            actions = self._generate_spike_actions(analysis, price_data)
        else:  # UNEXPECTED_DROP
            actions = self._generate_drop_actions(analysis, price_data)
        
        # Calculate potential impact
        impact = self._calculate_impact(analysis, price_data)
        
        return {
            'priority': priority,
            'urgency': urgency,
            'title': self._generate_title(analysis),
            'why': self._generate_explanation(analysis),
            'actions': actions,
            'impact': impact,
            'confidence': confidence,
            'time_sensitive': priority == 'HIGH'
        }
    
    def _generate_spike_actions(self, analysis: Dict, price_data: Dict) -> List[Dict[str, str]]:
        """Generate actions for demand spikes."""
        actions = []
        
        deviation_pct = abs(analysis['deviation_pct'])
        current_price = analysis['current_price']
        
        # Action 1: Demand Response
        if current_price > 120:
            actions.append({
                'icon': '📉',
                'action': 'Activate Demand Response',
                'details': f'Reduce non-critical loads by {min(15, deviation_pct/2):.0f}% to offset spike',
                'estimated_savings': f"${(analysis['actual_demand'] * 0.10 * current_price * 0.5):,.0f}",
                'timeframe': 'Next 30 minutes'
            })
        
        # Action 2: Price-based strategy
        if current_price > 150:
            actions.append({
                'icon': '🔋',
                'action': 'Discharge Battery Storage',
                'details': f'Deploy stored energy to avoid purchasing at ${current_price:.2f}/MWh',
                'estimated_savings': f"${(50 * (current_price - 80)):,.0f}",
                'timeframe': 'Immediate'
            })
        
        # Action 3: Communication
        actions.append({
            'icon': '📢',
            'action': 'Alert Operations Team',
            'details': f'Notify shift supervisor of {deviation_pct:.1f}% demand spike',
            'estimated_savings': 'N/A',
            'timeframe': 'Immediate'
        })
        
        # Action 4: Investigation
        if deviation_pct > 15:
            actions.append({
                'icon': '🔍',
                'action': 'Investigate Root Cause',
                'details': 'Check SCADA for equipment issues or unexpected large load activation',
                'estimated_savings': 'Prevents future occurrences',
                'timeframe': 'Within 1 hour'
            })
        
        # Action 5: Load Shedding (high severity only)
        if deviation_pct > 25 and current_price > 200:
            actions.append({
                'icon': '⚠️',
                'action': 'Consider Load Shedding',
                'details': 'Identify and prepare to shed lowest-priority loads if spike continues',
                'estimated_savings': f"${(analysis['actual_demand'] * 0.05 * current_price):,.0f}",
                'timeframe': 'Prepare now, execute if needed'
            })
        
        return actions
    
    def _generate_drop_actions(self, analysis: Dict, price_data: Dict) -> List[Dict[str, str]]:
        """Generate actions for demand drops."""
        actions = []
        
        deviation_pct = abs(analysis['deviation_pct'])
        current_price = analysis['current_price']
        
        # Action 1: Verify Data
        actions.append({
            'icon': '🔍',
            'action': 'Verify Meter Data',
            'details': 'Confirm anomaly is real and not a data quality issue',
            'estimated_savings': 'Prevents false alarms',
            'timeframe': 'Immediate'
        })
        
        # Action 2: Opportunity actions
        if current_price < 80:
            actions.append({
                'icon': '⚡',
                'action': 'Charge Battery Storage',
                'details': f'Take advantage of low prices (${current_price:.2f}/MWh) and reduced load',
                'estimated_savings': f"${((150 - current_price) * 40):,.0f}",
                'timeframe': 'Next 2 hours'
            })
        
        # Action 3: Investigation for large drops
        if deviation_pct > 15:
            actions.append({
                'icon': '🔧',
                'action': 'Check for Outages',
                'details': f'Investigate {deviation_pct:.1f}% demand drop - possible facility outage or equipment failure',
                'estimated_savings': 'Maintains service reliability',
                'timeframe': 'Within 30 minutes'
            })
        
        # Action 4: Communication
        actions.append({
            'icon': '📞',
            'action': 'Contact Major Customers',
            'details': 'Verify large industrial customers are operational',
            'estimated_savings': 'N/A',
            'timeframe': 'Within 1 hour'
        })
        
        return actions
    
    def _calculate_impact(self, analysis: Dict, price_data: Dict) -> Dict[str, Any]:
        """Calculate the potential impact of the anomaly."""
        
        deviation_mw = analysis['actual_demand'] - analysis['expected_demand']
        current_price = analysis['current_price']
        
        # Financial impact (cost or savings)
        if analysis['anomaly_type'] == "UNEXPECTED_SPIKE":
            financial_impact = deviation_mw * current_price * 0.5  # 30-min interval
            impact_type = "Additional Cost"
        else:
            financial_impact = abs(deviation_mw) * current_price * 0.5
            impact_type = "Potential Issue"
        
        # Reliability impact
        if abs(analysis['deviation_pct']) > 20:
            reliability_risk = "High"
        elif abs(analysis['deviation_pct']) > 10:
            reliability_risk = "Medium"
        else:
            reliability_risk = "Low"
        
        return {
            'financial': f"${financial_impact:,.0f}",
            'financial_type': impact_type,
            'reliability_risk': reliability_risk,
            'magnitude_mw': abs(deviation_mw),
            'duration_estimate': '30-120 minutes (if unaddressed)'
        }
    
    def _generate_title(self, analysis: Dict) -> str:
        """Generate a clear title for the recommendation."""
        
        anomaly_type = analysis['anomaly_type']
        deviation_pct = abs(analysis['deviation_pct'])
        
        if anomaly_type == "UNEXPECTED_SPIKE":
            return f"Demand Spike Detected: {deviation_pct:.1f}% Above Normal"
        else:
            return f"Demand Drop Detected: {deviation_pct:.1f}% Below Normal"
    
    def _generate_explanation(self, analysis: Dict) -> str:
        """Generate a clear explanation of why this is an anomaly."""
        
        explanation = f"**Primary Cause:** {analysis['primary_diagnosis']}\n\n"
        explanation += f"**What's Happening:** Demand is {abs(analysis['deviation_pct']):.1f}% {analysis['direction']} "
        explanation += f"the expected {analysis['expected_demand']:.0f} MW for this time period.\n\n"
        
        explanation += "**Contributing Factors:**\n"
        for factor in analysis['contributing_factors'][:3]:  # Top 3 factors
            explanation += f"• {factor}\n"
        
        if analysis['current_price'] > 150:
            explanation += f"\n⚠️ **High Price Alert:** Current prices at ${analysis['current_price']:.2f}/MWh "
            explanation += "increase the urgency of this anomaly."
        elif analysis['current_price'] < 80:
            explanation += f"\n💡 **Low Price Opportunity:** Current prices at ${analysis['current_price']:.2f}/MWh "
            explanation += "present optimization opportunities."
        
        return explanation


def generate_anomaly_recommendations(
    ml_predictions_file: str = None,
    price_forecast_file: str = None,
    output_file: str = 'data/anomaly_recommendations.json'
) -> List[Dict]:
    """
    Generate recommendations for all detected anomalies.
    
    Args:
        ml_predictions_file: Path to ML predictions JSON
        price_forecast_file: Path to price forecast JSON
        output_file: Where to save recommendations
        
    Returns:
        List of anomaly-recommendation pairs
    """
    
    print("🔍 Analyzing Detected Anomalies...")
    print("="*70)
    
    # Load ML predictions
    if ml_predictions_file is None:
        current_month = datetime.now().month
        month_names = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        ml_predictions_file = f'models/predictions/{month_names[current_month-1]}_predictions.json'
    
    print(f"\n1️⃣  Loading ML predictions from {ml_predictions_file}...")
    with open(ml_predictions_file, 'r') as f:
        ml_data = json.load(f)
    
    predictions = ml_data.get('predictions', [])
    print(f"   ✅ Loaded {len(predictions)} predictions")
    
    # Filter to anomalies only
    anomalies = [p for p in predictions if p.get('is_anomaly', False)]
    print(f"   🚨 Found {len(anomalies)} anomalies")
    
    if len(anomalies) == 0:
        print("\n✅ No anomalies detected - system operating normally!")
        return []
    
    # Load price forecast
    if price_forecast_file is None:
        price_forecast_file = 'data/price_forecast.json'
    
    print(f"\n2️⃣  Loading price forecast from {price_forecast_file}...")
    with open(price_forecast_file, 'r') as f:
        price_data = json.load(f)
    
    price_forecast = price_data.get('data', [])
    price_df = pd.DataFrame(price_forecast)
    price_df['timestamp'] = pd.to_datetime(price_df['timestamp']).dt.round('h')
    print(f"   ✅ Loaded {len(price_forecast)} price points")
    
    # Calculate historical patterns
    print("\n3️⃣  Analyzing historical patterns...")
    pred_df = pd.DataFrame(predictions)
    normal_data = pred_df[~pred_df['is_anomaly']].copy()
    
    if not normal_data.empty:
        normal_data['timestamp'] = pd.to_datetime(normal_data['timestamp'])
        normal_data['hour'] = normal_data['timestamp'].dt.hour
        hourly_avg = normal_data.groupby('hour')['demand_mw'].mean().to_dict()
    else:
        # Fallback to using all data
        pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])
        pred_df['hour'] = pred_df['timestamp'].dt.hour
        hourly_avg = pred_df.groupby('hour')['demand_mw'].mean().to_dict()
    
    historical_pattern = {'hourly_avg': hourly_avg}
    print(f"   ✅ Built hourly patterns from {len(normal_data)} normal data points")
    
    # Analyze each anomaly
    print(f"\n4️⃣  Generating recommendations for {len(anomalies)} anomalies...")
    analyzer = AnomalyAnalyzer()
    results = []
    
    for i, anomaly in enumerate(anomalies, 1):
        # Get price data for this timestamp
        anomaly_time = pd.to_datetime(anomaly['timestamp']).round('h')
        price_row = price_df[price_df['timestamp'] == anomaly_time]
        
        if not price_row.empty:
            price_info = {
                'price_per_mwh': price_row.iloc[0]['price_per_mwh']
            }
        else:
            price_info = {'price_per_mwh': 100}  # Default
        
        # Analyze and generate recommendation
        result = analyzer.analyze_anomaly(
            anomaly=anomaly,
            price_data=price_info,
            historical_pattern=historical_pattern
        )
        
        results.append(result)
        print(f"   ✅ [{i}/{len(anomalies)}] {result['recommendation']['title']}")
    
    # Save results
    print(f"\n5️⃣  Saving recommendations to {output_file}...")
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'total_anomalies': len(anomalies),
        'high_priority': sum(1 for r in results if r['recommendation']['priority'] == 'HIGH'),
        'medium_priority': sum(1 for r in results if r['recommendation']['priority'] == 'MEDIUM'),
        'low_priority': sum(1 for r in results if r['recommendation']['priority'] == 'LOW'),
        'recommendations': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"   ✅ Saved successfully")
    
    # Print summary
    print("\n" + "="*70)
    print("📊 ANOMALY ANALYSIS SUMMARY")
    print("="*70)
    print(f"   🚨 Total Anomalies: {len(anomalies)}")
    print(f"   🔴 High Priority: {output_data['high_priority']}")
    print(f"   🟡 Medium Priority: {output_data['medium_priority']}")
    print(f"   🟢 Low Priority: {output_data['low_priority']}")
    print("="*70)
    
    return results


if __name__ == "__main__":
    # Generate anomaly-based recommendations
    results = generate_anomaly_recommendations()
    
    if results:
        print(f"\n🎯 Top 3 Anomalies with Recommendations:\n")
        for i, result in enumerate(results[:3], 1):
            rec = result['recommendation']
            anomaly = result['anomaly']
            
            print(f"{i}. {rec['title']}")
            print(f"   Time: {anomaly['time_str']} on {anomaly['date_str']}")
            print(f"   Priority: {rec['priority']} | Confidence: {anomaly['confidence']*100:.0f}%")
            print(f"   Actions: {len(rec['actions'])} recommended")
            print()
