"""
Collect Historical Data for All Months

This script collects historical demand data for each month to train
month-specific anomaly detection models.

Strategy:
- Collect data from the most recent occurrence of each month
- For months in the future (Nov-Dec 2025), collect from previous year
- Aim for ~30 days per month (full month worth of data)
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

sys.path.append(str(Path(__file__).parent))
from caiso_api_client import CAISOClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MonthlyDataCollector:
    """Collect historical data for each month"""
    
    def __init__(self):
        self.caiso_client = CAISOClient()
        self.db_path = Path(__file__).parent / "data" / "historical_data" / "ladwp_grid_data.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def get_collection_plan(self):
        """
        Determine which months to collect and from which year
        
        Current date: October 14, 2025
        
        Available:
        - Jan 2025 (past)
        - Feb 2025 (past)
        - Mar 2025 (past)
        - Apr 2025 (past)
        - May 2025 (past)
        - Jun 2025 (past)
        - Jul 2025 (past)
        - Aug 2025 (past)
        - Sep 2025 (past)
        - Oct 2025 (current - already have 2024+2025 data)
        - Nov 2024 (use previous year)
        - Dec 2024 (use previous year)
        """
        today = datetime.now().date()
        current_year = today.year
        current_month = today.month
        
        collection_plan = []
        
        for month in range(1, 13):
            if month == 10:
                # October - already collected
                logger.info(f"✅ October: Already have data from 2024 + 2025")
                continue
            elif month < current_month:
                # Past months this year
                year = current_year
                # Get full month
                start_date = datetime(year, month, 1).date()
                # Last day of month
                if month == 12:
                    end_date = datetime(year, 12, 31).date()
                else:
                    end_date = (datetime(year, month + 1, 1) - timedelta(days=1)).date()
            else:
                # Future months - use previous year
                year = current_year - 1
                start_date = datetime(year, month, 1).date()
                if month == 12:
                    end_date = datetime(year, 12, 31).date()
                else:
                    end_date = (datetime(year, month + 1, 1) - timedelta(days=1)).date()
            
            collection_plan.append({
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B'),
                'year': year,
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date - start_date).days + 1
            })
        
        return collection_plan
    
    def collect_month_data(self, plan_item):
        """Collect data for a specific month"""
        month_name = plan_item['month_name']
        year = plan_item['year']
        start_date = plan_item['start_date']
        end_date = plan_item['end_date']
        days = plan_item['days']
        
        logger.info(f"=" * 70)
        logger.info(f"COLLECTING: {month_name} {year} ({days} days)")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"=" * 70)
        
        all_data = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                logger.info(f"📅 Fetching {current_date}...")
                df = self.caiso_client.get_system_demand(date=current_date, hours_ahead=24)
                
                if df is not None and not df.empty:
                    # Filter to LADWP
                    if 'TAC_AREA_NAME' in df.columns:
                        df = df[df['TAC_AREA_NAME'] == 'LADWP'].copy()
                    
                    # Standardize column names
                    if 'MW' in df.columns:
                        df['demand_mw'] = pd.to_numeric(df['MW'], errors='coerce')
                    elif 'LOAD' in df.columns:
                        df['demand_mw'] = pd.to_numeric(df['LOAD'], errors='coerce')
                    
                    if 'demand_mw' in df.columns and not df['demand_mw'].isna().all():
                        all_data.append(df)
                        logger.info(f"   ✅ Got {len(df)} records")
                    else:
                        logger.warning(f"   ⚠️  No valid demand data")
                
            except Exception as e:
                logger.error(f"   ❌ Error fetching {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        if not all_data:
            logger.error(f"❌ No data collected for {month_name} {year}")
            return None
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Save to database
        self._save_to_database(combined_df, month_name, year)
        
        logger.info(f"✅ {month_name} {year} complete: {len(combined_df)} records")
        logger.info(f"   Average: {combined_df['demand_mw'].mean():.0f} MW")
        logger.info(f"   Range: {combined_df['demand_mw'].min():.0f} - {combined_df['demand_mw'].max():.0f} MW")
        
        return combined_df
    
    def _save_to_database(self, df, month_name, year):
        """Save collected data to database"""
        conn = sqlite3.connect(self.db_path)
        
        # Prepare data
        df['collected_at'] = datetime.now().isoformat()
        df['area'] = 'LADWP'
        df['market_type'] = 'DAM'
        df['source_month'] = month_name
        df['source_year'] = year
        
        # Insert (using INSERT OR IGNORE to avoid duplicates)
        for _, row in df.iterrows():
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO demand 
                    (timestamp, demand_mw, area, market_type, collected_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(row['timestamp']),  # Convert Timestamp to string
                    float(row['demand_mw']),
                    row['area'],
                    row['market_type'],
                    row['collected_at']
                ))
            except Exception as e:
                logger.error(f"Error inserting row: {e}")
                continue
        
        conn.commit()
        conn.close()
    
    def collect_all(self):
        """Collect data for all months"""
        plan = self.get_collection_plan()
        
        logger.info("=" * 70)
        logger.info("MONTHLY DATA COLLECTION PLAN")
        logger.info("=" * 70)
        logger.info(f"Total months to collect: {len(plan)}")
        logger.info("")
        
        for item in plan:
            logger.info(f"  {item['month']:2d}. {item['month_name']:9s} {item['year']} - {item['days']:2d} days")
        
        logger.info("")
        input("Press Enter to start collection...")
        
        results = {}
        for item in plan:
            month_name = item['month_name']
            df = self.collect_month_data(item)
            if df is not None:
                results[month_name] = {
                    'records': len(df),
                    'avg_mw': df['demand_mw'].mean(),
                    'year': item['year']
                }
        
        # Summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 70)
        
        for month_name, stats in results.items():
            logger.info(f"{month_name:9s} {stats['year']}: {stats['records']:4d} records, Avg: {stats['avg_mw']:.0f} MW")
        
        logger.info("")
        logger.info(f"✅ Total months collected: {len(results)}")
        logger.info(f"✅ Total records: {sum(s['records'] for s in results.values())}")
        logger.info("")
        logger.info("Next step: Run train_all_monthly_models.py")


def main():
    collector = MonthlyDataCollector()
    collector.collect_all()


if __name__ == "__main__":
    main()
