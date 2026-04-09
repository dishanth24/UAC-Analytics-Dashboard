import pandas as pd

# Load data
df = pd.read_csv("data/HHS_Unaccompanied_Alien_Children_Program.csv")

# Convert Date
df['Date'] = pd.to_datetime(df['Date'])

# Sort
df = df.sort_values(by='Date')

# Rename columns
df = df.rename(columns={
    'Children apprehended and placed in CBP custody*': 'CBP Intake',
    'Children in CBP custody': 'CBP Care',
    'Children transferred out of CBP custody': 'Transfers',
    'Children in HHS Care': 'HHS Care',
    'Children discharged from HHS Care': 'Discharges'
})

# 🔥 CLEAN + CONVERT TO NUMERIC
cols = ['CBP Intake', 'CBP Care', 'Transfers', 'HHS Care', 'Discharges']

for col in cols:
    df[col] = df[col].astype(str).str.replace(',', '')  # remove commas
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Metrics
df['Total Load'] = df['CBP Care'] + df['HHS Care']
df['Net Intake'] = df['Transfers'] - df['Discharges']
df['Growth Rate'] = df['Total Load'].pct_change() * 100
df['Backlog'] = df['Net Intake'].cumsum()

# Output
print(df[['Date', 'Total Load', 'Net Intake', 'Growth Rate', 'Backlog']].head())
