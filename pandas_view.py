"""A pandas view of the same data, for the Unit IV topic on reading and
writing CSV and JSON files with pandas.

This module is optional. main.py calls it inside a try block, so if pandas is
not installed the rest of the project still runs exactly as before. The core
analysis uses only the standard library, and this adds the pandas round trip:
read the processed CSV, aggregate, write a CSV, write a JSON, read the JSON
back.

Run it on its own with:  python pandas_view.py
"""

import json
import os

OUTPUT_DIR = "output"
PROCESSED_CSV = os.path.join(OUTPUT_DIR, "processed_logs.csv")
HOURLY_PANDAS = os.path.join(OUTPUT_DIR, "hourly_pandas.csv")
PANDAS_JSON = os.path.join(OUTPUT_DIR, "pandas_summary.json")

# The timestamp layout this log uses, given to pandas explicitly instead of
# letting it guess.
TIME_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def summarise(csv_path=None, out_dir=OUTPUT_DIR):
    """Read the processed CSV with pandas and return extra measurements.

    Returns a dictionary to merge into the JSON report, or None if pandas is
    not available.
    """

    import pandas as pd

    csv_path = csv_path or PROCESSED_CSV

    # 1. Read a CSV file with pandas.
    frame = pd.read_csv(csv_path, dtype={"response_time_ms": "float"})

    # Keep the offset the log carries. Passing utc=True here would shift every
    # hour back by seven, and pandas would report the busiest hour as 02 while
    # the standard library reports 09.
    frame["hour"] = pd.to_datetime(
        frame["timestamp"], format=TIME_FORMAT
    ).dt.hour

    failed = frame[frame["status_code"] >= 400]

    # 2. Aggregate the same way the standard library version does, so the two
    #    can be compared.
    by_hour = (
        frame.groupby("hour")
        .agg(requests=("url", "size"), failed=("status_code",
                                              lambda s: (s >= 400).sum()))
        .reset_index()
    )
    by_hour["error_pct"] = (by_hour["failed"] / by_hour["requests"] * 100).round(2)

    busiest = by_hour.loc[by_hour["requests"].idxmax()]

    top_codes = {
        str(k): int(v)
        for k, v in failed.groupby("status_code").size()
                       .sort_values(ascending=False).head(5).items()
    }

    heaviest = [
        {"url": url, "total_bytes": int(total)}
        for url, total in frame.groupby("url")["response_bytes"].sum()
                                 .sort_values(ascending=False).head(5).items()
    ]

    # 3. Write a CSV with pandas.
    os.makedirs(out_dir, exist_ok=True)
    by_hour.to_csv(HOURLY_PANDAS, index=False)

    # 4. Write a JSON file with pandas, then read it back with pandas.
    #    The orient is records, a flat array of row objects. A nested object
    #    cannot be read back into a frame, and that raised an error here
    #    before.
    by_hour.to_json(PANDAS_JSON, orient="records", indent=2)

    reread = pd.read_json(PANDAS_JSON)
    round_trip = (
        len(reread) == len(by_hour)
        and int(reread["requests"].sum()) == len(frame)
    )

    # 5. Compare against the same table written by the standard library.
    stdlib_path = os.path.join(out_dir, "hourly_summary.csv")
    agrees = None

    if os.path.exists(stdlib_path):
        stdlib = pd.read_csv(stdlib_path)
        agrees = int(stdlib["requests"].sum()) == len(frame)

    print(f"Pandas hourly table saved: {HOURLY_PANDAS}")
    print(f"Pandas summary saved:      {PANDAS_JSON}")
    print(f"Pandas read-back check:    {'ok' if round_trip else 'MISMATCH'}")
    if agrees is not None:
        print(f"Agrees with csv.writer:    {'yes' if agrees else 'no'}")

    return {
        "engine": f"pandas {pd.__version__}",
        "rows_read": int(len(frame)),
        "busiest_hour": int(busiest["hour"]),
        "busiest_hour_requests": int(busiest["requests"]),
        "peak_hour_error_pct": float(busiest["error_pct"]),
        "worst_hour_error_pct": float(by_hour["error_pct"].max()),
        "worst_hour": int(by_hour.loc[by_hour["error_pct"].idxmax(), "hour"]),
        "top_error_codes": top_codes,
        "top_urls_by_total_bytes": heaviest,
        "json_round_trip_ok": round_trip,
        "agrees_with_stdlib": agrees,
        "files": [HOURLY_PANDAS, PANDAS_JSON],
    }


if __name__ == "__main__":
    result = summarise()
    print(json.dumps(result, indent=2))
