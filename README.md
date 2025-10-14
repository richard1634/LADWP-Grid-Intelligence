# LADWP Real-Time Grid Intelligence Dashboard

## 🎯 Phase 1: Real-Time CAISO Grid Monitoring

A production-ready dashboard that provides LADWP operators with real-time visibility into California ISO (CAISO) grid conditions, enabling proactive decision-making and operational optimization.

---

## 🚀 Why This Dashboard is Valuable

### **Problem It Solves**
Traditional grid operations rely on:
- **Static SCADA alarms** - Reactive, not predictive
- **Manual data checking** - Time-consuming and error-prone
- **Delayed information** - By the time you see issues, it's too late
- **Siloed data** - Prices, demand, and constraints viewed separately

### **Our Solution**
✅ **Real-time intelligence** - Live CAISO data updated every 5 minutes  
✅ **Proactive alerts** - Detect price spikes and grid stress before they escalate  
✅ **Unified view** - All critical metrics in one dashboard  
✅ **Actionable insights** - Specific recommendations for operators  
✅ **Cost savings** - Avoid high-price periods, optimize operations  

---

## 💰 Business Value for LADWP

### **1. Cost Avoidance**
- **Detect high-price periods early** → Reduce load or shift to storage
- **Example**: Avoiding just 2 hours/day of $150/MWh vs $50/MWh prices on 1,000 MW load = **$73M annual savings**

### **2. Operational Efficiency**
- **Single pane of glass** for grid conditions
- **Reduce operator workload** - Automated monitoring vs manual checks
- **Faster response times** - See issues immediately

### **3. Grid Reliability**
- **Anticipate stress conditions** before they become emergencies
- **Proactive demand response** - Activate programs before system strain
- **Better coordination with CAISO** - Real-time awareness of grid status

### **4. Regulatory Compliance**
- **Automated logging** of grid events
- **Documentation** of operational decisions
- **Audit trail** for regulators

### **5. Data-Driven Decisions**
- **Optimize pumping schedules** around price forecasts
- **Better energy procurement** - Know when to buy/sell
- **Strategic planning** - Historical trend analysis

---

## 📊 Key Features

### **Current Implementation (Phase 1)**

#### 1. **Real-Time Grid Status**
- System-wide electricity demand (MW)
- Average energy prices ($/MWh)
- Grid stress level indicator
- Last update timestamp

#### 2. **Energy Price Intelligence**
- 6-hour price trend visualization
- Automatic spike detection (>2σ from mean)
- Price component breakdown (Energy, Congestion, Losses)
- Volatility metrics

#### 3. **Demand Forecasting**
- 24-hour demand profile
- Peak demand identification
- Capacity margin calculations
- Off-peak optimization opportunities

#### 4. **Operational Intelligence**
- Automated insights based on current conditions
- Specific action recommendations
- Alert generation for critical events
- Integration-ready for SCADA/notification systems

#### 5. **Interactive Visualizations**
- Time-series price charts
- Demand forecast curves
- Price component breakdowns
- Historical trend analysis

---

## 🎓 How to Use This Dashboard

### **For Grid Operators:**

1. **Morning Check-in**
   - Review 24-hour demand forecast
   - Check price trends for the day
   - Plan load shifting opportunities

2. **Real-Time Monitoring**
   - Watch the Grid Stress Level indicator
   - Respond to price spike alerts
   - Adjust operations based on recommendations

3. **High-Price Event**
   - Dashboard alerts: "High Prices - Potential Stress"
   - Recommended action shown automatically
   - Activate demand response programs
   - Document incident in system logs

4. **Economic Optimization**
   - Low price periods? Increase pumping
   - High price periods? Reduce non-critical loads
   - Track savings vs baseline operations

### **For Management:**

1. **Strategic Overview**
   - Review grid stress patterns
   - Analyze price volatility trends
   - Identify optimization opportunities

2. **Cost Management**
   - Track price exposure
   - Calculate avoided costs
   - Justify demand response investments

3. **Performance Metrics**
   - Operator response times
   - Cost avoidance achieved
   - System reliability improvements

---

## 🔧 Technical Details

### **Data Sources**
- **CAISO OASIS API** - California ISO's public data service
- **Update Frequency** - 5-minute intervals (real-time market)
- **Historical Depth** - Up to 24 hours of data
- **No Authentication Required** - Public API

### **Key Metrics Tracked**

| Metric | Source | Update Frequency | Use Case |
|--------|--------|------------------|----------|
| System Demand | `SLD_FCST` | 5 minutes | Capacity planning |
| Real-Time Prices (LMP) | `PRC_INTVL_LMP` | 5 minutes | Cost optimization |
| Price Components | `PRC_INTVL_LMP` | 5 minutes | Congestion analysis |
| Demand Forecast | `SYS_FCST_DA` | Hourly | Day-ahead planning |

### **Intelligence Algorithms**

1. **Price Spike Detection**
   ```
   Spike = |Price - Mean| > 2 × StdDev
   ```

2. **Grid Stress Score**
   ```
   Score = f(Demand, Price)
   - Very High Demand (>45,000 MW): +3
   - High Demand (>40,000 MW): +2
   - Very High Price (>$150/MWh): +3
   - High Price (>$100/MWh): +2
   - Elevated Price (>$75/MWh): +1
   
   Levels: Normal (0), Moderate (1-2), High (3-4), Critical (5+)
   ```

3. **Price Volatility**
   ```
   Volatility = Rolling StdDev (12-interval window)
   ```

---

## 📦 Installation & Setup

### **Prerequisites**
- Python 3.8+
- Internet connection (for CAISO API)

### **Quick Start**

1. **Install Dependencies**
   ```powershell
   cd "c:\Users\leric\Downloads\LADWP"
   pip install -r requirements.txt
   ```

2. **Run the Dashboard**
   ```powershell
   streamlit run dashboard.py
   ```

3. **Access the Dashboard**
   - Opens automatically in your browser
   - Default URL: `http://localhost:8501`

### **Files Structure**
```
LADWP/
├── dashboard.py           # Main Streamlit dashboard
├── caiso_api_client.py   # CAISO API integration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

---

## 🎯 Use Case Examples

### **Example 1: Avoiding High-Price Period**
**Scenario**: Dashboard detects price spike from $50 to $180/MWh at 5:00 PM

**Dashboard Actions**:
1. ⚠️ Alert: "High Prices - Potential Stress"
2. 📊 Shows: Price jumped 260% in 15 minutes
3. 💡 Recommends: "Consider demand response activation"

**Operator Response**:
1. Reviews non-critical loads
2. Activates customer demand response program
3. Reduces load by 200 MW for 2 hours

**Financial Impact**:
- Avoided cost: 200 MW × 2 hours × ($180 - $50) = **$52,000 saved**

### **Example 2: Optimizing Pumping Schedule**
**Scenario**: Dashboard shows low overnight prices ($25/MWh) vs high afternoon prices ($85/MWh)

**Dashboard Actions**:
1. 📈 Shows: 24-hour price forecast
2. 🎯 Highlights: Optimal pumping window 11 PM - 5 AM
3. 💡 Recommends: "Shift pumping to low-price period"

**Operator Response**:
1. Reschedules water pumping operations
2. Runs pumps at full capacity during cheap hours
3. Reduces daytime pumping

**Financial Impact**:
- Daily savings: 500 MW × 6 hours × ($85 - $25) = **$180,000/day**
- Annual savings: **$65.7M/year**

### **Example 3: Grid Emergency Preparation**
**Scenario**: Dashboard shows rising demand + high prices + transmission congestion

**Dashboard Actions**:
1. 🔴 Alert: "Critical Grid Stress"
2. 📊 Stress Score: 6/10 (Critical)
3. 💡 Recommends: "Implement emergency procedures, contact CAISO"

**Operator Response**:
1. Notifies operations management
2. Prepares load shedding plans
3. Coordinates with CAISO control room
4. Activates emergency demand response

**Reliability Impact**:
- Prevented potential blackout
- Maintained service to critical customers
- Documented compliance with CAISO directives

---

## 🔮 Future Enhancements (Phase 2 & 3)

### **Phase 2: Machine Learning Anomaly Detection**
- Train ML models on historical CAISO data
- Predict price spikes 30-60 minutes in advance
- Detect unusual patterns (grid events, equipment issues)
- Automated incident classification

### **Phase 3: Water Infrastructure Integration**
- Combine grid data with water system sensors
- Optimize pumping based on electricity prices
- Detect water main leaks using pressure anomalies
- Unified energy + water operations dashboard

### **Advanced Features**
- Mobile app for field operators
- SMS/email alerts for critical events
- Integration with SCADA systems
- Automated demand response dispatch
- Historical analytics & reporting
- API for third-party integrations

---

## 🤝 Integration Opportunities

### **Ready to Integrate With:**
- **SCADA Systems** - Automated alert injection
- **Energy Management Systems (EMS)** - Real-time optimization
- **Customer Information Systems (CIS)** - Demand response programs
- **GIS Systems** - Geographic visualization
- **Ticketing Systems** - Automatic incident creation
- **Notification Services** - Email, SMS, Slack, PagerDuty

---

## 📈 Success Metrics

### **Operational Metrics**
- Time to detect grid events (target: <5 minutes)
- Operator response time (target: <15 minutes)
- False alarm rate (target: <5%)

### **Financial Metrics**
- Cost avoidance per month
- Price exposure reduction
- ROI on demand response programs

### **Reliability Metrics**
- Grid stress events anticipated
- Emergency activations prevented
- Customer service improvements

---

## 🙋 FAQ

**Q: Does this replace SCADA?**  
A: No, it complements SCADA. SCADA monitors your equipment; this monitors the broader CAISO grid to give you strategic insight.

**Q: How accurate is the data?**  
A: Data comes directly from CAISO's official OASIS API - the same data used by grid operators and market participants.

**Q: What if the API is down?**  
A: The dashboard shows a warning and uses cached data. In production, we'd add redundancy and fallback data sources.

**Q: Can this run 24/7?**  
A: Yes! Deploy on a server with auto-refresh enabled. We recommend cloud hosting (AWS, Azure) for reliability.

**Q: What about security?**  
A: Current version uses public data only (no authentication needed). For production deployment with internal data, add authentication, encryption, and VPN access.

---

## 📞 Support

**Built for LADWP Operations Team**  
For questions, enhancements, or integration support, contact your IT department or the development team.

---

## 📄 License

Internal use only - LADWP proprietary.

---

**🎉 Start using the dashboard now and experience the power of real-time grid intelligence!**
