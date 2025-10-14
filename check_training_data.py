import sqlite3
import pandas as pd

conn = sqlite3.connect('data/historical_data/ladwp_grid_data.db')
df = pd.read_sql_query('SELECT * FROM demand_data', conn)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['month'] = df['timestamp'].dt.month

print('\nRecords per month:')
print(df.groupby('month').size())
print(f'\nTotal records: {len(df)}')
print(f'\nDate range: {df["timestamp"].min()} to {df["timestamp"].max()}')
