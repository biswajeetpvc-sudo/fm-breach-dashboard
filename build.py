"""
build.py — Run via GitHub Actions or locally.
Reads data/FK_Breach_Dashboard.xlsx → writes data.json
index.html fetches data.json at runtime (no embedding needed).
"""
import json, re, os
import pandas as pd

EXCEL_PATH  = "data/FK_Breach_Dashboard.xlsx"
OUTPUT_JSON = "data.json"

print(f"Reading {EXCEL_PATH}...")
xl = pd.ExcelFile(EXCEL_PATH)

all_rows = []
for sheet in xl.sheet_names:
    sheet = sheet.strip()
    if not re.match(r'^\d{2}-\d{2}-\d{4}$', sheet):
        print(f"  Skipping: {sheet}")
        continue

    df = xl.parse(sheet)
    df.columns = [c.strip() for c in df.columns]

    col = lambda *names: next((c for c in df.columns for n in names if c.lower()==n.lower()), None)
    zone_col   = col('ph_zone','zone')
    gm_col     = col('GM','gm')
    rm_col     = col('RM','rm')
    am_col     = col('AM','am')
    ph_col     = col('ph_name','ph','hub')
    bucket_col = col('Bucket','bucket')
    cpd_col    = col('cpd','CPD','cpd_breach')

    if not bucket_col or not ph_col:
        print(f"  Skipping {sheet}: missing columns")
        continue

    df = df.dropna(subset=[bucket_col])
    df['_zone']   = df[zone_col].fillna('Unknown').astype(str).str.strip() if zone_col else 'Unknown'
    df['_gm']     = df[gm_col].fillna('').astype(str).str.strip()   if gm_col   else ''
    df['_rm']     = df[rm_col].fillna('').astype(str).str.strip()   if rm_col   else ''
    df['_am']     = df[am_col].fillna('').astype(str).str.strip()   if am_col   else ''
    df['_ph']     = df[ph_col].fillna('Unknown').astype(str).str.strip()
    df['_bucket'] = df[bucket_col].astype(str).str.strip()
    df['_cpd']    = df[cpd_col].astype(str).str.lower().isin(['1','yes','true']) if cpd_col else False

    agg = df.groupby(['_date' if '_date' in df.columns else '_ph',
                      '_zone','_gm','_rm','_am','_ph','_bucket','_cpd']).size()

    df['_date'] = sheet
    agg = df.groupby(['_date','_zone','_gm','_rm','_am','_ph','_bucket','_cpd']).size().reset_index(name='cnt')
    for _, row in agg.iterrows():
        all_rows.append({
            'date':   row['_date'],
            'zone':   row['_zone'],
            'gm':     row['_gm'],
            'rm':     row['_rm'],
            'am':     row['_am'],
            'ph':     row['_ph'],
            'bucket': row['_bucket'],
            'cpd':    bool(row['_cpd']),
            'cnt':    int(row['cnt']),
        })
    print(f"  {sheet}: {len(df):,} rows")

with open(OUTPUT_JSON, 'w') as f:
    json.dump(all_rows, f, ensure_ascii=True, separators=(',',':'))

print(f"\nDone: {OUTPUT_JSON} ({len(json.dumps(all_rows))/1024:.1f} KB, {len(all_rows)} records)")
