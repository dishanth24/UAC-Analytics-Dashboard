import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="UAC Analytics Dashboard", layout="wide")
st.markdown("""
<style>

/* Streamlit Tabs */
button[data-baseweb="tab"] {
    font-size: 28px !important;
    font-weight: 700 !important;
    padding: 12px 20px !important;
}

</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
.block-container{
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
}
.chart-card{
    background:#111827;
    padding:20px;
    border-radius:15px;
    border:1px solid #374151;
    margin-bottom:20px;
}
.section-title{
    font-size:28px;
    font-weight:700;
    margin-bottom:15px;
}
div[data-testid="stMetric"]{
    background:#111827;
    border:1px solid #374151;
    padding:15px;
    border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("""
<div style="
background:linear-gradient(135deg,#1e3a8a,#2563eb);
padding:30px;
border-radius:20px;
text-align:center;
margin-bottom:25px;
">
<h1 style="color:white;">
📊 UAC System Capacity & Care Load Analytics Dashboard
</h1>
<p style="color:#dbeafe;">
Healthcare Analytics Framework for Monitoring Capacity,
Care Load and Operational Pressure
</p>
</div>
""", unsafe_allow_html=True)
st.markdown(
    """
    <p style='text-align: center; font-size: 18px; color: #4B5563;'>
        This dashboard analyzes system capacity and care load for unaccompanied children using CBP and HHS data.
    </p>
    """,
    unsafe_allow_html=True
)
st.markdown("---")
st.markdown("""
<style>
.metric-card{
background:#111827;
padding:20px;
border-radius:12px;
border:1px solid #374151;
text-align:center;
}
.metric-value{
font-size:32px;
font-weight:bold;
color:#60A5FA;
}
.metric-label{
font-size:15px;
color:#D1D5DB;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
section[data-testid="stSidebar"]{
    background: #111827;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{
    color:white;
}
</style>
""", unsafe_allow_html=True)
# Load data
try:
    df = pd.read_csv("data/HHS_Unaccompanied_Alien_Children_Program.csv")
except:
    st.error("Dataset not found. Please check file path.")
    st.stop()

# Preprocessing
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values(by='Date')

df = df.rename(columns={
    'Children apprehended and placed in CBP custody*': 'CBP Intake',
    'Children in CBP custody': 'CBP Care',
    'Children transferred out of CBP custody': 'Transfers',
    'Children in HHS Care': 'HHS Care',
    'Children discharged from HHS Care': 'Discharges'
})

cols = ['CBP Intake', 'CBP Care', 'Transfers', 'HHS Care', 'Discharges']
for col in cols:
    df[col] = df[col].astype(str).str.replace(',', '')
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Core Metrics
df['Total Load'] = df['CBP Care'] + df['HHS Care']
df['Net Intake'] = df['Transfers'] - df['Discharges']
df['Growth Rate'] = df['Total Load'].pct_change() * 100
df['Backlog'] = df['Net Intake'].cumsum()

# Advanced Analytics
df['7-Day Avg Load'] = df['Total Load'].rolling(7).mean()
df['14-Day Avg Load'] = df['Total Load'].rolling(14).mean()
df['Volatility'] = df['Total Load'].rolling(7).std()
df['Discharge Ratio'] = df['Discharges'] / df['Transfers']

# Sidebar
st.sidebar.title("⚙ Dashboard Controls")
st.sidebar.markdown("---")
start_date = st.sidebar.date_input("Start Date", df['Date'].min())
end_date = st.sidebar.date_input("End Date", df['Date'].max())

metric_option = st.sidebar.selectbox(
    "Select Metric",
    ["Total Load", "Net Intake", "Backlog", "CBP Care", "HHS Care"]
)

time_granularity = st.sidebar.selectbox(
    "Time Granularity",
    ["Daily", "Weekly", "Monthly"]
)

filtered_df = df[(df['Date'] >= pd.to_datetime(start_date)) &
                 (df['Date'] <= pd.to_datetime(end_date))]
# Forecasting Data
forecast_days = 30

last_date = df['Date'].max()
future_dates = pd.date_range(
    start=last_date + pd.Timedelta(days=1),
    periods=forecast_days
)

recent_avg = filtered_df['Total Load'].dropna().tail(30).mean()

if pd.isna(recent_avg):
    recent_avg = filtered_df['Total Load'].mean()

trend = (
    filtered_df['Total Load'].iloc[-1]
    -filtered_df['Total Load'].iloc[max(0, len(filtered_df)-30)]
) / 30

forecast_values = [
    filtered_df['Total Load'].iloc[-1] + trend * i
    for i in range(1, forecast_days + 1)
]

forecast_df = pd.DataFrame({
    'Date': future_dates,
    'Forecast Load': forecast_values
})

if filtered_df.empty:
    st.warning("No data available for selected date range.")
    st.stop()

# Time Granularity Processing
if time_granularity == "Weekly":
    display_df = filtered_df.resample('W', on='Date').mean(numeric_only=True).reset_index()
elif time_granularity == "Monthly":
    display_df = filtered_df.resample('ME', on='Date').mean(numeric_only=True).reset_index()
else:
    display_df = filtered_df.copy()

# Early vs Late Timeline Comparison
midpoint = len(filtered_df) // 2
early_period = filtered_df.iloc[:midpoint]
late_period = filtered_df.iloc[midpoint:]

early_avg_load = early_period['Total Load'].mean()
late_avg_load = late_period['Total Load'].mean()

# High-load threshold detection
high_load_threshold = filtered_df['Total Load'].quantile(0.90)
high_load_days = filtered_df[filtered_df['Total Load'] >= high_load_threshold]

# Data Quality & Validation
missing_dates = pd.date_range(df['Date'].min(), df['Date'].max()).difference(df['Date'])
duplicate_dates = df[df.duplicated(subset='Date', keep=False)]

invalid_transfers = df[df['Transfers'] > df['CBP Care']]
invalid_discharges = df[df['Discharges'] > df['HHS Care']]

# KPI Section

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "📈 Analytics",
    "🔮 Forecasting",
    "🛡 Validation",
    "📋 Data"
])

st.subheader("📊 Key Performance Indicators")

s1, s2, s3 = st.columns(3)

with s1:
    st.info(f"Peak Load: {int(filtered_df['Total Load'].max()):,}")

with s2:
    st.info(f"Average Load: {int(filtered_df['Total Load'].mean()):,}")

with s3:
    st.info(f"High Load Days: {len(high_load_days)}")

st.markdown("""
<style>
.card {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    border: 1px solid #334155;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

.metric {
    font-size: 38px;
    font-weight: 700;
    color: #60A5FA;
}

.label {
    font-size: 18px;
    color: #CBD5E1;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="card">
        <div class="label">Total Load</div>
        <div class="metric">{int(filtered_df['Total Load'].iloc[-1]):,}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="card">
        <div class="label">Net Intake</div>
        <div class="metric">{int(filtered_df['Net Intake'].iloc[-1]):,}</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="card">
        <div class="label">Backlog</div>
        <div class="metric">{int(filtered_df['Backlog'].iloc[-1]):,}</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="card">
        <div class="label">Avg Growth %</div>
        <div class="metric">{filtered_df['Growth Rate'].mean():.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="card">
        <div class="label">Discharge Ratio</div>
        <div class="metric">{filtered_df['Discharge Ratio'].mean():.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    

# Executive Overview
# Risk Indicator
avg_net_intake = filtered_df['Net Intake'].mean()

if avg_net_intake < 0:
    risk_status = "🟢 LOW RISK"
elif avg_net_intake < 50:
    risk_status = "🟡 MODERATE RISK"
else:
    risk_status = "🔴 HIGH RISK"

st.markdown("### 🚦 System Health Status")

st.success(f"Current System Status: {risk_status}")
st.markdown("### 🚨 Executive Overview")

risk = "Low"

if filtered_df['Net Intake'].mean() > 0:
    risk = "Medium"

if filtered_df['Net Intake'].mean() > 25:
    risk = "High"

st.info(
    f"""
    **Current Risk Level:** {risk}

    **Peak System Load:** {int(filtered_df['Total Load'].max()):,}

    **High Load Days:** {len(high_load_days)}

    **Average Net Intake:** {filtered_df['Net Intake'].mean():.2f}
    """
)

st.markdown("---") 
s1, s2, s3 = st.columns(3)

with s1:
    st.info(f"📈 Peak Load: {int(filtered_df['Total Load'].max()):,}")

with s2:
    st.info(f"📊 Average Load: {int(filtered_df['Total Load'].mean()):,}")

with s3:
    st.info(f"⚠ High Load Days: {len(high_load_days)}")

st.markdown("---")

# Charts Section
with tab2:
        st.subheader("📈 Trends Analysis")

c1, c2 = st.columns(2)

with c1:

    fig = px.area(
        display_df,
        x="Date",
        y="Total Load",
        title="Total Load Trend"
    )

fig.update_layout(
    template="plotly_dark",
    height=500,
      hovermode="x unified",
    margin=dict(l=20, r=20, t=50, b=20)
)   
fig.update_layout(
    paper_bgcolor="#111827",
    plot_bgcolor="#111827"
)

fig.update_xaxes(
    showgrid=False,
    linecolor="#374151"
)

fig.update_yaxes(
    gridcolor="#1F2937",
    linecolor="#374151"
)

st.plotly_chart(
    fig,
    use_container_width=True,
     key="total_load_chart"
)

with c2:

    fig = px.line(
        display_df,
        x="Date",
        y="Net Intake",
        title="Daily Net Intake Analysis"
    )

fig.update_layout(
    template="plotly_dark",
    height=500,
      hovermode="x unified",
    margin=dict(l=20, r=20, t=50, b=20)
)
fig.update_layout(
    paper_bgcolor="#111827",
    plot_bgcolor="#111827"
)

fig.update_xaxes(
    showgrid=False,
    linecolor="#374151"
)

fig.update_yaxes(
    gridcolor="#1F2937",
    linecolor="#374151"
)

st.plotly_chart(
    fig,
    use_container_width=True,
     key="net_intake_chart"
)

st.markdown("---")
st.subheader("📊 Capacity Analysis")

c3, c4 = st.columns([1,1])

with c3:
    fig = px.line(
        display_df,
        x="Date",
        y="Backlog",
        title="System Backlog Over Time"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500,
          hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_layout(
    paper_bgcolor="#111827",
    plot_bgcolor="#111827"
    )

    fig.update_xaxes(
    showgrid=False,
    linecolor="#374151"
    )

    fig.update_yaxes(
    gridcolor="#1F2937",
    linecolor="#374151"
    )
  
    st.plotly_chart(
    fig,
    use_container_width=True,
    key="backlog_trend"
)

with c4:
    fig = px.line(
        display_df,
        x="Date",
        y=["CBP Care", "HHS Care"],
        title="CBP Custody vs HHS Care Population"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_layout(
    paper_bgcolor="#111827",
    plot_bgcolor="#111827"
    )

    fig.update_xaxes(
    showgrid=False,
    linecolor="#374151" 
    )

    fig.update_yaxes(
    gridcolor="#1F2937",
    linecolor="#374151"
    )
 
    st.plotly_chart(
    fig,
    use_container_width=True,
    key="cbp_hhs_chart"
)

# Advanced Analytics Section
st.markdown("---")
st.subheader("🔮 Forecast Summary")

f1, f2, f3 = st.columns(3)

current_load = filtered_df['Total Load'].iloc[-1]
future_load = forecast_df['Forecast Load'].iloc[-1]

change_pct = ((future_load - current_load) / current_load) * 100

with f1:
    st.metric("Current Load", f"{int(current_load):,}")

with f2:
    st.metric("Forecast Load", f"{int(future_load):,}")

with f3:
    st.metric("Expected Change", f"{change_pct:.2f}%")

with tab3:

    st.subheader("📈 30-Day Capacity Forecast")

    fig_forecast = go.Figure()

    fig_forecast.add_trace(
        go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['Total Load'],
            mode='lines',
            name='Historical Load'
        )
    )

    fig_forecast.add_trace(
        go.Scatter(
            x=forecast_df['Date'],
            y=forecast_df['Forecast Load'],
            mode='lines',
            name='Forecast Load',
            line=dict(dash='dash')
        )
    )

    fig_forecast.update_layout(
        template="plotly_dark",
        height=500,
        title="Historical vs Forecasted System Load"
    )

    st.plotly_chart(
        fig_forecast,
        use_container_width=True,
        key="forecast_chart"
    )

    st.info(
        f"""
        Forecast based on the average system load of the most recent 30 days.

        Current Load: {int(filtered_df['Total Load'].iloc[-1]):,}

        Forecast Load: {recent_avg:,.0f}

        Forecast Horizon: {forecast_days} Days
        """
    )

st.markdown("---")
st.subheader("📉 Advanced Analytics")

c5, c6 = st.columns(2)

with c5:

    fig = px.line(
        display_df,
        x="Date",
        y=["7-Day Avg Load", "14-Day Avg Load"],
        title="Rolling Load Stability"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500,
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20
        )
    )
    fig.update_layout(
    paper_bgcolor="#111827",
    plot_bgcolor="#111827"
    )

    fig.update_xaxes(
    showgrid=False,
    linecolor="#374151"
    )

    fig.update_yaxes(
    gridcolor="#1F2937",
    linecolor="#374151"
    )

    fig.update_traces(
        line=dict(width=3)
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="rolling_avg_chart"
    )
 
    
with c6:
    fig = px.line(
        display_df,
        x="Date",
        y="Volatility",
        title="System Volatility"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_layout(
    paper_bgcolor="#111827",
    plot_bgcolor="#111827"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="volatility_chart"
    )
   
    
st.markdown("---")

# Trend Comparison & Load Pressure
with tab2:
    st.subheader("📌 Trend Comparison & Load Pressure")

t1, t2, t3 = st.columns(3)

t1.metric("Early Period Avg Load", f"{early_avg_load:,.0f}")
t2.metric("Late Period Avg Load", f"{late_avg_load:,.0f}")
t3.metric("High-Load Days", f"{len(high_load_days)}")

st.info(
    "This section compares early and late timeline system load to evaluate long-term pressure trends. "
    "High-load days represent periods where total care load exceeded the 90th percentile threshold."
)

st.markdown("---")

# Data Quality & Validation Section
with tab4:
        st.subheader("🛡️ Data Quality & Validation")

v1, v2, v3, v4 = st.columns(4)

v1.metric("Missing Dates", len(missing_dates))
v2.metric("Duplicate Dates", len(duplicate_dates))
v3.metric("Invalid Transfers", len(invalid_transfers))
v4.metric("Invalid Discharges", len(invalid_discharges))

st.info(
    "This section validates reporting consistency by checking for missing dates, duplicate entries, "
    "and logical inconsistencies in transfers and discharges."
)

st.markdown("---")
st.markdown("### ⬇ Download Center")

csv = display_df.to_csv(index=False)

st.download_button(
    label="Download Processed Dataset",
    data=csv,
    file_name="uac_processed_data.csv",
    mime="text/csv"
)
# Data Table
with tab5:
        st.subheader("📋 Detailed Data View")
        st.dataframe(display_df, use_container_width=True)

# Insights
st.markdown("## 📌 Key Insights")

st.success("""
✔ System experiences stress when Net Intake remains consistently positive  
✔ Backlog accumulation indicates delayed discharge capacity  
✔ Rolling averages reveal sustained pressure across care operations  
✔ Volatility spikes highlight unstable care load conditions  
✔ Balanced discharge improves system stability and reduces care burden  
""")
