"""
Smart Recommendation Engine for LADWP Grid Intelligence Dashboard
Phase 3 - Rule-Based Decision System
"""

import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


class RecommendationEngine:
    """
    Rule-based recommendation engine for grid operations.
    Analyzes predictions, prices, and demand to suggest actionable strategies.
    """
    
    # Thresholds (tunable based on historical data)
    HIGH_PRICE_THRESHOLD = 120  # $/MWh (lowered to trigger more often)
    VERY_HIGH_PRICE_THRESHOLD = 180  # $/MWh
    DEMAND_SPIKE_THRESHOLD = 0.15  # 15% increase
    ANOMALY_CONFIDENCE_THRESHOLD = 0.7  # 70% confidence for action
    
    # ROI calculations (simplified - customize based on actual costs)
    DEMAND_RESPONSE_COST_PER_MW = 50  # Cost to implement DR
    BATTERY_DISCHARGE_COST_PER_MWH = 30  # Battery wear cost
    LOAD_SHIFT_SAVINGS_MULTIPLIER = 0.8  # 80% of price difference
    
    def __init__(self):
        self.recommendations_history = []
    
    def generate_recommendations(
        self, 
        predictions: List[Dict], 
        price_forecast: List[Dict],
        current_demand: float,
        battery_soc: float = 0.5  # State of charge (0-1)
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on current conditions.
        
        Args:
            predictions: List of prediction dicts with timestamp, demand_mw, is_anomaly
            price_forecast: List of price dicts with timestamp, price_per_mwh
            current_demand: Current demand in MW
            battery_soc: Battery state of charge (0-1)
            
        Returns:
            List of recommendation dicts with action, reason, priority, roi, time_window
        """
        recommendations = []
        
        # Convert to DataFrames for easier analysis
        pred_df = pd.DataFrame(predictions)
        price_df = pd.DataFrame(price_forecast)
        
        # Ensure timestamps are datetime objects
        pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        
        # Round price timestamps to nearest hour for merging
        price_df['timestamp'] = price_df['timestamp'].dt.round('H')
        
        # Merge predictions with prices
        df = pd.merge(pred_df, price_df, on='timestamp', how='left')
        
        # Analyze next 4 hours (critical window)
        # Make now timezone-aware to match the data
        pacific = pytz.timezone('America/Los_Angeles')
        now = datetime.now(pacific)
        critical_window = df[df['timestamp'] <= now + timedelta(hours=4)]
        
        # Rule 1: High Price + High Demand → Demand Response
        self._check_demand_response_opportunity(critical_window, current_demand, recommendations)
        
        # Rule 2: Price Spike + Anomaly → Battery Discharge
        self._check_battery_discharge_opportunity(critical_window, battery_soc, recommendations)
        
        # Rule 3: Low Price Period → Battery Charging
        self._check_battery_charging_opportunity(df, battery_soc, recommendations)
        
        # Rule 4: Demand Spike Prediction → Load Shifting
        self._check_load_shifting_opportunity(df, current_demand, recommendations)
        
        # Rule 5: Consecutive Anomalies → Preventive Maintenance
        self._check_maintenance_needs(df, recommendations)
        
        # Rule 6: Price Arbitrage Opportunities
        self._check_price_arbitrage(df, recommendations)
        
        # Sort by priority and ROI
        recommendations.sort(key=lambda x: (x['priority'], -x['estimated_savings']), reverse=True)
        
        # Store for history tracking
        self.recommendations_history.append({
            'timestamp': now,
            'recommendations': recommendations
        })
        
        return recommendations
    
    def _check_demand_response_opportunity(
        self, 
        window: pd.DataFrame, 
        current_demand: float, 
        recommendations: List
    ):
        """Check for demand response opportunities during high price periods."""
        high_price_periods = window[window['price_per_mwh'] > self.HIGH_PRICE_THRESHOLD]
        
        if len(high_price_periods) > 0:
            peak_period = high_price_periods.iloc[0]
            peak_price = peak_period['price_per_mwh']
            peak_time = peak_period['timestamp']
            
            # Calculate potential savings
            dr_reduction_mw = current_demand * 0.10  # 10% reduction
            duration_hours = len(high_price_periods) * 0.5  # 30-min intervals
            savings = (peak_price * dr_reduction_mw * duration_hours) - \
                     (self.DEMAND_RESPONSE_COST_PER_MW * dr_reduction_mw)
            
            if savings > 0:
                recommendations.append({
                    'action': 'DEMAND_RESPONSE',
                    'title': 'Activate Demand Response Program',
                    'reason': f'Price spike to ${peak_price:.2f}/MWh detected at {peak_time.strftime("%I:%M %p")}',
                    'details': f'Reduce demand by {dr_reduction_mw:.1f} MW for {duration_hours:.1f} hours',
                    'priority': 'HIGH' if peak_price > self.VERY_HIGH_PRICE_THRESHOLD else 'MEDIUM',
                    'estimated_savings': savings,
                    'time_window': f'{peak_time.strftime("%I:%M %p")} - {(peak_time + timedelta(hours=duration_hours)).strftime("%I:%M %p")}',
                    'confidence': 0.85
                })
    
    def _check_battery_discharge_opportunity(
        self, 
        window: pd.DataFrame, 
        battery_soc: float, 
        recommendations: List
    ):
        """Check for battery discharge opportunities during price spikes + anomalies."""
        if battery_soc < 0.2:  # Not enough charge
            return
        
        critical_periods = window[
            (window['price_per_mwh'] > self.HIGH_PRICE_THRESHOLD) & 
            (window['is_anomaly'] == True)
        ]
        
        if len(critical_periods) > 0:
            peak_period = critical_periods.iloc[0]
            peak_price = peak_period['price_per_mwh']
            peak_time = peak_period['timestamp']
            
            # Calculate discharge strategy
            available_capacity_mwh = battery_soc * 100  # Assume 100 MWh battery
            discharge_amount = min(available_capacity_mwh * 0.8, 50)  # Max 50 MWh discharge
            
            savings = (peak_price * discharge_amount) - \
                     (self.BATTERY_DISCHARGE_COST_PER_MWH * discharge_amount)
            
            if savings > 0:
                recommendations.append({
                    'action': 'BATTERY_DISCHARGE',
                    'title': 'Discharge Battery Storage',
                    'reason': f'Price spike (${peak_price:.2f}/MWh) + demand anomaly detected',
                    'details': f'Discharge {discharge_amount:.1f} MWh from battery (SOC: {battery_soc*100:.0f}%)',
                    'priority': 'HIGH',
                    'estimated_savings': savings,
                    'time_window': f'{peak_time.strftime("%I:%M %p")} - {(peak_time + timedelta(hours=2)).strftime("%I:%M %p")}',
                    'confidence': 0.90
                })
    
    def _check_battery_charging_opportunity(
        self, 
        df: pd.DataFrame, 
        battery_soc: float, 
        recommendations: List
    ):
        """Check for battery charging opportunities during low price periods."""
        if battery_soc > 0.8:  # Battery nearly full
            return
        
        # Look for low price periods in next 12 hours
        pacific = pytz.timezone('America/Los_Angeles')
        now = datetime.now(pacific)
        next_12h = df[df['timestamp'] <= now + timedelta(hours=12)]
        low_price_periods = next_12h[next_12h['price_per_mwh'] < 80]  # Below $80/MWh
        
        if len(low_price_periods) > 2:  # Need sustained low price
            charge_window = low_price_periods.iloc[0]
            charge_price = charge_window['price_per_mwh']
            charge_time = charge_window['timestamp']
            
            # Calculate charging strategy
            available_capacity_mwh = (1 - battery_soc) * 100
            charge_amount = min(available_capacity_mwh, 40)  # Max 40 MWh charge
            
            # Estimate future savings (assume avg price of $150/MWh for discharge)
            future_revenue = 150 * charge_amount
            charge_cost = charge_price * charge_amount * 1.1  # Include charging losses
            savings = future_revenue - charge_cost
            
            if savings > 0:
                recommendations.append({
                    'action': 'BATTERY_CHARGE',
                    'title': 'Charge Battery Storage',
                    'reason': f'Low price period (${charge_price:.2f}/MWh) detected',
                    'details': f'Charge {charge_amount:.1f} MWh to battery (SOC: {battery_soc*100:.0f}%)',
                    'priority': 'MEDIUM',
                    'estimated_savings': savings,
                    'time_window': f'{charge_time.strftime("%I:%M %p")} - {(charge_time + timedelta(hours=4)).strftime("%I:%M %p")}',
                    'confidence': 0.75
                })
    
    def _check_load_shifting_opportunity(
        self, 
        df: pd.DataFrame, 
        current_demand: float, 
        recommendations: List
    ):
        """Check for load shifting opportunities between high and low price periods."""
        pacific = pytz.timezone('America/Los_Angeles')
        now = datetime.now(pacific)
        next_24h = df[df['timestamp'] <= now + timedelta(hours=24)]
        
        if len(next_24h) < 10:
            return
        
        # Find peak and off-peak periods
        peak_periods = next_24h[next_24h['price_per_mwh'] > 120]
        offpeak_periods = next_24h[next_24h['price_per_mwh'] < 80]
        
        if len(peak_periods) > 0 and len(offpeak_periods) > 0:
            peak_avg_price = peak_periods['price_per_mwh'].mean()
            offpeak_avg_price = offpeak_periods['price_per_mwh'].mean()
            price_diff = peak_avg_price - offpeak_avg_price
            
            if price_diff > 60:  # Significant arbitrage opportunity
                shiftable_load_mw = current_demand * 0.15  # 15% of load is shiftable
                savings = price_diff * shiftable_load_mw * self.LOAD_SHIFT_SAVINGS_MULTIPLIER * 4  # 4 hours
                
                recommendations.append({
                    'action': 'LOAD_SHIFT',
                    'title': 'Shift Non-Critical Loads',
                    'reason': f'${price_diff:.2f}/MWh price difference between peak and off-peak',
                    'details': f'Shift {shiftable_load_mw:.1f} MW to off-peak hours (${offpeak_avg_price:.2f}/MWh)',
                    'priority': 'MEDIUM',
                    'estimated_savings': savings,
                    'time_window': f'Peak: {peak_periods.iloc[0]["timestamp"].strftime("%I:%M %p")} | Off-peak: {offpeak_periods.iloc[0]["timestamp"].strftime("%I:%M %p")}',
                    'confidence': 0.70
                })
    
    def _check_maintenance_needs(self, df: pd.DataFrame, recommendations: List):
        """Check for equipment issues based on consecutive anomalies."""
        # Look for 3+ consecutive anomalies (potential equipment issue)
        anomaly_sequences = []
        current_sequence = []
        
        for idx, row in df.iterrows():
            if row['is_anomaly']:
                current_sequence.append(row)
            else:
                if len(current_sequence) >= 3:
                    anomaly_sequences.append(current_sequence)
                current_sequence = []
        
        if current_sequence and len(current_sequence) >= 3:
            anomaly_sequences.append(current_sequence)
        
        for sequence in anomaly_sequences[:2]:  # Report top 2 issues
            start_time = sequence[0]['timestamp']
            duration = len(sequence) * 0.5  # 30-min intervals
            
            recommendations.append({
                'action': 'MAINTENANCE_CHECK',
                'title': 'Schedule Preventive Maintenance',
                'reason': f'{len(sequence)} consecutive anomalies detected starting {start_time.strftime("%I:%M %p")}',
                'details': f'Unusual demand pattern suggests potential equipment issue or data quality problem',
                'priority': 'LOW',
                'estimated_savings': 5000,  # Estimated cost of emergency repair avoided
                'time_window': f'Next maintenance window',
                'confidence': 0.60
            })
    
    def _check_price_arbitrage(self, df: pd.DataFrame, recommendations: List):
        """Check for price arbitrage opportunities across different time periods."""
        pacific = pytz.timezone('America/Los_Angeles')
        now = datetime.now(pacific)
        next_48h = df[df['timestamp'] <= now + timedelta(hours=48)]
        
        if len(next_48h) < 20:
            return
        
        # Filter out rows with missing price data
        next_48h = next_48h.dropna(subset=['price_per_mwh'])
        
        if len(next_48h) < 20:
            return
        
        # Find maximum price spread
        max_price_row = next_48h.loc[next_48h['price_per_mwh'].idxmax()]
        min_price_row = next_48h.loc[next_48h['price_per_mwh'].idxmin()]
        
        price_spread = max_price_row['price_per_mwh'] - min_price_row['price_per_mwh']
        
        if price_spread > 100:  # Significant arbitrage opportunity
            arbitrage_volume_mw = 30  # 30 MW arbitrage
            savings = price_spread * arbitrage_volume_mw * 0.75  # 75% capture efficiency
            
            recommendations.append({
                'action': 'PRICE_ARBITRAGE',
                'title': 'Execute Price Arbitrage Strategy',
                'reason': f'${price_spread:.2f}/MWh spread detected in next 48 hours',
                'details': f'Buy at ${min_price_row["price_per_mwh"]:.2f}/MWh ({min_price_row["timestamp"].strftime("%I:%M %p")}), sell at ${max_price_row["price_per_mwh"]:.2f}/MWh ({max_price_row["timestamp"].strftime("%I:%M %p")})',
                'priority': 'MEDIUM',
                'estimated_savings': savings,
                'time_window': f'{min_price_row["timestamp"].strftime("%m/%d %I:%M %p")} - {max_price_row["timestamp"].strftime("%m/%d %I:%M %p")}',
                'confidence': 0.80
            })
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of recommendations over time."""
        if not self.recommendations_history:
            return {}
        
        total_recommendations = sum(len(h['recommendations']) for h in self.recommendations_history)
        total_potential_savings = sum(
            rec['estimated_savings'] 
            for h in self.recommendations_history 
            for rec in h['recommendations']
        )
        
        action_counts = {}
        for h in self.recommendations_history:
            for rec in h['recommendations']:
                action = rec['action']
                action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            'total_recommendations': total_recommendations,
            'total_potential_savings': total_potential_savings,
            'action_breakdown': action_counts,
            'avg_recommendations_per_run': total_recommendations / len(self.recommendations_history)
        }


def format_recommendation_for_display(rec: Dict[str, Any]) -> str:
    """Format a recommendation for clean display in the dashboard."""
    priority_emoji = {
        'HIGH': '🔴',
        'MEDIUM': '🟡',
        'LOW': '🟢'
    }
    
    action_emoji = {
        'DEMAND_RESPONSE': '📉',
        'BATTERY_DISCHARGE': '🔋',
        'BATTERY_CHARGE': '⚡',
        'LOAD_SHIFT': '🔄',
        'MAINTENANCE_CHECK': '🔧',
        'PRICE_ARBITRAGE': '💰'
    }
    
    return f"""
{priority_emoji.get(rec['priority'], '⚪')} **{rec['title']}** {action_emoji.get(rec['action'], '')}

**Why:** {rec['reason']}

**Action:** {rec['details']}

**When:** {rec['time_window']}

**Potential Savings:** ${rec['estimated_savings']:,.2f}

**Confidence:** {rec['confidence']*100:.0f}%
"""


if __name__ == "__main__":
    # Test the recommendation engine
    print("Testing Recommendation Engine...")
    
    # Sample data
    test_predictions = [
        {'timestamp': datetime.now() + timedelta(hours=i), 
         'demand_mw': 1000 + i*10, 
         'is_anomaly': i % 5 == 0} 
        for i in range(48)
    ]
    
    test_prices = [
        {'timestamp': datetime.now() + timedelta(hours=i), 
         'price_per_mwh': 100 + (50 if 14 <= (datetime.now() + timedelta(hours=i)).hour <= 20 else 0)} 
        for i in range(48)
    ]
    
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(
        predictions=test_predictions,
        price_forecast=test_prices,
        current_demand=1000,
        battery_soc=0.6
    )
    
    print(f"\n✅ Generated {len(recommendations)} recommendations\n")
    
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"Recommendation {i}:")
        print(format_recommendation_for_display(rec))
        print("-" * 80)
    
    stats = engine.get_summary_stats()
    print(f"\nSummary Stats: {json.dumps(stats, indent=2)}")
