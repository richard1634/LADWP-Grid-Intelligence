"""
Price Forecasting Module for LADWP Grid Intelligence
Generates synthetic price forecasts based on time-of-day patterns
(In production, this would integrate with CAISO price APIs or ML models)
"""

import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from typing import List, Dict


class PriceForecast:
    """
    Generate electricity price forecasts for the next 48 hours.
    Uses time-of-day patterns and seasonality.
    """
    
    # Base prices by hour ($/MWh) - California typical patterns
    BASE_PRICES = {
        0: 60, 1: 55, 2: 50, 3: 50, 4: 55, 5: 65,
        6: 85, 7: 110, 8: 130, 9: 140, 10: 145, 11: 150,
        12: 155, 13: 160, 14: 165, 15: 170, 16: 180, 17: 190,
        18: 200, 19: 195, 20: 175, 21: 140, 22: 100, 23: 75
    }
    
    # Seasonal multipliers
    SEASON_MULTIPLIERS = {
        'winter': 0.85,   # Dec, Jan, Feb
        'spring': 0.90,   # Mar, Apr, May
        'summer': 1.25,   # Jun, Jul, Aug
        'fall': 0.95      # Sep, Oct, Nov
    }
    
    def __init__(self, volatility: float = 0.15):
        """
        Initialize price forecast generator.
        
        Args:
            volatility: Price volatility factor (0-1). Higher = more variation.
        """
        self.volatility = volatility
    
    def get_season(self, date: datetime) -> str:
        """Determine the season based on month."""
        month = date.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def generate_forecast(
        self, 
        start_time: datetime = None, 
        hours: int = 48
    ) -> List[Dict]:
        """
        Generate price forecast for the specified time period.
        
        Args:
            start_time: Starting timestamp (defaults to now)
            hours: Number of hours to forecast
            
        Returns:
            List of dicts with timestamp and price_per_mwh
        """
        if start_time is None:
            # Use Pacific timezone for consistency with CAISO data
            pacific = pytz.timezone('America/Los_Angeles')
            start_time = datetime.now(pacific)
        
        # Get season multiplier
        season = self.get_season(start_time)
        season_mult = self.SEASON_MULTIPLIERS[season]
        
        forecast = []
        
        for hour_offset in range(hours):
            timestamp = start_time + timedelta(hours=hour_offset)
            hour = timestamp.hour
            
            # Base price for this hour
            base_price = self.BASE_PRICES[hour]
            
            # Apply seasonal adjustment
            price = base_price * season_mult
            
            # Add some realistic volatility (log-normal distribution)
            noise = np.random.lognormal(0, self.volatility) 
            price = price * noise
            
            # Weekend discount (10% lower on Sat/Sun)
            if timestamp.weekday() >= 5:  # Saturday or Sunday
                price *= 0.90
            
            # Occasional price spikes (5% chance)
            if np.random.random() < 0.05:
                price *= np.random.uniform(1.5, 2.5)
            
            # Floor at $40, cap at $500
            price = max(40, min(500, price))
            
            forecast.append({
                'timestamp': timestamp.isoformat(),
                'price_per_mwh': round(price, 2),
                'hour': hour,
                'season': season
            })
        
        return forecast
    
    def generate_forecast_dataframe(
        self, 
        start_time: datetime = None, 
        hours: int = 48
    ) -> pd.DataFrame:
        """
        Generate price forecast as a pandas DataFrame.
        
        Args:
            start_time: Starting timestamp (defaults to now)
            hours: Number of hours to forecast
            
        Returns:
            DataFrame with timestamp and price_per_mwh columns
        """
        forecast_list = self.generate_forecast(start_time, hours)
        df = pd.DataFrame(forecast_list)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def get_peak_offpeak_summary(
        self, 
        start_time: datetime = None, 
        hours: int = 24
    ) -> Dict:
        """
        Get summary of peak vs off-peak pricing for the forecast period.
        
        Args:
            start_time: Starting timestamp (defaults to now)
            hours: Number of hours to analyze
            
        Returns:
            Dict with peak, offpeak, and arbitrage opportunity info
        """
        df = self.generate_forecast_dataframe(start_time, hours)
        
        # Define peak hours (14:00 - 21:00)
        df['is_peak'] = df['timestamp'].dt.hour.isin(range(14, 22))
        
        peak_prices = df[df['is_peak']]['price_per_mwh']
        offpeak_prices = df[~df['is_peak']]['price_per_mwh']
        
        return {
            'peak_avg': peak_prices.mean(),
            'peak_max': peak_prices.max(),
            'offpeak_avg': offpeak_prices.mean(),
            'offpeak_min': offpeak_prices.min(),
            'price_spread': peak_prices.max() - offpeak_prices.min(),
            'arbitrage_potential': (peak_prices.mean() - offpeak_prices.mean()) * hours
        }


def save_forecast_to_json(output_path: str = 'data/price_forecast.json'):
    """
    Generate and save a 48-hour price forecast to JSON file.
    
    Args:
        output_path: Path to save the JSON file
    """
    import json
    import os
    
    forecaster = PriceForecast(volatility=0.12)
    forecast = forecaster.generate_forecast(hours=48)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'forecast_hours': 48,
            'data': forecast
        }, f, indent=2)
    
    print(f"✅ Price forecast saved to {output_path}")
    print(f"   Forecasted {len(forecast)} hourly prices")
    
    # Print summary
    df = pd.DataFrame(forecast)
    print(f"\n📊 Price Summary:")
    print(f"   Average: ${df['price_per_mwh'].mean():.2f}/MWh")
    print(f"   Min: ${df['price_per_mwh'].min():.2f}/MWh")
    print(f"   Max: ${df['price_per_mwh'].max():.2f}/MWh")
    
    return forecast


if __name__ == "__main__":
    print("Generating 48-hour price forecast...\n")
    
    # Generate and save forecast
    forecast = save_forecast_to_json()
    
    # Show peak/off-peak analysis
    print("\n" + "="*60)
    forecaster = PriceForecast()
    summary = forecaster.get_peak_offpeak_summary()
    
    print("\n⚡ Peak vs Off-Peak Analysis:")
    print(f"   Peak Average: ${summary['peak_avg']:.2f}/MWh")
    print(f"   Off-Peak Average: ${summary['offpeak_avg']:.2f}/MWh")
    print(f"   Price Spread: ${summary['price_spread']:.2f}/MWh")
    print(f"   Arbitrage Potential: ${summary['arbitrage_potential']:,.2f}")
