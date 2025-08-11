# scripts/simulate_iot_stream.py
import random
import psycopg2
from datetime import timedelta

DB_NAME = "tesla_energy"
DB_USER = "avaneesh"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = "5432"

def _rand_power_kw():
    return round(random.uniform(110, 190), 2)

def _rand_temp_c():
    return round(random.uniform(20, 42), 2)

def _rand_uptime():
    return random.random() < 0.97  # ~97%

def _rand_voltage(_power_kw):
    return round(400 + random.uniform(-8, 8), 2)

def _rand_current(power_kw, voltage):
    return round((power_kw * 1000) / max(voltage, 1e-6), 2)

def simulate_iot_data():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    # Ensure unique (site_id, timestamp) to make the job idempotent
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE indexname = 'uq_site_metrics_site_ts'
            ) THEN
                CREATE UNIQUE INDEX uq_site_metrics_site_ts
                ON site_metrics(site_id, timestamp);
            END IF;
        END $$;
    """)

    # Get DB's notion of "current hour" (avoids local/UTC mismatch)
    cur.execute("SELECT date_trunc('hour', now())::timestamp;")
    (now_hour,) = cur.fetchone()

    # latest per site (truncate to hour so minutes/seconds don't cause off-by-one)
    cur.execute("""
        WITH latest AS (
            SELECT site_id,
                   date_trunc('hour', MAX(timestamp))::timestamp AS max_ts_hour
            FROM site_metrics
            GROUP BY site_id
        )
        SELECT sm.site_id, latest.max_ts_hour
        FROM site_master sm
        LEFT JOIN latest ON latest.site_id = sm.site_id
        ORDER BY sm.site_id;
    """)
    rows = cur.fetchall()  # [(site_id, last_ts_hour_or_None), ...]

    inserts = []
    per_site_plan = []

    for site_id, last_ts_hour in rows:
        if last_ts_hour is None:
            # First ever backfill = previous hour only
            next_ts = now_hour - timedelta(hours=1)
        else:
            next_ts = last_ts_hour + timedelta(hours=1)

        planned = []
        while next_ts <= now_hour:
            power = _rand_power_kw()
            temp = _rand_temp_c()
            up = _rand_uptime()
            volt = _rand_voltage(power)
            curr = _rand_current(power, volt)
            inserts.append((site_id, next_ts, power, temp, up, volt, curr))
            planned.append(str(next_ts))
            next_ts += timedelta(hours=1)

        per_site_plan.append((site_id, planned))

    if inserts:
        cur.executemany("""
            INSERT INTO site_metrics
            (site_id, timestamp, power_output_kw, temperature_c, uptime_status, voltage, current)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (site_id, timestamp) DO NOTHING;
        """, inserts)
        conn.commit()

    cur.close()
    conn.close()

    # Logging: show what happened per site
    total = len(inserts)
    print(f"[simulate_iot_stream] DB now_hour = {now_hour}")
    for site_id, planned in per_site_plan:
        print(f"  - {site_id}: planned {len(planned)} rows -> {planned}")
    print(f"[simulate_iot_stream] Inserted {total} new records.")
    return total

if __name__ == "__main__":
    simulate_iot_data()
