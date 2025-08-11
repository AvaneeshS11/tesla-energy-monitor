import streamlit as st
import pandas as pd

# Load data
df = pd.read_csv("data/simulated_data.csv")

# Title
st.title("🔋 Tesla Energy Site Monitoring Dashboard")

# Summary metrics
st.subheader("⚡ Summary Statistics")
st.metric("Total Sites", df['site_id'].nunique())
st.metric("Total Records", len(df))

# Uptime bar chart
st.subheader("📊 Uptime % by Site")
uptime_df = (
    df.groupby('site_id')['uptime_status']
    .mean()
    .reset_index()
    .rename(columns={"uptime_status": "uptime_percent"})
)
uptime_df['uptime_percent'] = (uptime_df['uptime_percent'] * 100).round(2)
st.bar_chart(uptime_df.set_index('site_id'))

# Power output trend
st.subheader("📈 Power Output Over Time")
df['timestamp'] = pd.to_datetime(df['timestamp'])
trend_df = df.groupby(pd.Grouper(key='timestamp', freq='H'))['power_output_kw'].mean()
st.line_chart(trend_df)
