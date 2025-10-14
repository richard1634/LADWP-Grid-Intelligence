"""
Historical Data Collector for LADWP Grid Intelligence
Collects historical price and demand data from CAISO OASIS API
Stores in SQLite database for ML training and analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from caiso_api_client import CAISOClient
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import pytz
import time
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HistoricalDataCollector:
    """Collects and stores historical CAISO data"""
    
    def __init__(self, db_path='data/historical_data/ladwp_grid_data.db'):
        """
        Initialize collector
        
        Args:
            db_path: Path to SQLite database
        """
        self.client = CAISOClient()
        self.db_path = db_path
        self.pacific_tz = pytz.timezone('America/Los_Angeles')
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                timestamp TEXT PRIMARY KEY,
                price REAL NOT NULL,
                congestion REAL,
                energy REAL,
                loss REAL,
                node TEXT,
                collected_at TEXT NOT NULL
            )
        ''')
        
        # Demand table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS demand (
                timestamp TEXT PRIMARY KEY,
                demand_mw REAL NOT NULL,
                area TEXT,
                market_type TEXT,
                collected_at TEXT NOT NULL
            )
        ''')
        
        # Collection metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                records_collected INTEGER NOT NULL,
                collection_time TEXT NOT NULL,
                status TEXT NOT NULL
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_demand_timestamp ON demand(timestamp)')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def collect_historical_prices(self, days_back=30):
        """
        Collect historical price data
        
        Args:
            days_back: Number of days to collect (max 90 for CAISO)
        
        Returns:
            Number of records collected
        """
        logger.info(f"Starting price collection for last {days_back} days...")
        start_time = datetime.now()
        
        # Calculate date range
        end_date = datetime.now(self.pacific_tz).date()
        start_date = end_date - timedelta(days=days_back)
        
        all_data = []
        current_date = start_date
        
        # Collect day by day to avoid overwhelming API
        while current_date <= end_date:
            try:
                logger.info(f"Collecting prices for {current_date}...")
                
                # Get price data for this day
                df = self.client.get_real_time_prices(
                    nodes=['TH_SP15_GEN-APND'],
                    hours_back=24,
                    date=current_date
                )
                
                if df is not None and not df.empty:
                    # Add metadata
                    df['collected_at'] = datetime.now().isoformat()
                    df['node'] = 'TH_SP15_GEN-APND'
                    all_data.append(df)
                    logger.info(f"  Collected {len(df)} records for {current_date}")
                else:
                    logger.warning(f"  No data returned for {current_date}")
                
                # Move to next day
                current_date += timedelta(days=1)
                
                # Respect rate limiting (6 seconds between requests)
                time.sleep(6)
                
            except Exception as e:
                logger.error(f"Error collecting prices for {current_date}: {e}")
                continue
        
        # Combine all data
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            records_saved = self._save_prices_to_db(combined_df)
            
            # Log metadata
            self._log_collection_metadata(
                data_type='prices',
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                records_collected=records_saved,
                collection_time=datetime.now().isoformat(),
                status='success'
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Price collection complete: {records_saved} records in {elapsed:.1f}s")
            return records_saved
        else:
            logger.warning("No price data collected")
            return 0
    
    def collect_historical_demand(self, days_back=30):
        """
        Collect historical demand data
        
        Args:
            days_back: Number of days to collect (max 90 for CAISO)
        
        Returns:
            Number of records collected
        """
        logger.info(f"Starting demand collection for last {days_back} days...")
        start_time = datetime.now()
        
        # Calculate date range
        end_date = datetime.now(self.pacific_tz).date()
        start_date = end_date - timedelta(days=days_back)
        
        all_data = []
        current_date = start_date
        
        # Collect day by day
        while current_date <= end_date:
            try:
                logger.info(f"Collecting demand for {current_date}...")
                
                # Get demand data for this day (LADWP filtering happens in the method)
                df = self.client.get_system_demand(
                    date=current_date,
                    hours_ahead=24
                )
                
                if df is not None and not df.empty:
                    # Add metadata
                    df['collected_at'] = datetime.now().isoformat()
                    # DON'T override area - let the API-provided TAC_AREA_NAME be used
                    # We'll filter to LADWP in _save_demand_to_db
                    if 'TAC_AREA_NAME' in df.columns:
                        df['area'] = df['TAC_AREA_NAME']  # Preserve the actual area
                    df['market_type'] = 'DAM'
                    all_data.append(df)
                    logger.info(f"  Collected {len(df)} records for {current_date}")
                else:
                    logger.warning(f"  No data returned for {current_date}")
                
                # Move to next day
                current_date += timedelta(days=1)
                
                # Respect rate limiting
                time.sleep(6)
                
            except Exception as e:
                logger.error(f"Error collecting demand for {current_date}: {e}")
                continue
        
        # Combine all data
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            records_saved = self._save_demand_to_db(combined_df)
            
            # Log metadata
            self._log_collection_metadata(
                data_type='demand',
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                records_collected=records_saved,
                collection_time=datetime.now().isoformat(),
                status='success'
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Demand collection complete: {records_saved} records in {elapsed:.1f}s")
            return records_saved
        else:
            logger.warning("No demand data collected")
            return 0
    
    def _save_prices_to_db(self, df):
        """Save price data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prepare data
        df_to_save = df.copy()
        
        # Convert timestamp to string BEFORE any operations
        if 'timestamp' in df_to_save.columns:
            df_to_save['timestamp'] = pd.to_datetime(df_to_save['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S%z')
        
        # Rename LMP_PRC to price for consistency
        if 'LMP_PRC' in df_to_save.columns:
            df_to_save['price'] = df_to_save['LMP_PRC']
        
        # Select columns that exist
        columns = ['timestamp', 'price', 'node', 'collected_at']
        # Add optional component columns if they exist
        for col in ['congestion', 'energy', 'loss']:
            if col in df_to_save.columns:
                columns.append(col)
        
        df_to_save = df_to_save[columns]
        
        # Drop rows with missing price
        df_to_save = df_to_save.dropna(subset=['price'])
        
        if df_to_save.empty:
            conn.close()
            logger.warning("No valid price data to save after filtering")
            return 0
        
        # Remove duplicates within the dataframe itself (keep last occurrence)
        df_to_save = df_to_save.drop_duplicates(subset=['timestamp'], keep='last')
        
        # Delete any existing records with these timestamps from database
        timestamps = df_to_save['timestamp'].tolist()
        batch_size = 500
        for i in range(0, len(timestamps), batch_size):
            batch = timestamps[i:i+batch_size]
            placeholders = ','.join(['?'] * len(batch))
            cursor.execute(f'DELETE FROM prices WHERE timestamp IN ({placeholders})', batch)
        conn.commit()
        
        # Now insert (should never have duplicates now)
        df_to_save.to_sql('prices', conn, if_exists='append', index=False)
        
        conn.commit()
        records_saved = len(df_to_save)
        conn.close()
        
        return records_saved
    
    def _save_demand_to_db(self, df):
        """Save demand data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prepare data
        df_to_save = df.copy()
        
        # Convert timestamp to string BEFORE any operations
        if 'timestamp' in df_to_save.columns:
            df_to_save['timestamp'] = pd.to_datetime(df_to_save['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S%z')
        
        # Map demand column - CAISO returns MW or LOAD columns
        if 'demand_mw' not in df_to_save.columns:
            if 'MW' in df_to_save.columns:
                df_to_save['demand_mw'] = pd.to_numeric(df_to_save['MW'], errors='coerce')
            elif 'LOAD' in df_to_save.columns:
                df_to_save['demand_mw'] = pd.to_numeric(df_to_save['LOAD'], errors='coerce')
            elif 'demand' in df_to_save.columns:
                df_to_save['demand_mw'] = df_to_save['demand']
        
        # Map area column
        if 'area' not in df_to_save.columns:
            if 'TAC_AREA_NAME' in df_to_save.columns:
                df_to_save['area'] = df_to_save['TAC_AREA_NAME']
            else:
                df_to_save['area'] = 'LADWP'  # Default
        
        # FILTER TO LADWP ONLY - this is critical!
        df_to_save = df_to_save[df_to_save['area'] == 'LADWP']
        
        if df_to_save.empty:
            conn.close()
            logger.warning("No LADWP data found in this batch")
            return 0
        
        # Map market type
        if 'market_type' not in df_to_save.columns:
            if 'MARKET_RUN_ID' in df_to_save.columns:
                df_to_save['market_type'] = df_to_save['MARKET_RUN_ID']
            else:
                df_to_save['market_type'] = 'DAM'  # Default
        
        # Select columns
        columns = ['timestamp', 'demand_mw', 'area', 'market_type', 'collected_at']
        df_to_save = df_to_save[columns]
        
        # Drop rows with missing demand_mw
        df_to_save = df_to_save.dropna(subset=['demand_mw'])
        
        if df_to_save.empty:
            conn.close()
            logger.warning("No valid demand data to save after filtering")
            return 0
        
        # Remove duplicates within the dataframe itself (keep last occurrence)
        df_to_save = df_to_save.drop_duplicates(subset=['timestamp'], keep='last')
        
        # Delete any existing records with these timestamps from database
        timestamps = df_to_save['timestamp'].tolist()
        batch_size = 500
        for i in range(0, len(timestamps), batch_size):
            batch = timestamps[i:i+batch_size]
            placeholders = ','.join(['?'] * len(batch))
            cursor.execute(f'DELETE FROM demand WHERE timestamp IN ({placeholders})', batch)
        conn.commit()
        
        # Now insert (should never have duplicates now)
        df_to_save.to_sql('demand', conn, if_exists='append', index=False)
        
        conn.commit()
        records_saved = len(df_to_save)
        conn.close()
        
        return records_saved
    
    def _log_collection_metadata(self, data_type, start_date, end_date, 
                                 records_collected, collection_time, status):
        """Log collection metadata for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO collection_metadata 
            (data_type, start_date, end_date, records_collected, collection_time, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data_type, start_date, end_date, records_collected, collection_time, status))
        
        conn.commit()
        conn.close()
    
    def get_collection_stats(self):
        """Get statistics about collected data"""
        conn = sqlite3.connect(self.db_path)
        
        stats = {}
        
        # Price stats
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM prices')
        price_count, price_min, price_max = cursor.fetchone()
        stats['prices'] = {
            'count': price_count or 0,
            'date_range': f"{price_min} to {price_max}" if price_min else "No data"
        }
        
        # Demand stats
        cursor.execute('SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM demand')
        demand_count, demand_min, demand_max = cursor.fetchone()
        stats['demand'] = {
            'count': demand_count or 0,
            'date_range': f"{demand_min} to {demand_max}" if demand_min else "No data"
        }
        
        # Collection history
        cursor.execute('''
            SELECT data_type, COUNT(*) as collections, SUM(records_collected) as total_records
            FROM collection_metadata
            GROUP BY data_type
        ''')
        stats['collection_history'] = cursor.fetchall()
        
        conn.close()
        return stats
    
    def export_to_parquet(self, output_dir='data/historical_data'):
        """Export database to Parquet files for efficient storage"""
        conn = sqlite3.connect(self.db_path)
        
        # Export prices
        prices_df = pd.read_sql('SELECT * FROM prices ORDER BY timestamp', conn)
        if not prices_df.empty:
            prices_df.to_parquet(f'{output_dir}/prices.parquet', index=False)
            logger.info(f"Exported {len(prices_df)} price records to Parquet")
        
        # Export demand
        demand_df = pd.read_sql('SELECT * FROM demand ORDER BY timestamp', conn)
        if not demand_df.empty:
            demand_df.to_parquet(f'{output_dir}/demand.parquet', index=False)
            logger.info(f"Exported {len(demand_df)} demand records to Parquet")
        
        conn.close()


def main():
    """Main entry point for data collection"""
    parser = argparse.ArgumentParser(description='Collect historical CAISO data for LADWP')
    parser.add_argument('--days', type=int, default=30, 
                       help='Number of days to collect (default: 30, max: 90)')
    parser.add_argument('--prices-only', action='store_true',
                       help='Collect only price data')
    parser.add_argument('--demand-only', action='store_true',
                       help='Collect only demand data')
    parser.add_argument('--export', action='store_true',
                       help='Export to Parquet files after collection')
    parser.add_argument('--stats', action='store_true',
                       help='Show collection statistics and exit')
    
    args = parser.parse_args()
    
    collector = HistoricalDataCollector()
    
    # Show stats if requested
    if args.stats:
        stats = collector.get_collection_stats()
        print("\n=== Collection Statistics ===")
        print(f"\nPrices: {stats['prices']['count']} records")
        print(f"  Range: {stats['prices']['date_range']}")
        print(f"\nDemand: {stats['demand']['count']} records")
        print(f"  Range: {stats['demand']['date_range']}")
        print(f"\nCollection History:")
        for data_type, collections, total in stats['collection_history']:
            print(f"  {data_type}: {collections} collections, {total} total records")
        return
    
    # Collect data
    print(f"\n{'='*60}")
    print(f"LADWP Historical Data Collection")
    print(f"Collecting last {args.days} days")
    print(f"{'='*60}\n")
    
    if not args.demand_only:
        collector.collect_historical_prices(days_back=args.days)
    
    if not args.prices_only:
        collector.collect_historical_demand(days_back=args.days)
    
    # Export to Parquet if requested
    if args.export:
        print("\nExporting to Parquet files...")
        collector.export_to_parquet()
    
    # Show final stats
    print("\n" + "="*60)
    stats = collector.get_collection_stats()
    print("\n=== Final Statistics ===")
    print(f"Prices: {stats['prices']['count']} records")
    print(f"Demand: {stats['demand']['count']} records")
    print("="*60 + "\n")
    
    print("✅ Collection complete! Database saved at:")
    print(f"   {os.path.abspath(collector.db_path)}\n")


if __name__ == '__main__':
    main()
