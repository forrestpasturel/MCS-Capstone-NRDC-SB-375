"""
build_tract_dataset.py
======================
Reproducible geospatial ETL pipeline: builds a statewide, tract-level dataset
for the SB 375 / SB 1087 website by combining three data sources:

  1. CalEnviroScreen 4.0  — tract-level environmental / health scores
  2. Priority Populations 4.0 (CARB)  — DAC & low-income flags (AB 1550)
  3. Per-capita VMT (user-provided tract-level CSV)

Output:
  data/ca_tract_vmt_ces_pp.geojson   — full tract GeoJSON for mapping
  data/ca_tract_summary_stats.json   — statewide / urban / rural summary stats

Data sources & URLs:
  CalEnviroScreen 4.0:
    https://oehha.ca.gov/calenviroscreen/download-data
    ArcGIS FeatureServer:
      https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/
      CalEnviroScreen_4_0_Results_/FeatureServer/0
    CA Open Data:
      https://data.ca.gov/dataset/calenviroscreen-4-0-results

  Priority Populations 4.0 (CARB):
    https://gis.carb.arb.ca.gov/portal/home/item.html?id=0fa1e83c2f284b4f96d14a629e27fbe7

  VMT per capita (user-provided tract-level CSV):
    Expected at data/raw/vmt_by_tract.csv (see configuration section)

Run:
    cd data/
    python build_tract_dataset.py

    Optional flags:
      --skip-vmt       Skip VMT loading (CES + Priority Pops only)
      --skip-priority   Skip Priority Populations loading
      --no-simplify    Export full-resolution geometries
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION  — adjust paths and column names here
# ═══════════════════════════════════════════════════════════════════════════

HERE = Path(__file__).parent
RAW_DIR = HERE / "raw"
RAW_DIR.mkdir(exist_ok=True)

# ── CalEnviroScreen 4.0 ArcGIS REST endpoint ──────────────────────────────
CES_FEATURE_SERVICE_URL = (
    "https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/"
    "CalEnviroScreen_4_0_Results_/FeatureServer/0"
)

# ── CARB Priority Populations 4.0 ─────────────────────────────────────────
# The CARB portal item page is:
#   https://gis.carb.arb.ca.gov/portal/home/item.html?id=0fa1e83c2f284b4f96d14a629e27fbe7
# Typical REST endpoint pattern (may need adjustment):
PRIORITY_POP_SERVICE_URL = (
    "https://gis.carb.arb.ca.gov/portal/rest/services/Hosted/"
    "Priority_Populations_4_0/FeatureServer/0"
)

# ── VMT per-capita data (tract-level CSV) ─────────────────────────────────
# Place your statewide tract-level VMT file here.
# Expected schema:  tract_id, region_id, vmt_per_capita
#   tract_id       – 11-digit Census tract GEOID (string)
#   region_id      – MPO / county / Caltrans district code (string)
#   vmt_per_capita – daily VMT per person (miles/person/day, float)
VMT_CSV_PATH = RAW_DIR / "vmt_by_tract.csv"
VMT_TRACT_ID_COL = "tract_id"
VMT_REGION_COL = "region_id"
VMT_VALUE_COL = "vmt_per_capita"

# ── Emissions factor for optional GHG per-capita ──────────────────────────
# EPA average passenger vehicle: ~404 grams CO₂ per mile
# Source: https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle
CO2_GRAMS_PER_MILE = 404.0

# ── Thresholds ────────────────────────────────────────────────────────────
HIGH_VMT_QUANTILE = 0.75       # top 25 %
HIGH_POLLUTION_QUANTILE = 75   # CES percentile (0-100 scale)
DAC_CES_PERCENTILE = 75        # CES-based DAC fallback threshold

# ── Output paths ──────────────────────────────────────────────────────────
OUTPUT_GEOJSON = HERE / "ca_tract_vmt_ces_pp.geojson"
OUTPUT_STATS_JSON = HERE / "ca_tract_summary_stats.json"

# Geometry simplification tolerance (meters, in CA Albers EPSG:3310)
SIMPLIFY_TOLERANCE_M = 100


# ═══════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def query_arcgis_all_features(service_url, out_fields="*", where="1=1",
                              out_sr=4326, page_size=2000):
    """
    Download all features from an ArcGIS REST FeatureServer using pagination.
    Returns a GeoDataFrame.
    """
    import geopandas as gpd
    import requests

    query_url = f"{service_url}/query"
    all_features = []
    offset = 0

    print(f"  Querying: {service_url}")
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "outSR": out_sr,
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        try:
            resp = requests.get(query_url, params=params, timeout=120)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"    ⚠ Request failed at offset {offset}: {e}")
            break

        data = resp.json()
        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        print(f"    Fetched {len(all_features)} features...", end="\r")
        offset += page_size

        # If fewer than page_size returned, we're done
        if len(features) < page_size:
            break

    print(f"    Total features downloaded: {len(all_features)}")

    if not all_features:
        return gpd.GeoDataFrame()

    geojson_collection = {
        "type": "FeatureCollection",
        "features": all_features,
    }
    gdf = gpd.GeoDataFrame.from_features(geojson_collection, crs=f"EPSG:{out_sr}")
    return gdf


def safe_float(val):
    """Convert a value to float, returning NaN for blanks/None."""
    if val is None:
        return np.nan
    s = str(val).strip()
    if s == "" or s.lower() == "none":
        return np.nan
    try:
        return float(s)
    except (ValueError, TypeError):
        return np.nan


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 1: Load CalEnviroScreen 4.0
# ═══════════════════════════════════════════════════════════════════════════

def load_ces40():
    """
    Load CalEnviroScreen 4.0 tract data from the OEHHA ArcGIS FeatureServer.
    Returns a GeoDataFrame with standardized column names.
    """
    print("\n" + "=" * 60)
    print("STEP 1: Load CalEnviroScreen 4.0")
    print("=" * 60)

    # Fields we need from the service (confirmed from service metadata)
    out_fields = ",".join([
        "TractTXT", "tract", "ACS2019TotalPop",
        "CIscore", "CIscoreP",
        "Pollution", "PollutionScore", "PollutionP",
        "PopChar", "PopCharScore", "PopCharP",
        "pmP", "ozoneP", "dieselP", "trafficP",
        "pm", "ozone", "diesel", "traffic",
    ])

    gdf = query_arcgis_all_features(
        CES_FEATURE_SERVICE_URL,
        out_fields=out_fields,
    )

    if gdf.empty:
        print("  ✗ Failed to load CalEnviroScreen 4.0 data")
        sys.exit(1)

    print(f"  ✓ Loaded {len(gdf)} tracts")
    print(f"  Columns: {list(gdf.columns)}")

    # ── Standardize GEOID ─────────────────────────────────────────────────
    # TractTXT is a string tract ID; 'tract' is numeric.
    # We need an 11-digit FIPS code (state + county + tract).
    if "TractTXT" in gdf.columns:
        gdf["geoid"] = gdf["TractTXT"].astype(str).str.strip()
    elif "tract" in gdf.columns:
        # Numeric: convert to int then string, left-pad to 11 digits
        gdf["geoid"] = (
            gdf["tract"]
            .apply(lambda x: str(int(x)) if pd.notna(x) else "")
            .str.zfill(11)
        )
    else:
        print("  ✗ Cannot find tract identifier column")
        sys.exit(1)

    # Ensure 11-digit geoid (California FIPS = 06)
    # Some may be 10 digits; pad with leading zero
    gdf["geoid"] = gdf["geoid"].str.zfill(11)
    # Filter to California only (FIPS starts with '06')
    gdf = gdf[gdf["geoid"].str.startswith("06")].copy()

    # ── Rename fields to target schema ────────────────────────────────────
    rename_map = {
        "ACS2019TotalPop": "population_total",
        "CIscore": "ces_score",
        "CIscoreP": "ces_percentile",
        "Pollution": "pollution_burden",
        "PollutionP": "pollution_burden_pct",
        "PopCharP": "population_char_pct",
        "pmP": "pm25_pct",
        "ozoneP": "ozone_pct",
        "dieselP": "diesel_pm_pct",
        "trafficP": "traffic_density_pct",
    }

    for src, dst in rename_map.items():
        if src in gdf.columns:
            gdf[dst] = gdf[src].apply(safe_float)
        else:
            gdf[dst] = np.nan
            print(f"    ⚠ Column '{src}' not found; '{dst}' set to NaN")

    # Keep only the columns we need plus geometry
    keep = ["geoid", "geometry", "population_total", "ces_score",
            "ces_percentile", "pollution_burden", "pollution_burden_pct",
            "population_char_pct", "pm25_pct", "ozone_pct",
            "diesel_pm_pct", "traffic_density_pct"]
    gdf = gdf[[c for c in keep if c in gdf.columns]].copy()

    # Drop rows with no geometry or invalid geoid
    gdf = gdf.dropna(subset=["geometry"])
    gdf = gdf[gdf.geometry.is_valid]
    gdf = gdf[gdf["geoid"].str.len() == 11]

    print(f"  ✓ {len(gdf)} California tracts after cleanup")
    return gdf


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 2: Load Priority Populations 4.0 (DAC / Low-Income flags)
# ═══════════════════════════════════════════════════════════════════════════

def load_priority_pops(ces_gdf):
    """
    Load CARB Priority Populations 4.0 feature layer.
    Falls back to CES-derived DAC flag if service is unavailable.

    Returns a DataFrame with: geoid, dac_flag, low_income_flag, dac_low_income_combo
    """
    print("\n" + "=" * 60)
    print("STEP 2: Load Priority Populations 4.0")
    print("=" * 60)

    pp_df = None

    # ── Attempt to load from CARB ArcGIS REST service ─────────────────────
    try:
        print("  Attempting CARB Priority Populations service...")
        pp_gdf = query_arcgis_all_features(
            PRIORITY_POP_SERVICE_URL,
            out_fields="*",
        )

        if not pp_gdf.empty:
            print(f"  ✓ Loaded {len(pp_gdf)} features from CARB")
            print(f"    Columns: {list(pp_gdf.columns)[:15]}...")

            # Identify the tract/GEOID column
            cols_lower = {c.lower(): c for c in pp_gdf.columns}
            geoid_col = None
            for candidate in ["census_tract", "tract", "geoid", "geoid10",
                              "geoid20", "tractce", "ct_id", "fips"]:
                if candidate in cols_lower:
                    geoid_col = cols_lower[candidate]
                    break

            # Identify DAC and low-income columns
            dac_col = None
            li_col = None
            for candidate in ["sb535dacdesignation", "sb535_dac",
                              "dac_designation", "dac", "sb535dac",
                              "disadvantaged_community"]:
                if candidate in cols_lower:
                    dac_col = cols_lower[candidate]
                    break
            for candidate in ["ab1550lowincome", "ab1550_lowincome",
                              "low_income", "lowincome", "li_designation",
                              "ab1550_li", "low_income_community"]:
                if candidate in cols_lower:
                    li_col = cols_lower[candidate]
                    break

            if geoid_col:
                pp_df = pd.DataFrame()
                pp_df["geoid"] = pp_gdf[geoid_col].astype(str).str.zfill(11)

                if dac_col:
                    # Handle various True/False representations
                    pp_df["dac_flag"] = pp_gdf[dac_col].apply(
                        lambda x: str(x).strip().lower() in
                        ("yes", "true", "1", "y", "dac")
                    )
                    print(f"    DAC column: '{dac_col}' → {pp_df['dac_flag'].sum()} DAC tracts")
                else:
                    pp_df["dac_flag"] = np.nan

                if li_col:
                    pp_df["low_income_flag"] = pp_gdf[li_col].apply(
                        lambda x: str(x).strip().lower() in
                        ("yes", "true", "1", "y", "low income", "lowincome")
                    )
                    print(f"    Low-income column: '{li_col}' → {pp_df['low_income_flag'].sum()} LI tracts")
                else:
                    pp_df["low_income_flag"] = np.nan

                pp_df = pp_df.drop_duplicates(subset=["geoid"], keep="first")
            else:
                print("    ⚠ Could not identify tract/GEOID column in CARB data")
                pp_df = None

    except Exception as e:
        print(f"  ⚠ CARB service unavailable: {e}")
        pp_df = None

    # ── Fallback: derive DAC from CES percentile ─────────────────────────
    if pp_df is None or pp_df["dac_flag"].isna().all():
        print("  → Falling back to CES-derived DAC flag (CES percentile ≥ 75)")
        pp_df = pd.DataFrame()
        pp_df["geoid"] = ces_gdf["geoid"].values
        pp_df["dac_flag"] = ces_gdf["ces_percentile"].apply(
            lambda x: bool(x >= DAC_CES_PERCENTILE) if pd.notna(x) else False
        ).values
        pp_df["low_income_flag"] = False  # Cannot derive from CES alone
        print(f"    DAC tracts (CES ≥ {DAC_CES_PERCENTILE}th pctile): {pp_df['dac_flag'].sum()}")

    # ── Compute combo field ──────────────────────────────────────────────
    def combo(row):
        dac = bool(row.get("dac_flag", False))
        li = bool(row.get("low_income_flag", False))
        if dac and li:
            return "DAC_and_low_income"
        elif dac:
            return "DAC_only"
        elif li:
            return "low_income_only"
        return "neither"

    pp_df["dac_low_income_combo"] = pp_df.apply(combo, axis=1)

    print(f"  ✓ Priority Populations: {len(pp_df)} tracts")
    print(f"    Combo breakdown:")
    for cat, cnt in pp_df["dac_low_income_combo"].value_counts().items():
        print(f"      {cat}: {cnt}")

    return pp_df[["geoid", "dac_flag", "low_income_flag", "dac_low_income_combo"]]


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 3: Load tract-level VMT per capita
# ═══════════════════════════════════════════════════════════════════════════

def load_vmt():
    """
    Load tract-level VMT per-capita data from a user-provided CSV.

    Expected file: data/raw/vmt_by_tract.csv
    Expected columns: tract_id, region_id, vmt_per_capita

    Returns a DataFrame with: geoid, region_id, vmt_per_capita
    """
    print("\n" + "=" * 60)
    print("STEP 3: Load VMT per-capita data")
    print("=" * 60)

    if not VMT_CSV_PATH.exists():
        print(f"  ✗ VMT file not found: {VMT_CSV_PATH}")
        print(f"    Create data/raw/vmt_by_tract.csv with columns:")
        print(f"      {VMT_TRACT_ID_COL}, {VMT_REGION_COL}, {VMT_VALUE_COL}")
        print("    VMT fields will be set to null.")
        return None

    print(f"  Reading: {VMT_CSV_PATH.name}")
    df = pd.read_csv(VMT_CSV_PATH, dtype={VMT_TRACT_ID_COL: str, VMT_REGION_COL: str})
    print(f"  Loaded {len(df)} rows, columns: {list(df.columns)}")

    # ── Validate expected columns ─────────────────────────────────────────
    for col in [VMT_TRACT_ID_COL, VMT_VALUE_COL]:
        if col not in df.columns:
            print(f"  ✗ Missing required column '{col}'. Available: {list(df.columns)}")
            print(f"    Update VMT_TRACT_ID_COL / VMT_VALUE_COL at the top of the script.")
            return None

    # ── Standardize ───────────────────────────────────────────────────────
    df["geoid"] = df[VMT_TRACT_ID_COL].astype(str).str.zfill(11)
    df["vmt_per_capita"] = pd.to_numeric(df[VMT_VALUE_COL], errors="coerce")
    df["region_id"] = df[VMT_REGION_COL].astype(str) if VMT_REGION_COL in df.columns else ""

    df = df.dropna(subset=["vmt_per_capita"])
    df = df[df["vmt_per_capita"] > 0]
    df = df.drop_duplicates(subset=["geoid"], keep="first")

    result = df[["geoid", "region_id", "vmt_per_capita"]].copy()

    print(f"  ✓ {len(result)} tracts with VMT data")
    print(f"    VMT per capita range: {result['vmt_per_capita'].min():.1f} – {result['vmt_per_capita'].max():.1f}")
    print(f"    VMT per capita mean:  {result['vmt_per_capita'].mean():.1f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 4: Merge and compute derived fields
# ═══════════════════════════════════════════════════════════════════════════

def build_unified_dataset(ces_gdf, pp_df, vmt_df):
    """
    Merge CES, Priority Populations, and VMT into a single GeoDataFrame.
    Compute derived fields (quantiles, flags, GHG, etc.).
    """
    import geopandas as gpd

    print("\n" + "=" * 60)
    print("STEP 4: Build unified tract dataset")
    print("=" * 60)

    gdf = ces_gdf.copy()

    # ── Join Priority Populations ─────────────────────────────────────────
    if pp_df is not None:
        gdf = gdf.merge(pp_df, on="geoid", how="left")
        # Fill NaN flags with False / "neither"
        gdf["dac_flag"] = gdf["dac_flag"].fillna(False).astype(bool)
        gdf["low_income_flag"] = gdf["low_income_flag"].fillna(False).astype(bool)
        gdf["dac_low_income_combo"] = gdf["dac_low_income_combo"].fillna("neither")
        print(f"  Joined Priority Populations: {gdf['dac_flag'].sum()} DAC tracts")
    else:
        gdf["dac_flag"] = False
        gdf["low_income_flag"] = False
        gdf["dac_low_income_combo"] = "neither"

    # ── Join VMT data ─────────────────────────────────────────────────────
    if vmt_df is not None:
        gdf = gdf.merge(vmt_df, on="geoid", how="left")
        # Rename vmt_per_capita → vmt_pc for downstream compatibility
        gdf["vmt_pc"] = gdf["vmt_per_capita"]
        vmt_count = gdf["vmt_pc"].notna().sum()
        print(f"  Joined VMT: {vmt_count}/{len(gdf)} tracts have VMT data")
    else:
        gdf["vmt_pc"] = np.nan
        gdf["region_id"] = ""
        print("  VMT data not available; vmt_pc set to NaN")

    # ── VMT index: ratio to statewide mean, scaled to 100 ────────────────
    statewide_mean = gdf["vmt_pc"].mean()  # excludes NaN by default
    if pd.notna(statewide_mean) and statewide_mean > 0:
        gdf["vmt_index"] = (gdf["vmt_pc"] / statewide_mean * 100).round(1)
    else:
        gdf["vmt_index"] = np.nan

    # ── VMT quantiles & category ──────────────────────────────────────────
    # vmt_pc_quantile: 0-1 rank based on raw VMT per capita
    gdf["vmt_pc_quantile"] = gdf["vmt_pc"].rank(pct=True, na_option="keep").round(4)
    # vmt_index_quantile / vmt_index_pctile: rank based on vmt_index
    gdf["vmt_index_quantile"] = gdf["vmt_index"].rank(pct=True, na_option="keep").round(4)
    gdf["vmt_index_pctile"] = (gdf["vmt_index_quantile"] * 100).round(1)

    # Tertile-based category
    def vmt_category(q):
        if pd.isna(q):
            return None
        if q < 1 / 3:
            return "low"
        elif q < 2 / 3:
            return "medium"
        return "high"

    gdf["vmt_pc_category"] = gdf["vmt_pc_quantile"].apply(vmt_category)

    # ── GHG per capita ────────────────────────────────────────────────────
    # ghg_pc_tpy = vmt_pc (mi/person/day) × 365 (days) × CO2_g/mi / 1e6 (g→tons)
    gdf["ghg_pc_tpy"] = gdf["vmt_pc"] * 365 * CO2_GRAMS_PER_MILE / 1e6
    gdf["ghg_pc_tpy"] = gdf["ghg_pc_tpy"].round(4)
    gdf["ghg_pc_quantile"] = gdf["ghg_pc_tpy"].rank(pct=True, na_option="keep").round(4)

    # ── Derived hotspot flags ─────────────────────────────────────────────
    # high_vmt_flag uses vmt_pc_quantile (raw VMT, top 25%)
    gdf["high_vmt_flag"] = gdf["vmt_pc_quantile"] >= HIGH_VMT_QUANTILE
    gdf["high_pollution_flag"] = gdf["pollution_burden_pct"] >= HIGH_POLLUTION_QUANTILE
    gdf["high_vmt_high_pollution_flag"] = gdf["high_vmt_flag"] & gdf["high_pollution_flag"]
    gdf["high_ghg_flag"] = gdf["ghg_pc_quantile"] >= HIGH_VMT_QUANTILE

    # Handle NaN: flags should be False where underlying data is missing
    for flag_col in ["high_vmt_flag", "high_pollution_flag",
                     "high_vmt_high_pollution_flag", "high_ghg_flag"]:
        gdf[flag_col] = gdf[flag_col].fillna(False).astype(bool)

    # ── County and place name ─────────────────────────────────────────────
    # GEOID format: SSCCCTTTTTT (2-digit state + 3-digit county + 6-digit tract)
    # Extract 5-digit state+county FIPS (e.g., "06001" for Alameda County)
    gdf["county"] = gdf["geoid"].str[:5]
    county_fips = _ca_county_fips_map()
    gdf["county"] = gdf["county"].map(county_fips).fillna("Unknown")

    # Place name: not available from these data sources; stub as empty
    gdf["place_name"] = ""

    # ── Urban/rural classification ────────────────────────────────────────
    # Stub: defaults to "unknown". To fill in, join a RUCA or Census
    # urban/rural classification table on geoid.
    # TODO: Join urban_rural lookup table here
    gdf["urban_rural_class"] = "unknown"

    # ── Round numeric fields for cleaner output ──────────────────────────
    for col in ["ces_score", "pollution_burden", "vmt_pc"]:
        if col in gdf.columns:
            gdf[col] = gdf[col].round(2)
    for col in ["ces_percentile", "pollution_burden_pct", "population_char_pct",
                "pm25_pct", "ozone_pct", "diesel_pm_pct", "traffic_density_pct"]:
        if col in gdf.columns:
            gdf[col] = gdf[col].round(1)

    # ── Final column order ────────────────────────────────────────────────
    target_cols = [
        # Identification & geography
        "geoid", "county", "place_name", "population_total", "urban_rural_class",
        "region_id",
        # VMT / GHG
        "vmt_pc", "vmt_index", "vmt_pc_quantile", "vmt_pc_category",
        "vmt_index_quantile", "vmt_index_pctile",
        "ghg_pc_tpy", "ghg_pc_quantile",
        # CalEnviroScreen 4.0
        "ces_score", "ces_percentile",
        "pollution_burden", "pollution_burden_pct", "population_char_pct",
        "pm25_pct", "ozone_pct", "diesel_pm_pct", "traffic_density_pct",
        # DAC / AB 1550
        "dac_flag", "low_income_flag", "dac_low_income_combo",
        # Derived hotspot flags
        "high_vmt_flag", "high_pollution_flag", "high_vmt_high_pollution_flag",
        "high_ghg_flag",
        # Geometry
        "geometry",
    ]
    existing = [c for c in target_cols if c in gdf.columns]
    gdf = gdf[existing].copy()

    print(f"\n  ✓ Unified dataset: {len(gdf)} tracts, {len(existing)} columns")
    print(f"    DAC tracts: {gdf['dac_flag'].sum()}")
    if gdf["vmt_pc"].notna().any():
        print(f"    Mean VMT/capita: {gdf['vmt_pc'].mean():.1f} mi/person/day")
        print(f"    Mean VMT index:  {gdf['vmt_index'].mean():.1f}")
    print(f"    High VMT+Pollution hotspots: {gdf['high_vmt_high_pollution_flag'].sum()}")

    return gdf


def _ca_county_fips_map():
    """Return a dict of 5-digit state+county FIPS → county name for all 58 CA counties."""
    return {
        "06001": "Alameda", "06003": "Alpine", "06005": "Amador",
        "06007": "Butte", "06009": "Calaveras", "06011": "Colusa",
        "06013": "Contra Costa", "06015": "Del Norte", "06017": "El Dorado",
        "06019": "Fresno", "06021": "Glenn", "06023": "Humboldt",
        "06025": "Imperial", "06027": "Inyo", "06029": "Kern",
        "06031": "Kings", "06033": "Lake", "06035": "Lassen",
        "06037": "Los Angeles", "06039": "Madera", "06041": "Marin",
        "06043": "Mariposa", "06045": "Mendocino", "06047": "Merced",
        "06049": "Modoc", "06051": "Mono", "06053": "Monterey",
        "06055": "Napa", "06057": "Nevada", "06059": "Orange",
        "06061": "Placer", "06063": "Plumas", "06065": "Riverside",
        "06067": "Sacramento", "06069": "San Benito",
        "06071": "San Bernardino", "06073": "San Diego",
        "06075": "San Francisco", "06077": "San Joaquin",
        "06079": "San Luis Obispo", "06081": "San Mateo",
        "06083": "Santa Barbara", "06085": "Santa Clara",
        "06087": "Santa Cruz", "06089": "Shasta", "06091": "Sierra",
        "06093": "Siskiyou", "06095": "Solano", "06097": "Sonoma",
        "06099": "Stanislaus", "06101": "Sutter", "06103": "Tehama",
        "06105": "Trinity", "06107": "Tulare", "06109": "Tuolumne",
        "06111": "Ventura", "06113": "Yolo", "06115": "Yuba",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 5: Simplify geometries & export
# ═══════════════════════════════════════════════════════════════════════════

def export_geojson(gdf, simplify=True):
    """Simplify tract geometries and export to GeoJSON."""
    import geopandas as gpd

    print("\n" + "=" * 60)
    print("STEP 5: Simplify & export GeoJSON")
    print("=" * 60)

    if simplify and SIMPLIFY_TOLERANCE_M > 0:
        print(f"  Simplifying geometries (tolerance={SIMPLIFY_TOLERANCE_M}m)...")
        # Project to CA Albers (meters) for simplification
        gdf_proj = gdf.to_crs(epsg=3310)
        gdf_proj["geometry"] = gdf_proj.geometry.simplify(
            tolerance=SIMPLIFY_TOLERANCE_M, preserve_topology=True
        )
        gdf = gdf_proj.to_crs(epsg=4326)

    # Convert boolean columns for clean JSON serialization
    bool_cols = ["dac_flag", "low_income_flag", "high_vmt_flag",
                 "high_pollution_flag", "high_vmt_high_pollution_flag", "high_ghg_flag"]
    for col in bool_cols:
        if col in gdf.columns:
            gdf[col] = gdf[col].astype(bool)

    # Replace NaN/None with None for clean JSON
    gdf = gdf.where(gdf.notna(), other=None)

    gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    size_mb = OUTPUT_GEOJSON.stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved: {OUTPUT_GEOJSON.name} ({size_mb:.1f} MB)")
    print(f"    Tracts: {len(gdf)}")

    return gdf


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 6: Compute and export summary statistics
# ═══════════════════════════════════════════════════════════════════════════

def export_summary_stats(gdf):
    """Compute statewide/urban/rural summary statistics and export to JSON."""
    print("\n" + "=" * 60)
    print("STEP 6: Compute & export summary statistics")
    print("=" * 60)

    def compute_stats(df, label):
        """Compute stats for a subset of tracts."""
        stats = {
            "tract_count": int(len(df)),
        }

        # DAC share
        if "dac_flag" in df.columns:
            stats["share_dac"] = round(df["dac_flag"].mean(), 4)

        # VMT stats
        if "vmt_pc" in df.columns and df["vmt_pc"].notna().any():
            stats["mean_vmt_pc"] = round(df["vmt_pc"].mean(), 1)

            dac_mask = df["dac_flag"] == True
            if dac_mask.any() and df.loc[dac_mask, "vmt_pc"].notna().any():
                stats["mean_vmt_pc_dac"] = round(
                    df.loc[dac_mask, "vmt_pc"].mean(), 1
                )
            non_dac = ~dac_mask
            if non_dac.any() and df.loc[non_dac, "vmt_pc"].notna().any():
                stats["mean_vmt_pc_non_dac"] = round(
                    df.loc[non_dac, "vmt_pc"].mean(), 1
                )

        # GHG stats
        if "ghg_pc_tpy" in df.columns and df["ghg_pc_tpy"].notna().any():
            stats["mean_ghg_pc_tpy"] = round(df["ghg_pc_tpy"].mean(), 3)

        # Hotspot share
        if "high_vmt_high_pollution_flag" in df.columns:
            hotspot_count = df["high_vmt_high_pollution_flag"].sum()
            stats["count_high_vmt_high_pollution"] = int(hotspot_count)
            if "dac_flag" in df.columns:
                dac_hotspot = (df["dac_flag"] & df["high_vmt_high_pollution_flag"]).sum()
                stats["share_dac_high_vmt_high_pollution"] = round(
                    dac_hotspot / len(df), 4
                ) if len(df) > 0 else 0

        # CES stats
        if "ces_percentile" in df.columns and df["ces_percentile"].notna().any():
            stats["mean_ces_percentile"] = round(df["ces_percentile"].mean(), 1)

        if "pollution_burden_pct" in df.columns and df["pollution_burden_pct"].notna().any():
            stats["mean_pollution_burden_pct"] = round(
                df["pollution_burden_pct"].mean(), 1
            )

        return stats

    summary = {}

    # Statewide
    summary["statewide"] = compute_stats(gdf, "statewide")

    # Urban / Rural breakdown
    if "urban_rural_class" in gdf.columns:
        urban_mask = gdf["urban_rural_class"].str.lower().isin(["urban", "suburban"])
        rural_mask = gdf["urban_rural_class"].str.lower() == "rural"
        unknown_mask = ~(urban_mask | rural_mask)

        if urban_mask.any():
            summary["urban"] = compute_stats(gdf[urban_mask], "urban")
        if rural_mask.any():
            summary["rural"] = compute_stats(gdf[rural_mask], "rural")
        if unknown_mask.any():
            summary["unclassified"] = compute_stats(gdf[unknown_mask], "unclassified")
    else:
        summary["urban"] = {"tract_count": 0, "note": "urban_rural_class not yet populated"}
        summary["rural"] = {"tract_count": 0, "note": "urban_rural_class not yet populated"}

    # Metadata
    summary["_metadata"] = {
        "generated_by": "build_tract_dataset.py",
        "sources": [
            "CalEnviroScreen 4.0 (OEHHA)",
            "Priority Populations 4.0 (CARB)",
            "VMT per capita (user-provided tract-level CSV)",
        ],
        "emission_factor_g_co2_per_mile": CO2_GRAMS_PER_MILE,
        "high_vmt_quantile_threshold": HIGH_VMT_QUANTILE,
        "high_pollution_percentile_threshold": HIGH_POLLUTION_QUANTILE,
    }

    OUTPUT_STATS_JSON.write_text(
        json.dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"  ✓ Saved: {OUTPUT_STATS_JSON.name}")
    print(f"\n  Summary (statewide):")
    for k, v in summary["statewide"].items():
        print(f"    {k}: {v}")

    return summary


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Build statewide tract-level dataset for SB 375 / SB 1087 website"
    )
    parser.add_argument("--skip-vmt", action="store_true",
                        help="Skip VMT data loading")
    parser.add_argument("--skip-priority", action="store_true",
                        help="Skip Priority Populations loading")
    parser.add_argument("--no-simplify", action="store_true",
                        help="Export full-resolution geometries")
    args = parser.parse_args()

    print("=" * 60)
    print("build_tract_dataset.py — SB 375 Geospatial Pipeline")
    print("=" * 60)

    # Check dependencies
    try:
        import geopandas  # noqa: F401
        import requests    # noqa: F401
    except ImportError as e:
        print(f"\n✗ Missing dependency: {e}")
        print("  Install with: pip install geopandas requests shapely")
        sys.exit(1)

    # Step 1: CalEnviroScreen 4.0
    ces_gdf = load_ces40()

    # Step 2: Priority Populations
    if args.skip_priority:
        print("\n⏭ Skipping Priority Populations (--skip-priority)")
        pp_df = None
    else:
        pp_df = load_priority_pops(ces_gdf)

    # Step 3: VMT per capita
    if args.skip_vmt:
        print("\n⏭ Skipping VMT data (--skip-vmt)")
        vmt_df = None
    else:
        vmt_df = load_vmt()

    # Step 4: Merge and compute derived fields
    gdf = build_unified_dataset(ces_gdf, pp_df, vmt_df)

    # Step 5: Export GeoJSON
    gdf = export_geojson(gdf, simplify=not args.no_simplify)

    # Step 6: Export summary stats
    summary = export_summary_stats(gdf)

    print("\n" + "=" * 60)
    print("✅ Pipeline complete!")
    print("=" * 60)
    print(f"  GeoJSON: {OUTPUT_GEOJSON}")
    print(f"  Stats:   {OUTPUT_STATS_JSON}")
    print(f"  Tracts:  {len(gdf)}")


if __name__ == "__main__":
    main()
