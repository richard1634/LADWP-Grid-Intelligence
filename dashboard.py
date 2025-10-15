"""
LADWP Real-Time Grid Intelligence Dashboard
Phase 1: Live CAISO Data Monitoring

This dashboard provides real-time visibility into grid conditions affecting LADWP operations.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import json
from pathlib import Path
from caiso_api_client import (
    CAISOClient, 
    calculate_price_volatility,
    detect_price_spikes,
    calculate_grid_stress_score
)

# Page configuration
st.set_page_config(
    page_title="LADWP Grid Intelligence Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    /* LADWP Brand Colors - Blue and White Theme */
    :root {
        --ladwp-blue: #003DA5;
        --ladwp-light-blue: #0066CC;
        --ladwp-dark-blue: #002B73;
        --ladwp-accent: #00A3E0;
    }
    
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
    }
    
    /* Header styling */
    h1 {
        color: var(--ladwp-blue) !important;
        font-weight: 700 !important;
        border-bottom: 4px solid var(--ladwp-accent);
        padding-bottom: 0.5rem;
    }
    
    h2 {
        color: var(--ladwp-dark-blue) !important;
        font-weight: 600 !important;
    }
    
    h3 {
        color: var(--ladwp-light-blue) !important;
    }
    
    /* Metric card styling */
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: var(--ladwp-blue) !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: var(--ladwp-dark-blue) !important;
        font-weight: 600;
    }
    
    /* Card containers */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMetricValue"]) {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 61, 165, 0.1);
        border-left: 4px solid var(--ladwp-accent);
    }
    
    /* Better spacing between sections */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Chart containers */
    .stPlotlyChart {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0, 61, 165, 0.08);
        border: 1px solid rgba(0, 61, 165, 0.1);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--ladwp-blue) 0%, var(--ladwp-dark-blue) 100%);
    }
    
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid var(--ladwp-accent);
    }
    
    /* Buttons */
    .stButton button {
        background-color: var(--ladwp-blue);
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background-color: var(--ladwp-light-blue);
        box-shadow: 0 4px 12px rgba(0, 61, 165, 0.3);
    }
    
    /* Dividers */
    hr {
        border-color: var(--ladwp-accent);
        opacity: 0.3;
    }
    
    </style>
""", unsafe_allow_html=True)

# Initialize CAISO client
@st.cache_resource
def get_caiso_client():
    return CAISOClient()

client = get_caiso_client()

# Header with LADWP branding
st.markdown("""
    <div style='text-align: left; padding: 1rem 0;'>
        <h1 style='margin-bottom: 0.5rem;'>
            ⚡ Los Angeles Department of Water & Power
        </h1>
        <h2 style='color: #0066CC; font-weight: 600; margin-top: 0;'>
            Real-Time Grid Intelligence Dashboard
        </h2>
        <p style='color: #666; font-size: 1.1rem; margin-top: 0.5rem;'>
            Live CAISO grid monitoring with predictive analytics for operational excellence
        </p>
    </div>
""", unsafe_allow_html=True)

# Add timestamp and connection status
col_status1, col_status2, col_status3 = st.columns([2, 1, 1])
with col_status1:
    st.caption(f"🕐 Last Updated: {datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%I:%M:%S %p PT')}")
with col_status2:
    st.caption("📡 Data Source: CAISO OASIS API")
with col_status3:
    st.caption("🔄 Rate Limited (6s intervals)")

st.markdown("---")

# Sidebar controls
st.sidebar.header("Dashboard Controls")

# Date selector for historical analysis
st.sidebar.markdown("### 📅 Date Selection")
today = datetime.now(pytz.timezone('America/Los_Angeles')).date()
selected_date = st.sidebar.date_input(
    "View forecast for date",
    value=today,
    min_value=today - timedelta(days=7),
    max_value=today,
    help="Select any day from the past week to view historical forecasts"
)

# Show if viewing historical data
if selected_date < today:
    days_ago = (today - selected_date).days
    st.sidebar.info(f"📊 Viewing data from {days_ago} day(s) ago")

st.sidebar.markdown("---")

refresh_interval = st.sidebar.selectbox(
    "Auto-refresh interval",
    ["Manual", "30 seconds", "1 minute", "5 minutes"],
    index=2
)

# Default lookback window for current day price data
hours_back = 6  # Show last 6 hours when viewing today

st.sidebar.markdown("---")

# Fetch data first to get available options
with st.spinner("Loading available data options..."):
    try:
        temp_demand_df = client.get_system_demand()
        temp_price_df = client.get_real_time_prices(hours_back=2)
        
        # Get available TAC areas
        if temp_demand_df is not None and 'TAC_AREA_NAME' in temp_demand_df.columns:
            available_tac_areas = sorted(temp_demand_df['TAC_AREA_NAME'].unique().tolist())
        else:
            available_tac_areas = ['All Areas']
        
        # Get available price nodes
        if temp_price_df is not None and 'NODE' in temp_price_df.columns:
            available_nodes = sorted(temp_price_df['NODE'].unique().tolist())
        else:
            available_nodes = ['Default']
            
    except Exception as e:
        available_tac_areas = ['All Areas']
        available_nodes = ['Default']

# Set LADWP as the only focus
LADWP_TAC_AREA = 'LADWP'
LADWP_PRICE_NODE = 'TH_SP15_GEN-APND'  # Southern California pricing hub

# Try to use LADWP area if available, otherwise use first available
if LADWP_TAC_AREA in available_tac_areas:
    selected_tac_area = LADWP_TAC_AREA
elif 'SCE-TAC' in available_tac_areas:
    selected_tac_area = 'SCE-TAC'  # Fallback to SCE
else:
    selected_tac_area = available_tac_areas[0] if available_tac_areas else 'LADWP'

# Use SP15 node for LA pricing
if LADWP_PRICE_NODE in available_nodes:
    selected_price_node = LADWP_PRICE_NODE
else:
    # Try to find any SP15 node
    sp15_nodes = [n for n in available_nodes if 'SP15' in n]
    selected_price_node = sp15_nodes[0] if sp15_nodes else available_nodes[0]

# Area info display
st.sidebar.markdown("### 📍 LADWP Territory")
st.sidebar.info(f"""
**Demand Area**: {selected_tac_area}  
Los Angeles Department of Water and Power service territory

**Pricing Zone**: {selected_price_node}  
Southern California (SP15) pricing hub
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### About This Dashboard")
st.sidebar.info("""
**Data Source**: CAISO OASIS API (Real-time)

**Updates**: Live 5-minute interval data

**Coverage**: LADWP service territory within CAISO grid

**Rate Limiting**: 6-second minimum between requests (API-friendly)

**Caching**: 10-minute cache to minimize API load

💡 **Tip**: Set refresh to "5 minutes" or "Manual" for best performance
""")

# Auto-refresh logic
if refresh_interval != "Manual":
    interval_map = {"30 seconds": 30, "1 minute": 60, "5 minutes": 300}
    st.empty()  # Placeholder for auto-refresh

# Convert selected date to datetime for API
selected_datetime = datetime.combine(selected_date, datetime.min.time())
selected_datetime = pytz.timezone('America/Los_Angeles').localize(selected_datetime)

# Fetch data with error handling
spinner_text = f"Fetching grid data for {selected_date.strftime('%B %d, %Y')}..." if selected_date < today else "Fetching live grid data from CAISO..."
with st.spinner(spinner_text):
    try:
        # Get current grid status (always use current)
        grid_status = client.get_current_grid_status()
        
        # Get real-time prices for selected date
        if selected_date < today:
            # Historical data - get full day
            price_df = client.get_real_time_prices(date=selected_datetime)
        else:
            # Current data - use hours_back
            price_df = client.get_real_time_prices(hours_back=hours_back)
        
        # Get demand forecast for selected date
        if selected_date < today:
            # Historical data
            demand_df = client.get_system_demand(date=selected_datetime)
        else:
            # Current data - don't pass date to get live forecast
            demand_df = client.get_system_demand()
        
        data_fetch_success = True
    except Exception as e:
        data_fetch_success = False
        st.error(f"⚠️ Error fetching data: {e}")
        st.info("💡 Using cached data or demo mode. The dashboard will retry automatically.")
        
        # Initialize with empty/default data
        grid_status = {
            'timestamp': datetime.now(pytz.timezone('America/Los_Angeles')),
            'demand_mw': None,
            'avg_price_per_mwh': None,
            'price_range': None,
            'renewable_pct': None,
            'constraints_active': 0,
            'status': 'Data Unavailable'
        }
        price_df = None
        demand_df = None

# ==========================================
# SECTION 1: Current Grid Status Overview
# ==========================================
st.header("📊 Current Grid Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if grid_status['demand_mw']:
        st.metric(
            "System Demand",
            f"{grid_status['demand_mw']:,.0f} MW",
            delta=None,
            help="Current CAISO system-wide electricity demand"
        )
    else:
        st.metric("System Demand", "Loading...", delta=None)

with col2:
    if grid_status['avg_price_per_mwh']:
        price_delta = grid_status['avg_price_per_mwh'] - 50  # Compare to typical $50/MWh
        st.metric(
            "Avg. Energy Price",
            f"${grid_status['avg_price_per_mwh']:.2f}/MWh",
            delta=f"${price_delta:.2f} vs typical",
            delta_color="inverse",
            help="Average real-time market price"
        )
    else:
        st.metric("Avg. Energy Price", "Loading...", delta=None)

with col3:
    stress = calculate_grid_stress_score(
        grid_status['demand_mw'],
        grid_status['avg_price_per_mwh']
    )
    
    stress_color = {
        "Normal": "🟢",
        "Moderate": "🟡", 
        "High": "🟠",
        "Critical": "🔴"
    }
    
    st.metric(
        "Grid Stress Level",
        f"{stress_color.get(stress['level'], '⚪')} {stress['level']}",
        delta=None,
        help=f"Stress factors: {', '.join(stress['factors']) if stress['factors'] else 'None'}"
    )

with col4:
    st.metric(
        "Last Updated",
        grid_status['timestamp'].strftime('%I:%M %p'),
        delta=None,
        help="Pacific Time"
    )

# Alert banner
if stress['level'] in ['High', 'Critical']:
    st.markdown(f"""
        <div class="alert-{'critical' if stress['level'] == 'Critical' else 'warning'}">
            <strong>⚠️ GRID ALERT: {stress['level']} Stress Detected</strong><br>
            Factors: {', '.join(stress['factors'])}<br>
            Recommended Action: Monitor operations closely, consider demand response measures
        </div>
    """, unsafe_allow_html=True)
elif stress['level'] == 'Normal':
    st.markdown("""
        <div class="alert-normal">
            <strong>✅ Grid Operating Normally</strong>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# SECTION 2: System Demand Analysis
# ==========================================
# Show date in header if viewing historical data
if selected_date < today:
    st.header(f"📊 System Demand Forecast - {selected_date.strftime('%A, %B %d, %Y')}")
    st.info(f"📊 Viewing historical forecast from {(today - selected_date).days} day(s) ago")
else:
    st.header("📊 System Demand Forecast - Next 48 Hours")
    st.info("🔮 Showing CAISO's predictive forecast extending into tomorrow")

if demand_df is not None and not demand_df.empty:
    
    # Check if we have required columns
    has_timestamp = 'timestamp' in demand_df.columns
    has_demand = 'MW' in demand_df.columns
    
    if not has_timestamp:
        # Try to create timestamp from available columns
        if 'INTERVAL_START_GMT' in demand_df.columns:
            try:
                demand_df['timestamp'] = pd.to_datetime(demand_df['INTERVAL_START_GMT'])
                demand_df['timestamp'] = demand_df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('America/Los_Angeles'))
                has_timestamp = True
            except:
                pass
        elif 'INTERVALSTARTTIME_GMT' in demand_df.columns:
            try:
                demand_df['timestamp'] = pd.to_datetime(demand_df['INTERVALSTARTTIME_GMT'])
                demand_df['timestamp'] = demand_df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(pytz.timezone('America/Los_Angeles'))
                has_timestamp = True
            except:
                pass
    
    if not has_timestamp or not has_demand:
        st.warning(f"⚠️ Data structure issue. Available columns: {', '.join(demand_df.columns.tolist()[:10])}")
        st.info(f"💡 Data has {len(demand_df)} records but missing required columns for visualization.")
    else:
        # Now showing demand data (no spike detection needed)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Update subtitle based on viewing mode
            if selected_date < today:
                st.subheader("Historical 24-Hour Profile")
            else:
                st.subheader("Forecast: Next 48 Hours")
            
            # Create demand chart
            fig = go.Figure()
            
            # Filter to selected LADWP area
            if 'TAC_AREA_NAME' in demand_df.columns:
                # Check if selected area exists in data
                available_areas = demand_df['TAC_AREA_NAME'].unique()
                
                if selected_tac_area in available_areas:
                    demand_plot_df = demand_df[demand_df['TAC_AREA_NAME'] == selected_tac_area].copy()
                else:
                    # Fallback to first available area
                    selected_tac_area = available_areas[0]
                    demand_plot_df = demand_df[demand_df['TAC_AREA_NAME'] == selected_tac_area].copy()
            else:
                # If no TAC_AREA_NAME, use all data
                demand_plot_df = demand_df.copy()
            
            # Ensure timestamps are timezone-aware for proper display
            if 'timestamp' in demand_plot_df.columns:
                # Make sure timestamps have timezone info
                if demand_plot_df['timestamp'].dt.tz is None:
                    demand_plot_df['timestamp'] = demand_plot_df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/Los_Angeles')
                elif str(demand_plot_df['timestamp'].dt.tz) == 'UTC':
                    demand_plot_df['timestamp'] = demand_plot_df['timestamp'].dt.tz_convert('America/Los_Angeles')
            
            # Sort data by timestamp and show full forecast range
            area_data = demand_plot_df.sort_values('timestamp')
            
            # Add helpful caption about data range
            if not area_data.empty:
                data_start = area_data['timestamp'].min()
                data_end = area_data['timestamp'].max()
                hours_span = (data_end - data_start).total_seconds() / 3600
                
                # Check for future data
                current_time = datetime.now(pytz.timezone('America/Los_Angeles'))
                future_data = area_data[area_data['timestamp'] > current_time]
                past_data = area_data[area_data['timestamp'] <= current_time]
                
                if not future_data.empty:
                    future_hours = (future_data['timestamp'].max() - current_time).total_seconds() / 3600
                    st.caption(f"📍 {selected_tac_area} | Past: {len(past_data)} records | 🔮 Forecast: {len(future_data)} records ({future_hours:.1f}h ahead)")
                else:
                    st.caption(f"📍 {selected_tac_area} territory | {data_start.strftime('%I:%M %p')} - {data_end.strftime('%I:%M %p')} ({hours_span:.0f}h)")
            
            # Split into historical and forecast for different styling
            current_time = datetime.now(pytz.timezone('America/Los_Angeles'))
            historical_data = area_data[area_data['timestamp'] <= current_time].copy()
            forecast_data = area_data[area_data['timestamp'] > current_time].copy()
            
            # Plot historical data (solid line) - LADWP Blue
            if not historical_data.empty:
                fig.add_trace(go.Scatter(
                    x=historical_data['timestamp'],
                    y=historical_data['MW'],
                    mode='lines',
                    name='Historical Demand',
                    fill='tozeroy',
                    line=dict(color='#003DA5', width=3),
                    fillcolor='rgba(0, 61, 165, 0.15)',
                    hovertemplate='<b>Historical</b><br>Time: %{x|%I:%M %p}<br>Demand: %{y:,.0f} MW<extra></extra>'
                ))
            
            # Plot forecast data (dashed line) - LADWP Light Blue
            if not forecast_data.empty:
                # Connect last historical point to forecast
                if not historical_data.empty:
                    last_hist = historical_data.iloc[[-1]]
                    forecast_data = pd.concat([last_hist, forecast_data])
                
                fig.add_trace(go.Scatter(
                    x=forecast_data['timestamp'],
                    y=forecast_data['MW'],
                    mode='lines',
                    name='🔮 CAISO Forecast',
                    line=dict(color='#00A3E0', width=3, dash='dash'),
                    fillcolor='rgba(0, 163, 224, 0.12)',
                    fill='tozeroy',
                    hovertemplate='<b>🔮 Forecast</b><br>Time: %{x|%I:%M %p}<br>Demand: %{y:,.0f} MW<extra></extra>'
                ))
            
            # Add peak demand marker - LADWP Dark Blue
            if not area_data.empty:
                peak_idx = area_data['MW'].idxmax()
                peak_time = area_data.loc[peak_idx, 'timestamp']
                peak_demand = area_data.loc[peak_idx, 'MW']
                
                fig.add_trace(go.Scatter(
                    x=[peak_time],
                    y=[peak_demand],
                    mode='markers+text',
                    name='Peak',
                    marker=dict(color='#002B73', size=16, symbol='diamond', line=dict(width=2, color='white')),
                    text=[f'Peak: {peak_demand:,.0f} MW'],
                    textposition='top center',
                    textfont=dict(color='#002B73', size=12, family='Arial Black'),
                    showlegend=False
                ))
            
            fig.update_layout(
                xaxis_title="Time (Pacific)",
                yaxis_title="Demand (MW)",
                hovermode='x unified',
                height=450,
                showlegend=True,
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.02, 
                    xanchor="right", 
                    x=1,
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='rgba(128,128,128,0.3)',
                    borderwidth=1
                ),
                margin=dict(l=20, r=20, t=20, b=40),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            )
            
            st.plotly_chart(fig, use_container_width=True, key='demand_chart')
        
        with col2:
            st.subheader("Demand Statistics")
            
            if 'MW' in demand_df.columns and 'timestamp' in demand_df.columns:
                # Get current and forecasted values
                now = pd.Timestamp.now(tz='America/Los_Angeles')
                future_data = demand_df[demand_df['timestamp'] >= now]
                
                if not future_data.empty:
                    next_demand = future_data.iloc[0]['MW']
                    st.metric("Next Hour Forecast", f"{next_demand:,.0f} MW")
                
                peak_demand = demand_df['MW'].max()
                off_peak = demand_df['MW'].min()
                avg_demand = demand_df['MW'].mean()
                
                st.metric("Peak Forecast", f"{peak_demand:,.0f} MW")
                st.metric("Average", f"{avg_demand:,.0f} MW")
                st.metric("Off-Peak", f"{off_peak:,.0f} MW")
                
                # Calculate variation
                variation = ((peak_demand - off_peak) / avg_demand) * 100
                st.metric("Peak Variation", f"{variation:.1f}%")

else:
    st.warning("⚠️ Unable to fetch demand forecast data from CAISO API.")
    st.info("💡 The dashboard will automatically retry on next refresh. Using cached data if available.")

st.markdown("---")

# ==========================================
# SECTION 2.5: ML-Powered Anomaly Detection (Integrated with Demand Forecast)
# ==========================================
st.subheader("🤖 AI-Powered Forecast Analysis")
st.info("Machine learning models analyze the 48-hour demand forecast to detect anomalies and provide recommendations")

# Determine which model to use based on current month
current_month = datetime.now().month
month_names = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
]
current_month_name = month_names[current_month - 1]

# Try to load month-specific predictions first
predictions_file = f"{current_month_name}_predictions.json"
model_type = f"{current_month_name.capitalize()}-Specific Model"

predictions_path = Path(__file__).parent / "models" / "predictions" / predictions_file

# Fallback to general model if month-specific doesn't exist
if not predictions_path.exists():
    predictions_file = "latest_predictions.json"
    model_type = "General Model"
    predictions_path = Path(__file__).parent / "models" / "predictions" / predictions_file

if predictions_path.exists():
    try:
        with open(predictions_path, 'r') as f:
            ml_predictions = json.load(f)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Forecast Points", ml_predictions.get('total_points', 0))
        
        with col2:
            anomaly_count = ml_predictions.get('anomalies_detected', 0)
            st.metric("Anomalies Detected", anomaly_count)
        
        with col3:
            anomaly_rate = ml_predictions.get('anomaly_rate', 0)
            st.metric("Anomaly Rate", f"{anomaly_rate:.1f}%")
        
        with col4:
            st.metric("Model Active", model_type)
        
        # Convert predictions to DataFrame
        pred_df = pd.DataFrame(ml_predictions.get('predictions', []))
        
        if not pred_df.empty:
            pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])
            
            # Create visualization
            fig_ml = go.Figure()
            
            # Normal points
            normal_df = pred_df[~pred_df['is_anomaly']]
            if not normal_df.empty:
                fig_ml.add_trace(go.Scatter(
                    x=normal_df['timestamp'],
                    y=normal_df['demand_mw'],
                    mode='lines+markers',
                    name='Normal Forecast',
                    line=dict(color='#00A3E0', width=2),
                    marker=dict(size=6, color='#00A3E0'),
                    hovertemplate='<b>Normal</b><br>Time: %{x|%I:%M %p}<br>Demand: %{y:.0f} MW<extra></extra>'
                ))
            
            # Anomalous points by severity
            severity_colors = {
                'critical': '#E63946',
                'high': '#FF9500',
                'medium': '#FFD60A'
            }
            
            for severity, color in severity_colors.items():
                severity_df = pred_df[(pred_df['is_anomaly']) & (pred_df['severity'] == severity)]
                if not severity_df.empty:
                    fig_ml.add_trace(go.Scatter(
                        x=severity_df['timestamp'],
                        y=severity_df['demand_mw'],
                        mode='markers',
                        name=f'{severity.capitalize()} Anomaly',
                        marker=dict(
                            size=15,
                            color=color,
                            symbol='diamond',
                            line=dict(color='white', width=2)
                        ),
                        hovertemplate=f'<b>⚠️ {severity.upper()}</b><br>Time: %{{x|%I:%M %p}}<br>Demand: %{{y:.0f}} MW<br>Confidence: %{{customdata:.1f}}%<extra></extra>',
                        customdata=severity_df['confidence']
                    ))
            
            fig_ml.update_layout(
                xaxis_title="Time (Pacific)",
                yaxis_title="Demand (MW)",
                hovermode='x unified',
                height=400,
                showlegend=True,
                margin=dict(l=20, r=20, t=20, b=40),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            )
            
            st.plotly_chart(fig_ml, use_container_width=True, key='ml_anomaly_chart')
            
            # Show anomaly details if any detected
            anomalies_df = pred_df[pred_df['is_anomaly']].sort_values('confidence', ascending=False)
            
            if not anomalies_df.empty:
                st.markdown(f"**🚨 Detected Anomalies ({len(anomalies_df)})**")
                
                for idx, row in anomalies_df.head(5).iterrows():
                    severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡'}.get(row['severity'], '⚪')
                    time_str = row['timestamp'].strftime('%a %I:%M %p')
                    
                    with st.expander(f"{severity_emoji} {time_str} - {row['demand_mw']:.0f} MW ({row['severity'].upper()})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Confidence:** {row['confidence']:.1f}%")
                            st.write(f"**Severity:** {row['severity'].capitalize()}")
                        with col2:
                            st.write(f"**Demand:** {row['demand_mw']:.0f} MW")
                            st.write(f"**Timestamp:** {row['timestamp']}")
            else:
                st.success("✅ No anomalies detected - all forecasts appear normal")
        
        # Model info footer
        st.caption(f"🤖 Model: {model_type} | Last updated: {ml_predictions.get('generated_at', 'Unknown')}")
    
    except Exception as e:
        st.error(f"Error loading ML predictions: {e}")
else:
    st.info(f"⚠️ ML predictions not available for {current_month_name.capitalize()}.")

# ==========================================
# SECTION 2.6: Smart Recommendations (Integrated)
# ==========================================
st.markdown("### 💡 Smart Recommendations")

# Load anomaly-based recommendations for the current month
recommendations_file = f'data/{current_month_name}_anomaly_recommendations.json'
if Path(recommendations_file).exists():
    try:
        with open(recommendations_file, 'r') as f:
            rec_data = json.load(f)
        
        recommendations = rec_data.get('recommendations', [])
        
        if recommendations:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Recommendations", rec_data.get('total_anomalies', len(recommendations)))
            
            with col2:
                high_priority = rec_data.get('high_priority', 0)
                st.metric("High Priority", high_priority)
            
            with col3:
                medium_priority = rec_data.get('medium_priority', 0)
                st.metric("Medium Priority", medium_priority)
            
            # Display top 3 recommendations
            for i, item in enumerate(recommendations[:3], 1):
                anomaly = item['anomaly']
                rec = item['recommendation']
                
                priority_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(rec['priority'], '⚪')
                
                with st.expander(f"{priority_emoji} {anomaly['time_str']} | {rec['title']}", expanded=(i == 1)):
                    st.markdown(f"**Priority:** {rec['priority']} | **Urgency:** {rec['urgency']}")
                    st.markdown("**Analysis:**")
                    st.write(rec['why'])
                    st.markdown("**Actions:**")
                    for j, action in enumerate(rec['actions'][:3], 1):
                        st.write(f"{action['icon']} **{j}.** {action['action']}")
                        st.caption(f"   {action['details']}")
        else:
            st.info("No recommendations available - system operating normally")
    
    except Exception as e:
        st.error(f"Error loading recommendations: {e}")
else:
    st.info(f"No recommendations available for {current_month_name.capitalize()}")

st.markdown("---")

# ==========================================
# SECTION 3: Real-Time Price Analysis
# ==========================================
# Show date in header if viewing historical data
if selected_date < today:
    st.header(f"💰 Real-Time Energy Prices - {selected_date.strftime('%A, %B %d, %Y')}")
    st.info(f"📊 Viewing historical prices from {(today - selected_date).days} day(s) ago")
else:
    st.header("💰 Real-Time Energy Prices")
    st.info("🔮 Showing CAISO's real-time and forecasted pricing")

if price_df is not None and not price_df.empty:
    
    # Check if we have required columns
    has_timestamp = 'timestamp' in price_df.columns
    has_price = 'LMP_PRC' in price_df.columns
    
    if not has_timestamp or not has_price:
        st.warning(f"⚠️ Data structure issue. Available columns: {', '.join(price_df.columns.tolist()[:10])}")
        st.info(f"💡 Data has {len(price_df)} records but missing required columns for visualization.")
    else:
        # Detect price spikes
        spikes_df = detect_price_spikes(price_df, threshold_std=2.5)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if selected_date < today:
                st.subheader("Price Trends (Full Day)")
            else:
                st.subheader(f"Price Trends (Last {hours_back} Hours)")
            
            # Create price chart
            fig_price = go.Figure()
            
            if 'NODE' in price_df.columns and has_price:
                # Get unique nodes for the selected price zone
                unique_nodes = price_df['NODE'].unique()
                
                # If we have a selected node, use it; otherwise use the first available node
                if selected_price_node in unique_nodes:
                    node_to_display = selected_price_node
                else:
                    node_to_display = unique_nodes[0] if len(unique_nodes) > 0 else None
                
                if node_to_display:
                    # Filter for selected node
                    node_data = price_df[price_df['NODE'] == node_to_display].copy()
                    
                    if not node_data.empty:
                        # Sort by timestamp
                        node_data = node_data.sort_values('timestamp')
                        
                        # Add price line
                        fig_price.add_trace(go.Scatter(
                            x=node_data['timestamp'],
                            y=node_data['LMP_PRC'],
                            mode='lines+markers',
                            name='LMP Price',
                            line=dict(color='#003f5c', width=2),
                            marker=dict(size=4),
                            hovertemplate='<b>Time:</b> %{x|%Y-%m-%d %H:%M}<br>' +
                                         '<b>Price:</b> $%{y:.2f}/MWh<br>' +
                                         '<extra></extra>'
                        ))
                        
                        # Add price spikes if any
                        if not spikes_df.empty:
                            spike_data = spikes_df[spikes_df['NODE'] == node_to_display]
                            if not spike_data.empty:
                                fig_price.add_trace(go.Scatter(
                                    x=spike_data['timestamp'],
                                    y=spike_data['LMP_PRC'],
                                    mode='markers',
                                    name='Price Spike',
                                    marker=dict(
                                        color='red',
                                        size=10,
                                        symbol='diamond',
                                        line=dict(color='darkred', width=1)
                                    ),
                                    hovertemplate='<b>⚠️ Price Spike</b><br>' +
                                                 'Time: %{x|%Y-%m-%d %H:%M}<br>' +
                                                 'Price: $%{y:.2f}/MWh<br>' +
                                                 '<extra></extra>'
                                ))
                        
                        # Add typical price range bands
                        mean_price = node_data['LMP_PRC'].mean()
                        std_price = node_data['LMP_PRC'].std()
                        
                        # Add shaded region for typical range (mean ± 1 std)
                        fig_price.add_hrect(
                            y0=mean_price - std_price,
                            y1=mean_price + std_price,
                            fillcolor="rgba(0, 128, 0, 0.1)",
                            line_width=0,
                            annotation_text="Typical Range",
                            annotation_position="top left"
                        )
            
            fig_price.update_layout(
                xaxis_title="Time",
                yaxis_title="Price ($/MWh)",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_price, use_container_width=True, key='price_chart')
    
        with col2:
            st.subheader("Price Statistics")
            
            if has_price and has_timestamp:
                # Current price
                current_time = datetime.now(pytz.timezone('America/Los_Angeles'))
                recent_data = price_df[price_df['timestamp'] <= current_time]
                
                if not recent_data.empty:
                    current_price = recent_data.iloc[-1]['LMP_PRC']
                    st.metric("Current Price", f"${current_price:.2f}/MWh")
                
                # 6-hour average
                six_hours_ago = current_time - pd.Timedelta(hours=6)
                recent_6h = price_df[price_df['timestamp'] >= six_hours_ago]
                if not recent_6h.empty:
                    avg_6h = recent_6h['LMP_PRC'].mean()
                    st.metric("6-Hour Average", f"${avg_6h:.2f}/MWh")
                
                # Price range
                min_price = price_df['LMP_PRC'].min()
                max_price = price_df['LMP_PRC'].max()
                st.metric("Min Price", f"${min_price:.2f}/MWh")
                st.metric("Max Price", f"${max_price:.2f}/MWh")
                
                # Price volatility
                price_std = price_df['LMP_PRC'].std()
                st.metric("Price Volatility", f"${price_std:.2f}/MWh")
                
                # Spike warning
                if not spikes_df.empty:
                    st.warning(f"⚠️ {len(spikes_df)} price spikes detected")
                else:
                    st.success("✓ No unusual price spikes")

else:
    st.warning("⚠️ Unable to fetch demand forecast data. Dashboard will retry on next refresh.")

st.markdown("---")

# ==========================================
# SECTION 4: Operational Intelligence
# ==========================================
st.header("🎯 Operational Intelligence & Recommendations")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Key Insights")
    
    insights = []
    
    # Price-based insights
    if grid_status['avg_price_per_mwh']:
        if grid_status['avg_price_per_mwh'] > 100:
            insights.append({
                'type': 'warning',
                'title': 'High Energy Prices',
                'message': f"Current prices (${grid_status['avg_price_per_mwh']:.2f}/MWh) are significantly above normal. Consider demand response activation.",
                'action': 'Activate demand response programs, defer non-critical loads'
            })
        elif grid_status['avg_price_per_mwh'] < 20:
            insights.append({
                'type': 'info',
                'title': 'Low Energy Prices',
                'message': f"Current prices (${grid_status['avg_price_per_mwh']:.2f}/MWh) are very low. Good opportunity for flexible loads.",
                'action': 'Consider increasing pumping operations, charging storage'
            })
    
    # Spike-based insights
    if price_df is not None and not price_df.empty:
        spikes = detect_price_spikes(price_df)
        if not spikes.empty:
            insights.append({
                'type': 'warning',
                'title': 'Price Volatility Detected',
                'message': f"{len(spikes)} significant price spikes in last {hours_back} hours indicates grid stress.",
                'action': 'Review real-time operations, prepare contingency plans'
            })
    
    # Stress-based insights
    if stress['level'] in ['High', 'Critical']:
        insights.append({
            'type': 'critical',
            'title': f'{stress["level"]} Grid Stress',
            'message': f"Multiple stress factors detected: {', '.join(stress['factors'])}",
            'action': 'Implement emergency procedures, contact CAISO operations'
        })
    
    # Display insights
    if insights:
        for insight in insights:
            icon = '🔴' if insight['type'] == 'critical' else '⚠️' if insight['type'] == 'warning' else 'ℹ️'
            st.markdown(f"""
            **{icon} {insight['title']}**  
            {insight['message']}  
            *Recommended Action:* {insight['action']}
            """)
            st.markdown("---")
    else:
        st.success("✅ No critical issues detected. Grid operating within normal parameters.")

with col2:
    st.subheader("Future Capabilities")
    
    st.markdown("""
    **Phase 2 Features** (Coming Soon):
    
    🔮 **Machine Learning**
    - Predictive anomaly detection
    - Demand forecasting models
    - Price spike prediction
    
    📊 **Enhanced Analytics**
    - Historical trend analysis
    - Comparative benchmarking
    - Performance metrics
    
    🔔 **Alert Integration**
    - Email/SMS notifications
    - SCADA system integration
    - Automated incident tickets
    
    💡 **Optimization Tools**
    - Economic dispatch recommendations
    - Load shifting suggestions
    - Storage optimization
    """)

st.markdown("---")

# ==========================================
# SECTION 5: System Information
# ==========================================
with st.expander("ℹ️ System Information"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Data Quality**")
        if price_df is not None and not price_df.empty:
            st.success(f"✅ Price Data: {len(price_df)} records")
        else:
            st.warning("⚠️ Price Data: Unavailable")
        
        if demand_df is not None and not demand_df.empty:
            st.success(f"✅ Demand Forecast: {len(demand_df)} records")
        else:
            st.warning("⚠️ Demand Forecast: Unavailable")
    
    with col2:
        st.markdown("**Technical Details**")
        st.text("Data Source: CAISO OASIS API")
        st.text("Update Frequency: 5 minutes")
        st.text("Rate Limiting: 6s between requests")
        st.text("Caching: 10 minutes")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <strong>LADWP Grid Intelligence Dashboard</strong> | Phase 1: Real-Time Monitoring<br>
    Data Source: CAISO OASIS | Built with Streamlit & Python<br>
    <em>Empowering smarter grid operations through real-time data intelligence</em>
</div>
""", unsafe_allow_html=True)
