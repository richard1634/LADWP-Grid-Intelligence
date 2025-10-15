# Historical Data Collection

This module collects historical CAISO data and stores it in a SQLite database.

## Quick Start

### 1. Install Dependencies

```bash
pip install pyarrow
```

(pandas and pytz should already be installed from Phase 1)

### 2. Collect Data

**Collect 30 days (recommended for testing):**
```bash
python data/data_collector.py --days 30
```

**Collect 90 days (maximum, best for ML training):**
```bash
python data/data_collector.py --days 90
```

**Collect only prices:**
```bash
python data/data_collector.py --days 30 --prices-only
```

**Collect only demand:**
```bash
python data/data_collector.py --days 30 --demand-only
```

**Export to Parquet files:**
```bash
python data/data_collector.py --days 30 --export
```

### 3. Check Collection Status

```bash
python data/data_collector.py --stats
```

## Database Schema

**Location:** `data/historical_data/ladwp_grid_data.db`

### Tables

**prices**
- timestamp (TEXT, PRIMARY KEY)
- price (REAL) - Total LMP price in $/MWh
- congestion (REAL) - Congestion component
- energy (REAL) - Energy component
- loss (REAL) - Loss component
- node (TEXT) - Pricing node
- collected_at (TEXT) - When data was collected

**demand**
- timestamp (TEXT, PRIMARY KEY)
- demand_mw (REAL) - System demand in MW
- area (TEXT) - TAC area (LADWP)
- market_type (TEXT) - Market type (DAM)
- collected_at (TEXT) - When data was collected

**collection_metadata**
- Tracks all collection runs
- Useful for debugging and monitoring

## Features

✅ Automatic duplicate handling  
✅ Rate limiting (6s between requests)  
✅ Resume capability (won't re-collect existing data)  
✅ Detailed logging to `data/collection.log`  
✅ Export to Parquet for efficient storage  
✅ Collection statistics tracking  

## Expected Collection Times

- **30 days:** ~6 minutes (30 days × 2 endpoints × 6s rate limit)
- **90 days:** ~18 minutes

## Tips

1. **Start with 30 days** for faster initial collection
2. **Run daily** to keep data current (use `--days 1`)
3. **Export to Parquet** for ML training efficiency
4. **Check logs** if errors occur: `data/collection.log`

## Next Steps

After collecting data:
1. Run `--stats` to verify collection
2. Export to Parquet with `--export`
3. Proceed to Step 2: Pattern Baseline Learning

## Troubleshooting

**"No data returned":**
- CAISO may not have data for weekends/holidays
- Try different date ranges

**Rate limit errors:**
- Script already respects 6s rate limit
- If issues persist, check CAISO API status

**Database locked:**
- Close any other programs accessing the database
- Check if collector is already running
