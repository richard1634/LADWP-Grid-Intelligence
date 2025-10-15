"""
Simple test for Day-Ahead Market forecast
"""
from caiso_api_client import CAISOClient
from datetime import datetime, timedelta
import pytz
import pandas as pd

client = CAISOClient()

print("="*60)
print("TESTING DAY-AHEAD MARKET (DAM) FORECAST")
print("="*60)

now = datetime.now(pytz.timezone('America/Los_Angeles'))
start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(hours=72)

params = {
    'queryname': 'SLD_FCST',
    'market_run_id': 'DAM',  # Day-Ahead Market (not RTM)
    'startdatetime': start_time.strftime('%Y%m%dT%H:%M-0000'),
    'enddatetime': end_time.strftime('%Y%m%dT%H:%M-0000'),
    'version': '1',
    'resultformat': '6'
}

print(f"\nFetching SLD_FCST with market_run_id=DAM")
print(f"Time range: {start_time} to {end_time}")

df = client._make_request(params)

if df is not None and not df.empty:
    print(f"\nSUCCESS! Retrieved {len(df)} records")
    
    # Parse timestamps
    if 'INTERVALSTARTTIME_GMT' in df.columns:
        df['timestamp'] = pd.to_datetime(df['INTERVALSTARTTIME_GMT'])
        
        print(f"\nData range:")
        print(f"  Start: {df['timestamp'].min()}")
        print(f"  End:   {df['timestamp'].max()}")
        
        hours_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
        print(f"  Span:  {hours_span:.1f} hours")
        
        # Check future data
        future = df[df['timestamp'] > now]
        if not future.empty:
            future_hours = (future['timestamp'].max() - now).total_seconds() / 3600
            print(f"\nFUTURE DATA: {len(future)} records")
            print(f"Extends {future_hours:.1f} hours into the future!")
            print(f"Forecast ends at: {future['timestamp'].max()}")
else:
    print("\nNo data returned")

print("\n" + "="*60)
