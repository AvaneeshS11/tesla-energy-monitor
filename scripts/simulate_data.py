# scripts/simulate_data.py

import pandas as pd
import random
from datetime import datetime, timedelta
import os

# --- Configuration ---
NUM_SITES = 5
SITE_IDS = [f"SC{str(i).zfill(3)}" for i in range(1, NUM_SITES + 1)]
DAYS = 7  # simulate 7 days of hourly data
FREQ = "1H"

# --- Generate Simulated Data ---
def generate_data():
    rows = []
    start_time = datetime.now() - timedelta(days=DAYS)
    timestamps = pd.date_range(start=start_time, periods=DAYS * 24, freq=FREQ)

    for site_id in SITE_IDS:
        for ts in timestamps:
            temperature = round(random.uniform(15, 40), 2)
            power_output = round(random.uniform(50, 250), 2)
            uptime_status = random.choices([True, False], weights=[0.95, 0.05])[0]
            voltage = round(random.uniform(380, 420), 2)
            current = round(power_output / voltage * 1000, 2)

            rows.append({
                "site_id": site_id,
                "timestamp": ts,
                "power_output_kw": power_output,
                "temperature_c": temperature,
                "uptime_status": uptime_status,
                "voltage": voltage,
                "current": current
            })

    return pd.DataFrame(rows)

# --- Save to CSV ---
def save_to_csv(df):
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", "simulated_data.csv")
    df.to_csv(filepath, index=False)
    print(f"✅ Data saved to: {filepath}")

# --- Main Script ---
if __name__ == "__main__":
    df = generate_data()
    save_to_csv(df)
