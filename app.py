import streamlit as st
import pandas as pd

# Page config
st.set_page_config(page_title="UAC Analytics Dashboard", layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>UAC System Capacity Dashboard</h1>", unsafe_allow_html=True)
st.markdown(
    """
    <p style='text-align: center; font-size: 18px; color: #4B5563;'>
        This dashboard analyzes system capacity and care load for unaccompanied children using CBP and HHS data.
    </p>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

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
st.sidebar.header("🔍 Filters")
start_date = st.sidebar.date_input("Start Date", df['Date'].min())
end_date = st.sidebar.date_input("End Date", df['Date'].max())

filtered_df = df[(df['Date'] >= pd.to_datetime(start_date)) &
                 (df['Date'] <= pd.to_datetime(end_date))]

if filtered_df.empty:
    st.warning("No data available for selected date range.")
    st.stop()

# KPI Section
st.subheader("📊 Key Performance Indicators")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Load", f"{int(filtered_df['Total Load'].iloc[-1]):,}")
k2.metric("Net Intake", f"{int(filtered_df['Net Intake'].iloc[-1]):,}")
k3.metric("Backlog", f"{int(filtered_df['Backlog'].iloc[-1]):,}")
k4.metric("Avg Growth %", f"{filtered_df['Growth Rate'].mean():.2f}%")
k5.metric("Discharge Ratio", f"{filtered_df['Discharge Ratio'].mean():.2f}")

st.markdown("---")

# Charts Section
st.subheader("📈 Trends Analysis")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### Total System Load")
    st.line_chart(filtered_df.set_index('Date')['Total Load'])

with c2:
    st.markdown("### Net Intake")
    st.line_chart(filtered_df.set_index('Date')['Net Intake'])

c3, c4 = st.columns(2)

with c3:
    st.markdown("### Backlog Trend")
    st.line_chart(filtered_df.set_index('Date')['Backlog'])

with c4:
    st.markdown("### CBP vs HHS Care")
    st.line_chart(filtered_df.set_index('Date')[['CBP Care', 'HHS Care']])

st.markdown("---")

# Advanced Analytics Section
st.subheader("📊 Advanced Analysis")

c5, c6 = st.columns(2)

with c5:
    st.markdown("### Rolling Load Stability")
    st.line_chart(filtered_df.set_index('Date')[['7-Day Avg Load', '14-Day Avg Load']])

with c6:
    st.markdown("### System Volatility")
    st.line_chart(filtered_df.set_index('Date')['Volatility'])

st.markdown("---")

# Data Table
st.subheader("📋 Detailed Data View")
st.dataframe(filtered_df, use_container_width=True)

# Insights
st.markdown("## 📌 Key Insights")

st.success("""
✔ System experiences stress when Net Intake remains consistently positive  
✔ Backlog accumulation indicates delayed discharge capacity  
✔ Rolling averages reveal sustained pressure across care operations  
✔ Volatility spikes highlight unstable care load conditions  
✔ Balanced discharge improves system stability and reduces care burden  
""")
