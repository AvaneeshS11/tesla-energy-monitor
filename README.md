# Tesla Energy Monitor (Simulated Uptime Dashboard)

## 📌 Goal
Streamlit dashboard + PostgreSQL backend that simulates and visualizes performance for a fleet of Tesla Energy sites. It includes an hourly IoT data simulator (idempotent backfill), SQL views for analytics, KPI/alerting logic, and an interactive map with health coloring (green = healthy, orange = attention).

## What this shows
- Live(ish) data: a Python job writes hourly records per site into Postgres (safe to run repeatedly).
- Analytics & viz:
  - KPIs (total sites, total records)
  - Uptime % by site (bar)
  - Power output over time (zoomable Plotly line)
  - Map of sites with hover details & health colors
  - KPI Alerts table (rows outlined if below thresholds)
    
- Ops skills: SQL, Python, Postgres, Streamlit; optional schedulers (Airflow or GitHub Actions).

## Architecture (high level) 

[simulate_iot_stream.py]  -->  PostgreSQL (tesla_energy)
   (hourly, idempotent)       ├─ site_master            (static sites & geo)
                              ├─ site_metrics           (time-series readings)
                              └─ site_metrics_flat VIEW (join + ready for analytics)

[Streamlit app] ----> queries the DB and renders KPIs, charts, and a health map
(Optional) Airflow/GitHub Actions ----> schedule the simulator hourly

## Tech Stack
- PostgreSQL
- Python (pandas, psycopg2, plotly, SQLAlchemy)
- Streamlit
- Airflow
- DBeaver

## Data Model 
- site_master(site_id, site_name, latitude, longitude)
  Static reference of 5 demo sites.

- site_metrics(site_id, timestamp, power_output_kw, temperature_c, uptime_status, voltage, current)
  Hourly time‑series measurements simulated per site.

- site_metrics_flat (VIEW)
  site_metrics joined to site_master for convenience in the app and map.

- Uniqueness: UNIQUE (site_id, timestamp) prevents duplicates. The simulator uses ON CONFLICT DO NOTHING.

## 🚀 Features
- Simulated energy + uptime data for sites
- SQL-based analysis of site KPIs
- Interactive dashboard (Streamlit)
- (Optional) ETL automation with Airflow

## 📁 Folder Structure
- `scripts/`: Python simulation and ingestion  
- `sql/`: PostgreSQL schema + analysis queries  
- `dashboards/`: Streamlit dashboard  
- `data/`: Simulated sensor datasets
