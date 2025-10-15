"""
Quick test script to check what forecast data range CAISO provides
"""
from caiso_api_client import CAISOClient
from datetime import datetime
import pytz

client = CAISOClient()

print("=" * 60)
print("TESTING CAISO FORECAST DATA RANGE")
print("=" * 60)

# Get demand forecast
print("\n📊 Fetching demand forecast with hours_ahead=48...")
demand_df = client.get_system_demand(hours_ahead=48)

if demand_df is not None and not demand_df.empty:
    print(f"✅ Retrieved {len(demand_df)} records")
    
    if 'timestamp' in demand_df.columns:
        min_time = demand_df['timestamp'].min()
        max_time = demand_df['timestamp'].max()
        now = datetime.now(pytz.timezone('America/Los_Angeles'))
        
        print(f"\n📅 Current Time: {now.strftime('%Y-%m-%d %I:%M %p %Z')}")
        print(f"📅 Data Start:   {min_time.strftime('%Y-%m-%d %I:%M %p %Z')}")
        print(f"📅 Data End:     {max_time.strftime('%Y-%m-%d %I:%M %p %Z')}")
        
        hours_span = (max_time - min_time).total_seconds() / 3600
        hours_ahead = (max_time - now).total_seconds() / 3600
        hours_behind = (now - min_time).total_seconds() / 3600
        
        print(f"\n⏱️  Total Data Span: {hours_span:.1f} hours")
        print(f"⏱️  Hours Behind Now: {hours_behind:.1f} hours")
        print(f"⏱️  Hours Ahead of Now: {hours_ahead:.1f} hours")
        
        # Check if we have future data
        future_data = demand_df[demand_df['timestamp'] > now]
        if not future_data.empty:
            print(f"\n🔮 FUTURE DATA: {len(future_data)} records extending into the future!")
            print(f"   Forecast extends to: {future_data['timestamp'].max().strftime('%Y-%m-%d %I:%M %p')}")
        else:
            print(f"\n❌ NO FUTURE DATA - All data is historical/current only")
    else:
        print("⚠️ No timestamp column found")
        print(f"Available columns: {demand_df.columns.tolist()}")
else:
    print("❌ No data retrieved")

print("\n" + "=" * 60)
