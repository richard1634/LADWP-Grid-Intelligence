# 🚀 QUICK START GUIDE# 🎯 QUICK START GUIDE - Phase 1 Dashboard



## Get Up and Running in 5 Minutes## ⚡ 3 Ways to Experience the Dashboard



------



## 📋 Prerequisites## 🌐 Option 1: Full Interactive Web Dashboard (BEST)



- **Python 3.8+** installed### Launch Command:

- **Node.js 16+** installed (for frontend)```powershell

- **Internet connection** (for CAISO API)cd "c:\Users\leric\Downloads\LADWP"

C:/Python313/python.exe -m streamlit run dashboard.py

---```



## ⚡ Quick Launch### What You'll See:

```

### Option 1: Use the Automated Startup Script (Recommended)┌─────────────────────────────────────────────────────────────────────┐

│  ⚡ LADWP Real-Time Grid Intelligence Dashboard                     │

```powershell│  Live CAISO grid data with intelligent monitoring                   │

cd c:\Users\leric\Downloads\LADWP├─────────────────────────────────────────────────────────────────────┤

.\start.ps1│                                                                      │

```│  📊 Current Grid Status                                              │

│  ┌───────────────┬───────────────┬───────────────┬───────────────┐ │

This will:│  │ System Demand │ Energy Price  │  Grid Stress  │ Last Updated  │ │

1. ✅ Start the FastAPI backend server (port 8000)│  │  45,230 MW    │ $78.50/MWh    │  🟡 Moderate  │   2:15 PM     │ │

2. ✅ Start the React frontend dev server (port 5173)│  └───────────────┴───────────────┴───────────────┴───────────────┘ │

3. ✅ Open your browser automatically to http://localhost:5173│                                                                      │

│  💰 Real-Time Energy Prices                                          │

### Option 2: Manual Launch│  [Interactive Chart: 6-hour price trends with spike detection]      │

│  [Shows: Price spikes, volatility, typical ranges]                  │

**Terminal 1 - Backend:**│                                                                      │

```powershell│  📈 System Demand Forecast                                           │

cd c:\Users\leric\Downloads\LADWP│  [24-hour demand curve with peak identification]                    │

python -m uvicorn api_server:app --reload --port 8000│                                                                      │

```│  🎯 Operational Intelligence & Recommendations                       │

│  ⚠️ High Energy Prices - Consider demand response activation        │

**Terminal 2 - Frontend:**│  💡 3 price spikes detected - Review real-time operations           │

```powershell│                                                                      │

cd c:\Users\leric\Downloads\LADWP\frontend└─────────────────────────────────────────────────────────────────────┘

npm run dev```

```

### Features:

Then open: **http://localhost:5173**- ✅ Interactive charts (zoom, pan, hover for details)

- ✅ Auto-refresh every 1-5 minutes

---- ✅ Real-time alerts and recommendations

- ✅ Export data functionality

## 🎯 What You'll See- ✅ Mobile-responsive design



### Dashboard Tabs### Browser Opens Automatically at:

**http://localhost:8501**

**1. ⚡ Demand & AI Analysis (Default)**

- Real-time grid demand and status---

- 30-hour demand forecast

- ML anomaly detection chart## 💻 Option 2: Command-Line Demo (QUICK)

- AI-powered recommendations

- Severity indicators### Launch Command:

```powershell

**2. 💰 Price Analysis**cd "c:\Users\leric\Downloads\LADWP"

- Real-time energy prices (LMP)C:/Python313/python.exe demo_phase1.py

- 6-hour price trend chart```

- Price spike detection

- Component breakdown (Energy/Congestion/Loss)### What You'll See:

- Volatility metrics```

================================================================================

### Key Features  ⚡ LADWP REAL-TIME GRID INTELLIGENCE DASHBOARD - PHASE 1 DEMO

- 🔄 Auto-refreshes every 5 minutes================================================================================

- 🤖 12 month-specific ML models (auto-selected)

- 📊 Interactive charts with zoom/pan📅 Demo Running: Monday, October 13, 2025 at 03:15 PM Pacific

- 💡 Actionable recommendations🔌 Data Source: CAISO OASIS API (Live Production Data)

- ⚠️ Real-time alerts

────────────────────────────────────────────────────────────────────────────────

---  📊 SECTION 1: Current Grid Status Overview

────────────────────────────────────────────────────────────────────────────────

## 🔧 First-Time Setup

🔋 SYSTEM DEMAND: 43,250 MW

### 1. Install Python Dependencies💰 ENERGY PRICE: $68.50/MWh

⚠️  GRID STRESS: 🟢 Normal

```powershell

cd c:\Users\leric\Downloads\LADWP💡 OPERATIONAL GUIDANCE:

pip install -r requirements.txt   ✅ Grid operating within normal parameters

```   ✅ Standard operations - no special actions required



### 2. Install Frontend Dependencies────────────────────────────────────────────────────────────────────────────────

  📈 SECTION 2: Real-Time Price Analysis

```powershell────────────────────────────────────────────────────────────────────────────────

cd frontend

npm install💵 PRICE STATISTICS (Last 6 Hours):

```   Current Price: $68.50/MWh

   Average Price: $52.30/MWh

### 3. (Optional) Setup API Key for AI Recommendations   Min / Max: $38.20 / $95.70

   Volatility (σ): $12.45

```powershell

# Copy the example file🎯 ANOMALY DETECTION:

Copy-Item setup_api_key.example.ps1 setup_api_key.ps1   ⚠️  2 PRICE SPIKE(S) DETECTED!

   📊 Spike Analysis:

# Edit setup_api_key.ps1 and add your OpenAI API key      • $95.70/MWh (Severity: 3.2σ)

# Then run:      • $87.30/MWh (Severity: 2.4σ)

.\setup_api_key.ps1

```   💡 RECOMMENDATION:

      This indicates unusual grid conditions.

**Note:** AI recommendations work without an API key (falls back to rule-based system)      Review operations and consider demand response activation.



---💰 COST SAVINGS OPPORTUNITY:

   ✅ Prices in normal range

## 🧪 Test the System      No immediate optimization opportunity



### Check if Backend is Running────────────────────────────────────────────────────────────────────────────────

Open in browser: http://localhost:8000/api/health  💎 SECTION 4: Business Value Summary

────────────────────────────────────────────────────────────────────────────────

Expected response:

```json🎯 HOW THIS DASHBOARD CREATES VALUE FOR LADWP:

{

  "status": "healthy",1️⃣  COST AVOIDANCE

  "caiso_api": "connected",   • Real-time price visibility prevents buying at peak

  "models_loaded": true   • Example: Avoiding 2 hrs/day at high prices = $8.1M/year savings

}

```2️⃣  OPERATIONAL OPTIMIZATION

   • Shift pumping to low-price periods

### Check ML Predictions   • Example: 500 MW shifted saves $180k/day = $65.7M/year

http://localhost:8000/api/ml-predictions

3️⃣  GRID RELIABILITY

Should return JSON with anomaly predictions for the next 30 hours.   • Early warning of stress conditions (30-60 min advance)

   • Proactive demand response prevents blackouts

---

4️⃣  DATA-DRIVEN DECISIONS

## 📊 Understanding the Dashboard   • Single pane of glass for all grid metrics

   • Faster response times (5 min vs 30 min)

### Grid Status Indicator

- 🟢 **Normal** - Grid operating normally💰 ESTIMATED ROI:

- 🟡 **Moderate** - Elevated demand or prices   Annual Cost Savings: $15M - $85M

- 🟠 **High** - Significant stress conditions   Implementation Cost: $10k/year

- 🔴 **Critical** - Emergency conditions   Return on Investment: 150,000% - 850,000%

   Payback Period: Less than 1 day

### ML Anomaly Severity

- **Normal** - Expected demand patterns================================================================================

- **Low** - Minor deviation (monitoring)  ✅ PHASE 1 DEMO COMPLETE

- **Medium** - Unusual pattern (attention)================================================================================

- **High** - Significant anomaly (action required)```



### Confidence Scores### Features:

- **>80%** - Very high confidence- ✅ Quick overview of all functionality

- **60-80%** - High confidence- ✅ Real CAISO data analysis

- **40-60%** - Moderate confidence- ✅ Business value calculations

- **<40%** - Low confidence (may be false positive)- ✅ No browser needed

- ✅ Perfect for presentations

---

---

## 🆘 Troubleshooting

## 🔧 Option 3: API Connection Test (VERIFY)

### Backend won't start

```powershell### Launch Command:

# Check if port 8000 is already in use```powershell

netstat -ano | findstr :8000cd "c:\Users\leric\Downloads\LADWP"

C:/Python313/python.exe test_api.py

# Kill process if needed```

taskkill /PID <process_id> /F

```### What You'll See:

```

### Frontend won't start============================================================

```powershellCAISO OASIS API Connection Test

# Clear cache and reinstall============================================================

cd frontend

Remove-Item -Recurse -Force node_modules⏰ Current Time (Pacific): 2025-10-13 03:01 PM

npm install

```📊 Test 1: Fetching System Load Forecast...

   ✅ SUCCESS - Status Code: 200

### No ML predictions showing   📦 Response Size: 140,117 bytes

```powershell

# Generate predictions manually💰 Test 2: Fetching Real-Time Prices...

cd c:\Users\leric\Downloads\LADWP   ✅ SUCCESS - Status Code: 200

python scripts/generate_all_predictions.py   📦 Response Size: 1,572 bytes

```   📈 Records Retrieved: 24

   💵 Average Price: $52.34/MWh

### "Month model not found" error

```powershell============================================================

# Retrain all monthly models✅ API Test Complete!

python scripts/train_all_monthly_models.py============================================================

```

🚀 Next Step: Run the dashboard with: 

---   C:/Python313/python.exe -m streamlit run dashboard.py

```

## 📚 Next Steps

### Features:

### Learn More- ✅ Verifies CAISO API connectivity

- **Full Documentation**: See `README.md`- ✅ Tests data retrieval

- **ML System Details**: See `docs/MONTHLY_MODELS_GUIDE.md`- ✅ Shows sample data

- **Operational Guide**: See `docs/USAGE_GUIDE.md`- ✅ Quick diagnostics

- **AI Recommendations**: See `docs/AI_ANOMALY_RECOMMENDATIONS.md`- ✅ 30-second test



### Maintenance Tasks---

- **Monthly**: Retrain models with latest data (`scripts/retrain_all.py`)

- **Daily**: Generate fresh predictions (`scripts/generate_all_predictions.py`)## 📊 What Each Option Is Best For

- **As Needed**: Collect historical data (`scripts/collect_all_months.py`)

| Option | Best For | Time Required | Output |

### Testing|--------|----------|---------------|--------|

- **Month Transitions**: `python tests/test_month_transition.py`| **Web Dashboard** | Daily operations, monitoring | Ongoing | Interactive UI |

- **Baseline Validation**: `python tests/test_november_baseline.py`| **Command-Line Demo** | Presentations, demos | 2 minutes | Terminal output |

- **API Testing**: Open `tests/test_api.html` in browser| **API Test** | Verification, debugging | 30 seconds | Connection status |



------



## 🎉 You're Ready!## 💡 Recommended First Steps



Your LADWP Grid Intelligence Dashboard is now running with:### Step 1: Verify API (30 seconds)

✅ Real-time CAISO data```powershell

✅ ML-powered anomaly detectionC:/Python313/python.exe test_api.py

✅ AI-driven recommendations```

✅ Interactive visualizations✅ Confirms CAISO connection works



**Start monitoring the grid and optimize your operations!**### Step 2: See the Value (2 minutes)

```powershell
C:/Python313/python.exe demo_phase1.py
```
✅ Shows real data + ROI calculations

### Step 3: Experience Full Dashboard (Ongoing)
```powershell
C:/Python313/python.exe -m streamlit run dashboard.py
```
✅ Use for actual operations

---

## 🎯 Key Files Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `dashboard.py` | Main web dashboard | Daily operations |
| `demo_phase1.py` | Command-line demo | Presentations |
| `test_api.py` | API connectivity test | Troubleshooting |
| `caiso_api_client.py` | API integration library | Development |
| `PHASE1_COMPLETE.md` | This summary | Understanding value |
| `USAGE_GUIDE.md` | Detailed scenarios | Training operators |
| `README.md` | Technical docs | Developers |

---

## 🚨 Troubleshooting

### Dashboard won't start?
```powershell
# Make sure packages are installed
C:/Python313/python.exe -m pip install streamlit pandas numpy requests plotly pytz

# Then try again
C:/Python313/python.exe -m streamlit run dashboard.py
```

### API returning no data?
- Normal during CAISO maintenance windows (usually 2-4 AM)
- Try different time of day
- Check internet connection

### Browser doesn't open?
- Manually navigate to: http://localhost:8501
- Or try: http://127.0.0.1:8501

---

## 📈 What Success Looks Like

### Week 1:
- ✅ Dashboard running 24/7
- ✅ 2-3 operators trained
- ✅ First cost avoidance event ($50k saved)

### Month 1:
- ✅ All operators using daily
- ✅ Pumping optimization in place ($2M saved)
- ✅ Management briefed on results

### Quarter 1:
- ✅ Demand response integrated
- ✅ ML predictions added (Phase 2)
- ✅ $10-20M documented savings

---

## 🎉 You're Ready!

Everything is installed and ready to go.

Choose your option and launch the dashboard! 🚀

**The grid intelligence revolution starts now!** ⚡
