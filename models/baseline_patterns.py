"""
Baseline Pattern Learning - Phase 2 Step 2

Analyzes historical data to establish "normal" grid behavior patterns.
This provides features for ML models and basic anomaly detection.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaselinePatterns:
    """Learn and store normal grid behavior patterns from historical data."""
    
    def __init__(self, db_path: str = None):
        """Initialize with database path."""
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "historical_data" / "ladwp_grid_data.db"
        
        self.db_path = Path(db_path)
        self.patterns = {}
        self.patterns_dir = Path(__file__).parent / "baseline_data"
        self.patterns_dir.mkdir(exist_ok=True)
        
    def load_historical_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load price and demand data from database."""
        logger.info(f"Loading data from {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        
        # Check if prices table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        has_prices = cursor.fetchone() is not None
        
        # Load prices if table exists
        if has_prices:
            prices_df = pd.read_sql_query("""
                SELECT timestamp, price, congestion, energy, loss, node
                FROM prices
                ORDER BY timestamp
            """, conn)
            prices_df['timestamp'] = pd.to_datetime(prices_df['timestamp'])
        else:
            prices_df = pd.DataFrame()
            logger.warning("⚠️  No prices table found - will analyze demand only")
        
        # Load demand
        demand_df = pd.read_sql_query("""
            SELECT timestamp, demand_mw, area, market_type
            FROM demand
            ORDER BY timestamp
        """, conn)
        demand_df['timestamp'] = pd.to_datetime(demand_df['timestamp'])
        
        conn.close()
        
        logger.info(f"✅ Loaded {len(prices_df)} price records, {len(demand_df)} demand records")
        if not prices_df.empty:
            logger.info(f"📅 Price range: {prices_df['timestamp'].min()} to {prices_df['timestamp'].max()}")
        logger.info(f"📅 Demand range: {demand_df['timestamp'].min()} to {demand_df['timestamp'].max()}")
        
        return prices_df, demand_df
    
    def extract_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features for pattern analysis."""
        df = df.copy()
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['date'] = df['timestamp'].dt.date
        return df
    
    def analyze_price_patterns(self, prices_df: pd.DataFrame) -> dict:
        """Analyze price patterns by time of day and day of week."""
        logger.info("📊 Analyzing price patterns...")
        
        prices_df = self.extract_time_features(prices_df)
        
        patterns = {}
        
        # Overall statistics
        patterns['overall'] = {
            'mean': float(prices_df['price'].mean()),
            'std': float(prices_df['price'].std()),
            'min': float(prices_df['price'].min()),
            'max': float(prices_df['price'].max()),
            'median': float(prices_df['price'].median()),
            'p25': float(prices_df['price'].quantile(0.25)),
            'p75': float(prices_df['price'].quantile(0.75)),
            'p95': float(prices_df['price'].quantile(0.95)),
            'p99': float(prices_df['price'].quantile(0.99))
        }
        
        # Hourly patterns
        hourly = prices_df.groupby('hour')['price'].agg([
            'mean', 'std', 'min', 'max', 'median',
            ('p25', lambda x: x.quantile(0.25)),
            ('p75', lambda x: x.quantile(0.75)),
            ('p95', lambda x: x.quantile(0.95))
        ]).round(2)
        
        patterns['hourly'] = {
            int(hour): {
                'mean': float(row['mean']),
                'std': float(row['std']),
                'min': float(row['min']),
                'max': float(row['max']),
                'median': float(row['median']),
                'p25': float(row['p25']),
                'p75': float(row['p75']),
                'p95': float(row['p95'])
            }
            for hour, row in hourly.iterrows()
        }
        
        # Day of week patterns
        dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_patterns = prices_df.groupby('day_of_week')['price'].agg([
            'mean', 'std', 'min', 'max', 'median',
            ('p25', lambda x: x.quantile(0.25)),
            ('p75', lambda x: x.quantile(0.75)),
            ('p95', lambda x: x.quantile(0.95))
        ]).round(2)
        
        patterns['day_of_week'] = {
            dow_names[int(dow)]: {
                'mean': float(row['mean']),
                'std': float(row['std']),
                'min': float(row['min']),
                'max': float(row['max']),
                'median': float(row['median']),
                'p25': float(row['p25']),
                'p75': float(row['p75']),
                'p95': float(row['p95'])
            }
            for dow, row in dow_patterns.iterrows()
        }
        
        # Weekend vs Weekday
        weekend_patterns = prices_df.groupby('is_weekend')['price'].agg([
            'mean', 'std', 'min', 'max', 'median'
        ]).round(2)
        
        patterns['weekend_vs_weekday'] = {
            'weekday': {
                'mean': float(weekend_patterns.loc[0, 'mean']),
                'std': float(weekend_patterns.loc[0, 'std']),
                'median': float(weekend_patterns.loc[0, 'median'])
            },
            'weekend': {
                'mean': float(weekend_patterns.loc[1, 'mean']),
                'std': float(weekend_patterns.loc[1, 'std']),
                'median': float(weekend_patterns.loc[1, 'median'])
            }
        }
        
        # Peak hours identification (top 5 most expensive hours on average)
        top_hours = hourly.nlargest(5, 'mean')
        patterns['peak_hours'] = [int(h) for h in top_hours.index.tolist()]
        
        logger.info(f"✅ Price patterns analyzed")
        logger.info(f"   Overall mean: ${patterns['overall']['mean']:.2f}/MWh")
        logger.info(f"   Peak hours: {patterns['peak_hours']}")
        
        return patterns
    
    def analyze_demand_patterns(self, demand_df: pd.DataFrame) -> dict:
        """Analyze demand patterns by time of day and day of week."""
        logger.info("📊 Analyzing demand patterns...")
        
        demand_df = self.extract_time_features(demand_df)
        
        patterns = {}
        
        # Overall statistics
        patterns['overall'] = {
            'mean': float(demand_df['demand_mw'].mean()),
            'std': float(demand_df['demand_mw'].std()),
            'min': float(demand_df['demand_mw'].min()),
            'max': float(demand_df['demand_mw'].max()),
            'median': float(demand_df['demand_mw'].median()),
            'p25': float(demand_df['demand_mw'].quantile(0.25)),
            'p75': float(demand_df['demand_mw'].quantile(0.75)),
            'p95': float(demand_df['demand_mw'].quantile(0.95))
        }
        
        # Hourly patterns
        hourly = demand_df.groupby('hour')['demand_mw'].agg([
            'mean', 'std', 'min', 'max', 'median',
            ('p25', lambda x: x.quantile(0.25)),
            ('p75', lambda x: x.quantile(0.75)),
            ('p95', lambda x: x.quantile(0.95))
        ]).round(2)
        
        patterns['hourly'] = {
            int(hour): {
                'mean': float(row['mean']),
                'std': float(row['std']),
                'min': float(row['min']),
                'max': float(row['max']),
                'median': float(row['median']),
                'p25': float(row['p25']),
                'p75': float(row['p75']),
                'p95': float(row['p95'])
            }
            for hour, row in hourly.iterrows()
        }
        
        # Day of week patterns
        dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_patterns = demand_df.groupby('day_of_week')['demand_mw'].agg([
            'mean', 'std', 'min', 'max', 'median'
        ]).round(2)
        
        patterns['day_of_week'] = {
            dow_names[int(dow)]: {
                'mean': float(row['mean']),
                'std': float(row['std']),
                'min': float(row['min']),
                'max': float(row['max']),
                'median': float(row['median'])
            }
            for dow, row in dow_patterns.iterrows()
        }
        
        # Weekend vs Weekday
        weekend_patterns = demand_df.groupby('is_weekend')['demand_mw'].agg([
            'mean', 'std', 'median'
        ]).round(2)
        
        patterns['weekend_vs_weekday'] = {
            'weekday': {
                'mean': float(weekend_patterns.loc[0, 'mean']),
                'std': float(weekend_patterns.loc[0, 'std']),
                'median': float(weekend_patterns.loc[0, 'median'])
            },
            'weekend': {
                'mean': float(weekend_patterns.loc[1, 'mean']),
                'std': float(weekend_patterns.loc[1, 'std']),
                'median': float(weekend_patterns.loc[1, 'median'])
            }
        }
        
        # Peak demand hours (top 5)
        top_hours = hourly.nlargest(5, 'mean')
        patterns['peak_hours'] = [int(h) for h in top_hours.index.tolist()]
        
        logger.info(f"✅ Demand patterns analyzed")
        logger.info(f"   Overall mean: {patterns['overall']['mean']:.0f} MW")
        logger.info(f"   Peak hours: {patterns['peak_hours']}")
        
        return patterns
    
    def calculate_correlations(self, prices_df: pd.DataFrame, demand_df: pd.DataFrame) -> dict:
        """Calculate price-demand correlations."""
        logger.info("📊 Analyzing price-demand correlations...")
        
        # Merge on timestamp (closest match)
        prices_df = self.extract_time_features(prices_df)
        demand_df = self.extract_time_features(demand_df)
        
        # For correlation, we need matching timestamps
        # Group both by hour and date for aggregation
        prices_hourly = prices_df.groupby(['date', 'hour'])['price'].mean().reset_index()
        demand_hourly = demand_df.groupby(['date', 'hour'])['demand_mw'].mean().reset_index()
        
        merged = pd.merge(prices_hourly, demand_hourly, on=['date', 'hour'], how='inner')
        
        if len(merged) > 0:
            correlation = float(merged['price'].corr(merged['demand_mw']))
            logger.info(f"✅ Price-Demand correlation: {correlation:.3f}")
            return {'price_demand_correlation': round(correlation, 3)}
        else:
            logger.warning("⚠️  Could not calculate correlation - no matching timestamps")
            return {'price_demand_correlation': None}
    
    def learn_patterns(self) -> dict:
        """Main method to learn all patterns from historical data."""
        logger.info("=" * 60)
        logger.info("LEARNING BASELINE PATTERNS")
        logger.info("=" * 60)
        
        # Load data
        prices_df, demand_df = self.load_historical_data()
        
        # Analyze patterns (skip prices if empty)
        price_patterns = None
        if not prices_df.empty:
            price_patterns = self.analyze_price_patterns(prices_df)
        else:
            logger.warning("No price data available, skipping price pattern analysis")
            
        demand_patterns = self.analyze_demand_patterns(demand_df)
        
        correlations = None
        if not prices_df.empty:
            correlations = self.calculate_correlations(prices_df, demand_df)
        
        # Combine all patterns
        data_start = demand_df['timestamp'].min() if not demand_df.empty else prices_df['timestamp'].min()
        data_end = demand_df['timestamp'].max() if not demand_df.empty else prices_df['timestamp'].max()
        
        self.patterns = {
            'generated_at': datetime.now().isoformat(),
            'data_period': {
                'start': data_start.isoformat(),
                'end': data_end.isoformat(),
                'days': (data_end - data_start).days
            },
            'prices': price_patterns,
            'demand': demand_patterns,
            'correlations': correlations
        }
        
        # Save patterns
        self.save_patterns()
        
        logger.info("=" * 60)
        logger.info("✅ BASELINE PATTERNS LEARNED SUCCESSFULLY")
        logger.info("=" * 60)
        
        return self.patterns
    
    def save_patterns(self):
        """Save learned patterns to JSON file."""
        output_file = self.patterns_dir / "patterns.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)
        
        logger.info(f"💾 Patterns saved to: {output_file}")
    
    def load_patterns(self) -> dict:
        """Load previously learned patterns from JSON file."""
        input_file = self.patterns_dir / "patterns.json"
        
        if not input_file.exists():
            raise FileNotFoundError(f"No patterns file found at {input_file}. Run learn_patterns() first.")
        
        with open(input_file, 'r') as f:
            self.patterns = json.load(f)
        
        logger.info(f"📂 Patterns loaded from: {input_file}")
        return self.patterns
    
    def get_expected_price(self, hour: int, day_of_week: int = None) -> dict:
        """Get expected price statistics for a given hour (and optionally day of week)."""
        if not self.patterns:
            self.load_patterns()
        
        hour_str = str(hour)
        if hour_str in self.patterns['prices']['hourly']:
            return self.patterns['prices']['hourly'][hour_str]
        else:
            return self.patterns['prices']['overall']
    
    def get_expected_demand(self, hour: int, day_of_week: int = None) -> dict:
        """Get expected demand statistics for a given hour (and optionally day of week)."""
        if not self.patterns:
            self.load_patterns()
        
        hour_str = str(hour)
        if hour_str in self.patterns['demand']['hourly']:
            return self.patterns['demand']['hourly'][hour_str]
        else:
            return self.patterns['demand']['overall']
    
    def is_anomalous(self, value: float, hour: int, metric: str = 'price', threshold_std: float = 2.5) -> dict:
        """
        Simple anomaly detection using statistical thresholds.
        
        Args:
            value: Current value to check
            hour: Hour of day (0-23)
            metric: 'price' or 'demand'
            threshold_std: Number of standard deviations for anomaly threshold
        
        Returns:
            dict with is_anomalous, deviation, severity
        """
        if metric == 'price':
            expected = self.get_expected_price(hour)
        else:
            expected = self.get_expected_demand(hour)
        
        mean = expected['mean']
        std = expected['std']
        
        # Calculate deviation in standard deviations
        deviation = (value - mean) / std if std > 0 else 0
        
        # Determine severity
        is_anomalous = abs(deviation) > threshold_std
        
        if abs(deviation) > 3:
            severity = 'critical'
        elif abs(deviation) > 2.5:
            severity = 'high'
        elif abs(deviation) > 2:
            severity = 'medium'
        else:
            severity = 'normal'
        
        return {
            'is_anomalous': is_anomalous,
            'deviation_std': round(deviation, 2),
            'severity': severity,
            'expected_mean': mean,
            'expected_range': (round(mean - 2*std, 2), round(mean + 2*std, 2)),
            'actual_value': value
        }


def main():
    """Run baseline pattern learning."""
    baseline = BaselinePatterns()
    patterns = baseline.learn_patterns()
    
    # Print summary
    print("\n" + "=" * 60)
    print("PATTERN LEARNING SUMMARY")
    print("=" * 60)
    
    if patterns['prices']:
        print(f"\nPrice Patterns:")
        print(f"   Mean: ${patterns['prices']['overall']['mean']:.2f}/MWh")
        print(f"   Range: ${patterns['prices']['overall']['min']:.2f} - ${patterns['prices']['overall']['max']:.2f}")
        print(f"   Peak hours: {patterns['prices']['peak_hours']}")
    else:
        print("\nPrice Patterns: (no data)")
    
    print(f"\nDemand Patterns:")
    print(f"   Mean: {patterns['demand']['overall']['mean']:.0f} MW")
    print(f"   Range: {patterns['demand']['overall']['min']:.0f} - {patterns['demand']['overall']['max']:.0f} MW")
    print(f"   Peak hours: {patterns['demand']['peak_hours']}")
    
    if patterns.get('correlations') and patterns['correlations'].get('price_demand_correlation'):
        print(f"\nCorrelations:")
        print(f"   Price-Demand: {patterns['correlations']['price_demand_correlation']:.3f}")
    
    print("\nBaseline patterns ready for ML training!")
    print("=" * 60)


if __name__ == "__main__":
    main()
