"""
CAISO OASIS API Client
Fetches real-time grid data from California ISO's public API

Features:
- Rate limiting to avoid 429 errors
- Response caching to reduce API calls
- Automatic retry with exponential backoff
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
from typing import Optional, Dict, List
import time
import hashlib
import json


class CAISOClient:
    """Client for fetching data from CAISO OASIS API with rate limiting and caching"""
    
    BASE_URL = "http://oasis.caiso.com/oasisapi/SingleZip"
    
    # LADWP Load Aggregation Points (LAPs)
    LADWP_NODES = {
        "DLAP_LADWP": "LADWP Distribution Load Aggregation Point",
        "TH_NP15_GEN-APND": "NP15 Trading Hub (LADWP participates)",
        "TH_SP15_GEN-APND": "SP15 Trading Hub (LADWP participates)",
    }
    
    # Rate limiting configuration
    MIN_REQUEST_INTERVAL = 5.0  # Minimum 5 seconds between requests (safe)
    MAX_RETRIES = 3
    RETRY_DELAY = 10.0  # Start with 10 second delay
    
    # Cache configuration
    CACHE_DURATION = 600  # Cache responses for 10 minutes (600 seconds)
    
    def __init__(self):
        self.session = requests.Session()
        self.pacific_tz = pytz.timezone('America/Los_Angeles')
        self.last_request_time = 0
        self.cache = {}  # Simple in-memory cache: {cache_key: (data, timestamp)}
        
    def _get_cache_key(self, params: Dict) -> str:
        """Generate a unique cache key from request parameters"""
        # Sort params for consistent hashing
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Retrieve data from cache if still valid"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            age = time.time() - timestamp
            
            if age < self.CACHE_DURATION:
                print(f"   ✅ Using cached data (age: {age:.0f}s)")
                # Return a copy to avoid modifying cached data
                return data.copy() if data is not None else None
            else:
                # Remove stale cache entry
                del self.cache[cache_key]
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: pd.DataFrame):
        """Save data to cache with current timestamp"""
        # Store a copy to avoid external modifications affecting cache
        self.cache[cache_key] = (data.copy() if data is not None else None, time.time())
        
        # Simple cache cleanup: remove entries older than 2x cache duration
        current_time = time.time()
        expired_keys = [
            key for key, (_, ts) in self.cache.items()
            if current_time - ts > self.CACHE_DURATION * 2
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _wait_for_rate_limit(self):
        """Ensure minimum time between requests to avoid rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.MIN_REQUEST_INTERVAL:
            sleep_time = self.MIN_REQUEST_INTERVAL - time_since_last
            print(f"   ⏳ Rate limit: Waiting {sleep_time:.1f}s...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict, retry_count: int = 0) -> Optional[pd.DataFrame]:
        """
        Make API request with rate limiting, caching, and retry logic
        
        Args:
            params: API request parameters
            retry_count: Current retry attempt number
            
        Returns:
            DataFrame with response data, or None if request fails
        """
        # Check cache first
        cache_key = self._get_cache_key(params)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Apply rate limiting
        self._wait_for_rate_limit()
        
        try:
            print(f"   📡 Fetching from CAISO API...")
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            
            # Handle rate limiting (429 Too Many Requests)
            if response.status_code == 429:
                if retry_count < self.MAX_RETRIES:
                    retry_delay = self.RETRY_DELAY * (2 ** retry_count)  # Exponential backoff
                    print(f"   ⚠️  Rate limited (429). Retrying in {retry_delay:.0f}s... (Attempt {retry_count + 1}/{self.MAX_RETRIES})")
                    time.sleep(retry_delay)
                    return self._make_request(params, retry_count + 1)
                else:
                    print(f"   ❌ Rate limit exceeded. Max retries reached.")
                    return None
            
            response.raise_for_status()
            
            # CAISO returns CSV in ZIP format
            if response.content:
                # Read CSV directly from response
                from io import BytesIO
                import zipfile
                
                with zipfile.ZipFile(BytesIO(response.content)) as zf:
                    # Get the first CSV file in the zip
                    csv_filename = zf.namelist()[0]
                    with zf.open(csv_filename) as csv_file:
                        df = pd.read_csv(csv_file)
                        
                        # Save to cache
                        self._save_to_cache(cache_key, df)
                        print(f"   ✅ Data retrieved ({len(df)} records)")
                        
                        return df
            return None
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and retry_count < self.MAX_RETRIES:
                # Additional handling for 429 in exception
                retry_delay = self.RETRY_DELAY * (2 ** retry_count)
                print(f"   ⚠️  Rate limited. Retrying in {retry_delay:.0f}s...")
                time.sleep(retry_delay)
                return self._make_request(params, retry_count + 1)
            else:
                print(f"   ❌ HTTP Error: {e}")
                return None
        except Exception as e:
            print(f"   ❌ API Request Error: {e}")
            return None
    
    def get_system_demand(self, date: Optional[datetime] = None, hours_ahead: int = 48) -> pd.DataFrame:
        """
        Get CAISO system demand (load) forecast data
        Query: SLD_FCST (System Load Forecast)
        
        Args:
            date: Start date for forecast (default: now)
            hours_ahead: How many hours ahead to forecast (default: 48 for 2 days)
        
        Note: Uses DAM (Day-Ahead Market) which provides ~30 hours of future forecasts,
              vs RTM (Real-Time Market) which only provides ~30 minutes ahead
        """
        if date is None:
            date = datetime.now(self.pacific_tz)
        
        # Convert date to datetime if needed
        if isinstance(date, datetime):
            start_time = date.replace(hour=0, minute=0, second=0)
        else:
            # date is a date object, convert to datetime
            start_time = datetime.combine(date, datetime.min.time())
            start_time = self.pacific_tz.localize(start_time)
        
        # For current/future forecasts, get from start of day to hours_ahead in the future
        end_time = start_time + timedelta(hours=hours_ahead)
        
        params = {
            'queryname': 'SLD_FCST',  # System Load Forecast
            'market_run_id': 'DAM',    # Day-Ahead Market (provides ~30h ahead forecast)
            'startdatetime': start_time.strftime('%Y%m%dT%H:%M-0000'),
            'enddatetime': end_time.strftime('%Y%m%dT%H:%M-0000'),
            'version': '1',
            'resultformat': '6'  # CSV format
        }
        
        df = self._make_request(params)
        if df is not None and not df.empty:
            # Process timestamp - try multiple possible column names
            if 'timestamp' not in df.columns:
                timestamp_col = None
                for col_name in ['INTERVALSTARTTIME_GMT', 'INTERVAL_START_GMT', 'INTERVALSTARTTIME', 'OPR_DT']:
                    if col_name in df.columns:
                        timestamp_col = col_name
                        break
                
                if timestamp_col:
                    try:
                        df['timestamp'] = pd.to_datetime(df[timestamp_col])
                        if 'GMT' in timestamp_col or 'UTC' in timestamp_col:
                            # Check if already timezone-aware
                            if df['timestamp'].dt.tz is None:
                                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(self.pacific_tz)
                            else:
                                df['timestamp'] = df['timestamp'].dt.tz_convert(self.pacific_tz)
                        print(f"   ✅ Processed timestamps from column: {timestamp_col}")
                    except Exception as e:
                        print(f"   ⚠️  Warning: Could not process timestamps from {timestamp_col}: {e}")
                    
                    # Show data range regardless of timezone processing success/failure
                    if 'timestamp' in df.columns and not df.empty:
                        try:
                            print(f"   📅 Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                            hours_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
                            print(f"   ⏱️  Span: {hours_span:.1f} hours ({len(df)} records)")
                        except:
                            pass
        
        return df
    
    def get_real_time_prices(self, nodes: Optional[List[str]] = None, 
                            hours_back: int = 6,
                            date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get Real-Time Locational Marginal Prices (LMP)
        Query: PRC_INTVL_LMP (5-minute interval prices)
        
        Args:
            nodes: List of pricing nodes to query
            hours_back: Number of hours to look back from end_time
            date: Specific date to query (if None, uses current time)
        """
        if nodes is None:
            nodes = list(self.LADWP_NODES.keys())
        
        # If date is specified, use that date's data
        if date is not None:
            # Get data for the entire specified day
            # Convert date to datetime if needed
            if isinstance(date, datetime):
                start_time = date.replace(hour=0, minute=0, second=0)
                end_time = date.replace(hour=23, minute=59, second=59)
            else:
                # date is a date object, convert to datetime
                start_time = datetime.combine(date, datetime.min.time())
                start_time = self.pacific_tz.localize(start_time)
                end_time = datetime.combine(date, datetime.max.time())
                end_time = self.pacific_tz.localize(end_time)
        else:
            # Use current time and look back
            end_time = datetime.now(self.pacific_tz)
            start_time = end_time - timedelta(hours=hours_back)
        
        params = {
            'queryname': 'PRC_INTVL_LMP',
            'market_run_id': 'RTM',
            'node': ','.join(nodes),
            'startdatetime': start_time.strftime('%Y%m%dT%H:%M-0000'),
            'enddatetime': end_time.strftime('%Y%m%dT%H:%M-0000'),
            'version': '1',
            'resultformat': '6'
        }
        
        df = self._make_request(params)
        if df is not None and not df.empty:
            # Process timestamp - try multiple possible column names
            if 'timestamp' not in df.columns:
                timestamp_col = None
                for col_name in ['INTERVALSTARTTIME_GMT', 'INTERVAL_START_GMT', 'INTERVALSTARTTIME', 'OPR_DT']:
                    if col_name in df.columns:
                        timestamp_col = col_name
                        break
                
                if timestamp_col:
                    try:
                        df['timestamp'] = pd.to_datetime(df[timestamp_col])
                        if 'GMT' in timestamp_col or 'UTC' in timestamp_col:
                            # Check if already timezone aware
                            if df['timestamp'].dt.tz is None:
                                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(self.pacific_tz)
                            else:
                                df['timestamp'] = df['timestamp'].dt.tz_convert(self.pacific_tz)
                        print(f"   ✅ Processed timestamps from column: {timestamp_col}")
                    except Exception as e:
                        print(f"   ⚠️  Warning: Could not process timestamps from {timestamp_col}: {e}")
            
            # Process price columns - CAISO returns price data in MW column with XML_DATA_ITEM label
            # First, filter to only LMP_PRC rows (not congestion or loss components)
            if 'XML_DATA_ITEM' in df.columns:
                df = df[df['XML_DATA_ITEM'] == 'LMP_PRC'].copy()
                print(f"   ✅ Filtered to LMP_PRC data type ({len(df)} records)")
            
            # Then filter for total LMP only (not components)
            if 'LMP_TYPE' in df.columns:
                df = df[df['LMP_TYPE'] == 'LMP'].copy()
                print(f"   ✅ Filtered to LMP total prices ({len(df)} records)")
            
            # Now map MW column to LMP_PRC (MW contains the actual price values)
            if 'LMP_PRC' not in df.columns and 'MW' in df.columns:
                df['LMP_PRC'] = pd.to_numeric(df['MW'], errors='coerce')
                print(f"   ✅ Mapped price column: MW → LMP_PRC")
        
        return df
    
    def get_transmission_constraints(self) -> pd.DataFrame:
        """
        Get active transmission constraints
        Query: PRC_CNSTR_SHAD_PRC (Constraint Shadow Prices)
        """
        end_time = datetime.now(self.pacific_tz)
        start_time = end_time - timedelta(hours=2)
        
        params = {
            'queryname': 'PRC_INTVL_LMP',  # We'll use LMP congestion component
            'market_run_id': 'RTM',
            'startdatetime': start_time.strftime('%Y%m%dT%H:%M-0000'),
            'enddatetime': end_time.strftime('%Y%m%dT%H:%M-0000'),
            'version': '1',
            'resultformat': '6'
        }
        
        return self._make_request(params)
    
    def get_renewable_generation(self) -> pd.DataFrame:
        """
        Get wind and solar generation forecast
        Query: SLD_REN_FCST (Renewable Forecast)
        """
        date = datetime.now(self.pacific_tz)
        date_str = date.strftime('%Y%m%d')
        
        params = {
            'queryname': 'SLD_REN_FCST',
            'market_run_id': 'RTM',
            'startdatetime': f'{date_str}T00:00-0000',
            'enddatetime': f'{date_str}T23:59-0000',
            'version': '1',
            'resultformat': '6'
        }
        
        return self._make_request(params)
    
    def get_interface_flows(self) -> pd.DataFrame:
        """
        Get transmission interface flow data
        """
        end_time = datetime.now(self.pacific_tz)
        start_time = end_time - timedelta(hours=4)
        
        params = {
            'queryname': 'TRNS_INTERFACE',
            'startdatetime': start_time.strftime('%Y%m%dT%H:%M-0000'),
            'enddatetime': end_time.strftime('%Y%m%dT%H:%M-0000'),
            'version': '1',
            'resultformat': '6'
        }
        
        return self._make_request(params)
    
    def get_current_grid_status(self) -> Dict:
        """
        Get comprehensive current grid status
        Returns a summary of key metrics
        """
        status = {
            'timestamp': datetime.now(self.pacific_tz),
            'demand_mw': None,
            'avg_price_per_mwh': None,
            'price_range': None,
            'renewable_pct': None,
            'constraints_active': 0,
            'status': 'Normal'
        }
        
        try:
            # Get latest demand
            demand_df = self.get_system_demand()
            if demand_df is not None and not demand_df.empty:
                latest_demand = demand_df.iloc[-1]
                if 'MW' in latest_demand:
                    status['demand_mw'] = float(latest_demand['MW'])
            
            # Get latest prices
            price_df = self.get_real_time_prices(hours_back=1)
            if price_df is not None and not price_df.empty:
                if 'LMP_PRC' in price_df.columns:
                    status['avg_price_per_mwh'] = price_df['LMP_PRC'].mean()
                    status['price_range'] = (price_df['LMP_PRC'].min(), 
                                           price_df['LMP_PRC'].max())
            
            # Determine status based on prices
            if status['avg_price_per_mwh']:
                if status['avg_price_per_mwh'] > 100:
                    status['status'] = 'High Prices - Potential Stress'
                elif status['avg_price_per_mwh'] < 0:
                    status['status'] = 'Negative Prices - Oversupply'
                    
        except Exception as e:
            print(f"Error getting grid status: {e}")
        
        return status


# Utility functions for data analysis
def calculate_price_volatility(df: pd.DataFrame, window: int = 12) -> pd.Series:
    """Calculate rolling price volatility (standard deviation)"""
    if 'LMP_PRC' in df.columns:
        return df['LMP_PRC'].rolling(window=window).std()
    return pd.Series()


def detect_price_spikes(df: pd.DataFrame, threshold_std: float = 2.5) -> pd.DataFrame:
    """
    Detect price spikes using rolling window statistical threshold
    This accounts for normal daily price variations (morning ramp, evening peak)
    
    Returns DataFrame with spike indicators
    """
    if df is None or df.empty or 'LMP_PRC' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    
    # Sort by timestamp if available
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')
    
    # Use rolling window to detect sudden changes (30-minute window = ~6 records at 5-min intervals)
    window_size = 6
    
    if len(df) >= window_size:
        # Calculate rolling mean and std
        df['rolling_mean'] = df['LMP_PRC'].rolling(window=window_size, center=True).mean()
        df['rolling_std'] = df['LMP_PRC'].rolling(window=window_size, center=True).std()
        
        # Fill NaN values at edges with overall statistics
        df['rolling_mean'] = df['rolling_mean'].fillna(df['LMP_PRC'].mean())
        df['rolling_std'] = df['rolling_std'].fillna(df['LMP_PRC'].std())
        
        # Detect spikes as deviations from local rolling average
        df['spike_severity'] = (df['LMP_PRC'] - df['rolling_mean']) / (df['rolling_std'] + 0.01)  # +0.01 to avoid div by zero
        df['is_spike'] = abs(df['spike_severity']) > threshold_std
    else:
        # Fallback to simple method for small datasets
        mean_price = df['LMP_PRC'].mean()
        std_price = df['LMP_PRC'].std()
        
        df['is_spike'] = abs(df['LMP_PRC'] - mean_price) > (threshold_std * std_price)
        df['spike_severity'] = (df['LMP_PRC'] - mean_price) / (std_price + 0.01)
    
    return df[df['is_spike']]


def calculate_grid_stress_score(demand_mw: float, price_per_mwh: float) -> Dict:
    """
    Calculate a simple grid stress score based on demand and price
    """
    stress_score = 0
    factors = []
    
    # High demand indicator (CAISO peak is typically 40,000-50,000 MW)
    if demand_mw:
        if demand_mw > 45000:
            stress_score += 3
            factors.append("Very High Demand")
        elif demand_mw > 40000:
            stress_score += 2
            factors.append("High Demand")
    
    # High price indicator
    if price_per_mwh:
        if price_per_mwh > 150:
            stress_score += 3
            factors.append("Very High Prices")
        elif price_per_mwh > 100:
            stress_score += 2
            factors.append("High Prices")
        elif price_per_mwh > 75:
            stress_score += 1
            factors.append("Elevated Prices")
    
    # Categorize stress level
    if stress_score >= 5:
        level = "Critical"
    elif stress_score >= 3:
        level = "High"
    elif stress_score >= 1:
        level = "Moderate"
    else:
        level = "Normal"
    
    return {
        'score': stress_score,
        'level': level,
        'factors': factors
    }
