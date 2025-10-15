"""
Test script to explore CAISO Day-Ahead forecast queries
"""
from caiso_api_client import CAISOClient
from datetime import datetime, timedelta
import pytz
import pandas as pd

client = CAISOClient()

print("=" * 70)
print("TESTING CAISO DAY-AHEAD FORECAST QUERIES")
print("=" * 70)

# Try different forecast query names
forecast_queries = [
    ('SYS_FCST_DA', 'System Forecast - Day Ahead'),
    ('SLD_FCST', 'System Load Forecast (current query)'),
    ('SLD_REN_FCST', 'System Load & Renewable Forecast'),
    ('ENE_SLRS', 'Energy Solar Forecast'),
    ('ENE_WIND_SOLAR_SUMMARY', 'Wind & Solar Summary'),
]

now = datetime.now(pytz.timezone('America/Los_Angeles'))
tomorrow = now + timedelta(days=1)

for query_name, description in forecast_queries:
    print(f"\n{'='*70}")
    print(f"📊 Testing: {query_name} - {description}")
    print(f"{'='*70}")
    
    # Try to fetch with extended time range
    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=72)  # Try 3 days
    
    params = {
        'queryname': query_name,
        'market_run_id': 'DAM',  # Day-Ahead Market
        'startdatetime': start_time.strftime('%Y%m%dT%H:%M-0000'),
        'enddatetime': end_time.strftime('%Y%m%dT%H:%M-0000'),
        'version': '1',
        'resultformat': '6'
    }
    
    print(f"   Query: {query_name}")
    print(f"   Market: DAM (Day-Ahead Market)")
    print(f"   Range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
    
    try:
        df = client._make_request(params)
        
        if df is not None and not df.empty:
            print(f"   ✅ SUCCESS! Retrieved {len(df)} records")
            print(f"   Columns: {', '.join(df.columns.tolist()[:10])}")
            
            # Try to find timestamp column
            timestamp_cols = [col for col in df.columns if 'TIME' in col.upper() or 'DATE' in col.upper()]
            if timestamp_cols:
                print(f"   Time columns: {', '.join(timestamp_cols)}")
                
                # Try to parse first timestamp column
                try:
                    ts_col = timestamp_cols[0]
                    df['temp_ts'] = pd.to_datetime(df[ts_col])
                    print(f"   📅 Data range: {df['temp_ts'].min()} to {df['temp_ts'].max()}")
                    hours_span = (df['temp_ts'].max() - df['temp_ts'].min()).total_seconds() / 3600
                    print(f"   ⏱️  Span: {hours_span:.1f} hours")
                    
                    # Check for future data
                    future_records = df[df['temp_ts'] > now]
                    if not future_records.empty:
                        future_hours = (future_records['temp_ts'].max() - now).total_seconds() / 3600
                        print(f"   🔮 FUTURE DATA: {len(future_records)} records, extends {future_hours:.1f} hours ahead!")
                    else:
                        print(f"   ⚠️  No future data found")
                except Exception as e:
                    print(f"   ⚠️  Could not parse timestamps: {e}")
        else:
            print(f"   ❌ No data returned (may not be valid query)")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("Check which queries returned data and how far ahead they forecast!")
