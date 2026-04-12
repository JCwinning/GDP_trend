#!/usr/bin/env python3
"""
Patch: Download real GDP (constant 2015 USD) for all countries and merge into existing CSV.
Run this once to fix the missing gdp_constant_2015_usd data.
"""

import pandas as pd
import wbgapi as wb
import time

CSV_PATH = "data/gdp_data_2000_present.csv"
INDICATOR_CODE = "NY.GDP.MKTP.KD"
INDICATOR_NAME = "gdp_constant_2015_usd"
START_YEAR = 2000
END_YEAR = 2024
BATCH_SIZE = 30

print("=" * 60)
print("Patch: Downloading Real GDP (constant 2015 USD)")
print("=" * 60)

# ── Step 1: Load existing data ────────────────────────────────
print("\n[1/4] Loading existing CSV...")
df_existing = pd.read_csv(CSV_PATH)
print(f"  Existing records: {len(df_existing):,}")
print(f"  gdp_constant_2015_usd records BEFORE: "
      f"{(df_existing['indicator'] == INDICATOR_NAME).sum()}")

# ── Step 2: Drop existing gdp_constant_2015_usd rows ─────────
print("\n[2/4] Removing old gdp_constant_2015_usd records...")
df_base = df_existing[df_existing["indicator"] != INDICATOR_NAME].copy()
print(f"  Records after removal: {len(df_base):,}")

# ── Step 3: Get list of unique countries in the dataset ───────
country_info = (
    df_base[["country_name", "country_code_2", "country_code_3", "continent"]]
    .drop_duplicates()
)
all_codes = country_info["country_code_3"].dropna().tolist()
code_to_meta = {
    row["country_code_3"]: row
    for _, row in country_info.iterrows()
}

print(f"\n[3/4] Downloading {INDICATOR_CODE} for {len(all_codes)} countries "
      f"({START_YEAR}–{END_YEAR})...")

new_records = []
batches = [all_codes[i:i+BATCH_SIZE] for i in range(0, len(all_codes), BATCH_SIZE)]

for batch_idx, batch_codes in enumerate(batches, 1):
    try:
        data = wb.data.fetch(
            INDICATOR_CODE,
            batch_codes,
            time=range(START_YEAR, END_YEAR + 1),
        )
        batch_count = 0
        for point in data:
            if point["value"] is None:
                continue
            code = point["economy"]
            if code not in code_to_meta:
                continue
            meta = code_to_meta[code]
            year_str = point["time"]
            year = int(year_str[2:]) if year_str.startswith("YR") else int(year_str)
            new_records.append({
                "country_name":   meta["country_name"],
                "country_code_2": meta["country_code_2"],
                "country_code_3": code,
                "continent":      meta["continent"],
                "year":           year,
                "indicator":      INDICATOR_NAME,
                "value":          round(point["value"]),
            })
            batch_count += 1

        print(f"  Batch {batch_idx}/{len(batches)} done — {batch_count} points fetched")
    except Exception as e:
        print(f"  Batch {batch_idx}/{len(batches)} ERROR: {e}")

    time.sleep(0.3)

print(f"\n  Total new records: {len(new_records):,}")
countries_downloaded = len({r["country_name"] for r in new_records})
print(f"  Countries with real GDP data: {countries_downloaded}")

# ── Step 4: Merge and save ────────────────────────────────────
print("\n[4/4] Merging and saving CSV...")
df_new = pd.DataFrame(new_records)
df_final = pd.concat([df_base, df_new], ignore_index=True)

# Sort for readability
df_final = df_final.sort_values(
    ["country_name", "indicator", "year"]
).reset_index(drop=True)

df_final.to_csv(CSV_PATH, index=False)

print(f"  Total records saved: {len(df_final):,}")
print(f"  gdp_constant_2015_usd records AFTER: "
      f"{(df_final['indicator'] == INDICATOR_NAME).sum()}")
print("\n✅ Patch complete! Restart the Streamlit app to see updated data.")
