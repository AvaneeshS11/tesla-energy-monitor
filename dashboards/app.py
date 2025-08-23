import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px

# ========================
# Database connection config
# ========================
DB_NAME = "tesla_energy"
DB_USER = "avaneesh"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = "5432"

# DB helper
def run_query(query):
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

last_updated = run_query("""
    SELECT MAX(timestamp) AS last_ts FROM site_metrics;
""").iloc[0,0]
st.caption(f"Last data ingest: **{last_updated}**")


# ========================
# STREAMLIT UI + FILTERS
# ========================
st.title("🧾 Tesla Energy Site Monitoring Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
site_options = list(run_query("SELECT DISTINCT site_id FROM site_metrics")["site_id"])
selected_sites = st.sidebar.multiselect("Select Sites", site_options, default=site_options)

min_date = run_query("SELECT MIN(timestamp) FROM site_metrics").iloc[0, 0]
max_date = run_query("SELECT MAX(timestamp) FROM site_metrics").iloc[0, 0]
start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# SQL-compatible site tuple
if len(selected_sites) == 1:
    selected_sites_tuple = f"('{selected_sites[0]}')"
else:
    selected_sites_tuple = str(tuple(selected_sites))

# Format dates
start_date_str = datetime.combine(start_date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
end_date_str = datetime.combine(end_date, datetime.max.time()).strftime('%Y-%m-%d %H:%M:%S')

# ========================
# SQL QUERIES
# ========================
summary_query = f"""
SELECT COUNT(DISTINCT site_id) AS total_sites, COUNT(*) AS total_records
FROM site_metrics
WHERE site_id IN {selected_sites_tuple}
AND timestamp BETWEEN '{start_date_str}' AND '{end_date_str}';
"""

uptime_query = f"""
SELECT site_id, ROUND(100 * SUM(CASE WHEN uptime_status THEN 1 ELSE 0 END) / COUNT(*), 2) AS avg_uptime
FROM site_metrics
WHERE site_id IN {selected_sites_tuple}
AND timestamp BETWEEN '{start_date_str}' AND '{end_date_str}'
GROUP BY site_id
ORDER BY site_id;
"""

power_query = f"""
SELECT timestamp, power_output_kw
FROM site_metrics
WHERE site_id IN {selected_sites_tuple}
AND timestamp BETWEEN '{start_date_str}' AND '{end_date_str}'
ORDER BY timestamp;
"""

summary_table_query = f"""
SELECT 
    site_id,
    ROUND(AVG(power_output_kw)::numeric, 2) AS avg_power_output,
    COUNT(*) AS total_records,
    ROUND(100.0 * SUM(CASE WHEN uptime_status THEN 1 ELSE 0 END) / COUNT(*), 2) AS avg_uptime
FROM site_metrics
WHERE site_id IN {selected_sites_tuple}
AND timestamp BETWEEN '{start_date_str}' AND '{end_date_str}'
GROUP BY site_id
ORDER BY site_id;
"""

# New query for Map visualization using site_metrics_flat
map_query = f"""
SELECT
    site_id,
    site_name,
    latitude,
    longitude,
    ROUND(100.0 * SUM(CASE WHEN uptime_status THEN 1 ELSE 0 END) / COUNT(*), 2) AS uptime_percent,
    ROUND(AVG(voltage)::numeric, 2) AS avg_voltage
FROM site_metrics_flat
WHERE site_id IN {selected_sites_tuple}
AND timestamp BETWEEN '{start_date_str}' AND '{end_date_str}'
GROUP BY site_id, site_name, latitude, longitude
ORDER BY site_id;
"""



# ========================
# Run Queries
# ========================
summary_df = run_query(summary_query)
uptime_df = run_query(uptime_query)
power_df = run_query(power_query)
site_summary_df = run_query(summary_table_query)
map_df = run_query(map_query)

# ========================
# Process KPI Alerts
# ========================
def classify_alert(row):
    return "✅ Healthy" if row["avg_uptime"] >= 95 else "⚠️ Uptime < 95%"

site_summary_df["Alert"] = site_summary_df.apply(classify_alert, axis=1)
site_summary_df["avg_power_output"] = site_summary_df["avg_power_output"].round(2)
site_summary_df["avg_uptime"] = site_summary_df["avg_uptime"].round(2)

site_summary_df.rename(columns={
    "site_id": "Site ID",
    "avg_power_output": "Avg Power Output (kW)",
    "total_records": "Record Count",
    "avg_uptime": "Avg Uptime (%)",
    "Alert": "⚠️ Alert Status"
}, inplace=True)

def highlight_alerts(row):
    if "⚠️" in row["⚠️ Alert Status"]:
        return ['border: 2px solid red; text-align: center'] * len(row)
    else:
        return ['text-align: center'] * len(row)

# ========================
# Dashboard Display
# ========================
st.markdown("### ⚡ Summary Statistics")
st.metric("Total Sites", int(summary_df["total_sites"][0]))
st.metric("Total Records", int(summary_df["total_records"][0]))

st.markdown("### 📊 Uptime % by Site")
st.bar_chart(uptime_df.set_index("site_id"))

st.markdown("### 🚨 Site-Level KPI Alerts")
st.dataframe(site_summary_df.style.apply(highlight_alerts, axis=1), use_container_width=True)

st.markdown("### 📈 Power Output Over Time")
power_df["timestamp"] = pd.to_datetime(power_df["timestamp"])
fig = px.line(
    power_df,
    x="timestamp",
    y="power_output_kw",
    title="Power Output (kW) Over Time",
    labels={"timestamp": "Time", "power_output_kw": "Power (kW)"}
)
fig.update_layout(
    xaxis_title="Timestamp",
    yaxis_title="Power Output (kW)",
    xaxis=dict(tickformat="%b %d\n%H:%M", showgrid=True)
)
st.plotly_chart(fig, use_container_width=True)

# ========================
# 🗺️ Site Locations with Uptime Health (Fixed Dot Size + Correct Tooltip)
# ========================
st.markdown("### 🗺️ Site Locations with Uptime Health")

# Add a color column based on uptime
map_df["color"] = map_df["uptime_percent"].apply(lambda x: "green" if x >= 95 else "orange")

# Plot the map
map_fig = px.scatter_mapbox(
    map_df,
    lat="latitude",
    lon="longitude",
    hover_name="site_name",
    hover_data={
        "uptime_percent": True,
        "avg_voltage": True,
        "latitude": False,
        "longitude": False,
        "color": False
    },
    color="color",
    color_discrete_map={
        "green": "green",
        "orange": "orange"
    },
    size=None,
    zoom=3,
    height=500
)

# Adjust marker size to medium
map_fig.update_traces(marker=dict(size=10))

map_fig.update_layout(
    mapbox_style="open-street-map",
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)

st.plotly_chart(map_fig, use_container_width=True)
