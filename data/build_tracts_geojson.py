"""
build_tracts_geojson.py
=======================
ETL pipeline: downloads CalEnviroScreen 4.0 data, processes tract-level VMT,
pollution burden, and DAC flags, and exports a simplified GeoJSON for the
Leaflet equity map on the SB 375 "Lessons Learned" website.

Two modes:
  Mode A (full pipeline)  — requires geopandas + internet access
      Downloads CES 4.0 shapefile, extracts fields, simplifies geometries,
      exports data/tracts_equity.geojson

  Mode B (fallback)       — no geopandas / no download
      Generates synthetic representative tracts for 4 corridors using
      approximate Census tract boundaries.

Run:
    cd data/
    python build_tracts_geojson.py

Output:
    data/tracts_equity.geojson   ← consumed by Leaflet map via fetch()

Sources:
    - CalEnviroScreen 4.0: https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-40
    - OEHHA CES 4.0 shapefile download (SHP inside ZIP)
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
RAW_DIR = HERE / "raw"
RAW_DIR.mkdir(exist_ok=True)

OUTPUT = HERE / "tracts_equity.geojson"

# CalEnviroScreen 4.0 shapefile URL (official OEHHA download)
CES_ZIP_URL = "https://oehha.ca.gov/media/downloads/calenviroscreen/document/calenviroscreen40shpf2021shp.zip"
CES_ZIP_FILE = RAW_DIR / "calenviroscreen40shpf2021shp.zip"

# Percentile thresholds for "high" classification
HIGH_PCTILE_THRESHOLD = 75  # top 25%
DAC_PCTILE_THRESHOLD = 75   # CalEnviroScreen DAC = top 25% CES score


def download_file(url, dest, label="file"):
    """Download a URL to a local file with progress indication."""
    import requests
    if dest.exists():
        print(f"  {label} already exists: {dest.name} — skipping download")
        return
    print(f"  Downloading {label} ({url[:80]}...)")
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    written = 0
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            f.write(chunk)
            written += len(chunk)
            if total:
                pct = written / total * 100
                print(f"\r    {pct:.0f}% ({written // 1024 // 1024} MB)", end="", flush=True)
    print(f"\n    Saved: {dest.name} ({written // 1024 // 1024} MB)")


def run_mode_a():
    """Full pipeline with GeoPandas — real CalEnviroScreen data."""
    import geopandas as gpd

    # ── 1. Download CES 4.0 shapefile ─────────────────────────────
    print("\n=== Step 1: Obtain CalEnviroScreen 4.0 shapefile ===")
    download_file(CES_ZIP_URL, CES_ZIP_FILE, "CalEnviroScreen 4.0 SHP")

    # ── 2. Load shapefile from ZIP ────────────────────────────────
    print("\n=== Step 2: Load shapefile ===")
    # geopandas can read shapefiles inside ZIPs directly
    shp_path = f"zip://{CES_ZIP_FILE}"
    try:
        gdf = gpd.read_file(shp_path)
    except Exception:
        # Some ZIP structures need the shapefile name specified
        import zipfile
        with zipfile.ZipFile(CES_ZIP_FILE) as zf:
            shp_names = [n for n in zf.namelist() if n.endswith(".shp")]
            if not shp_names:
                print("ERROR: No .shp file found in ZIP. Check download.")
                sys.exit(1)
            shp_name = shp_names[0]
        gdf = gpd.read_file(f"zip://{CES_ZIP_FILE}!{shp_name}")

    print(f"  Loaded {len(gdf)} tracts, CRS: {gdf.crs}")
    print(f"  Columns: {list(gdf.columns)[:20]}...")

    # ── 3. Identify and extract relevant columns ──────────────────
    print("\n=== Step 3: Extract fields ===")

    # CES 4.0 column names vary slightly between releases — search flexibly
    col_map = {}
    cols_lower = {c.lower().replace(" ", "_").replace(".", ""): c for c in gdf.columns}

    # Census Tract ID
    for candidate in ["tract", "census_tract", "geoid", "geoid10", "geoid20", "tractid"]:
        if candidate in cols_lower:
            col_map["tract_id"] = cols_lower[candidate]
            break

    # CES Score & Percentile
    for candidate in ["ciscorep", "ces_40_score", "ces40score", "cisc_perc", "ciscorep"]:
        if candidate in cols_lower:
            col_map["ces_pctile"] = cols_lower[candidate]
            break

    # Pollution Burden percentile
    for candidate in ["pollution_burden_pctl", "pol_burden_pctl", "polburd_p", "pollution_burdenp",
                       "pol_burd", "pollution_burden_pctile", "polburdp"]:
        if candidate in cols_lower:
            col_map["pollution_burden_pctile"] = cols_lower[candidate]
            break

    # Traffic indicator (proxy for VMT)
    for candidate in ["traffic", "trafficp", "traffic_p", "traffp", "traffic_pctl"]:
        if candidate in cols_lower:
            col_map["traffic_pctile_raw"] = cols_lower[candidate]
            break

    # Total population
    for candidate in ["totpop19", "totalpop", "total_pop", "pop2019", "totpop", "population"]:
        if candidate in cols_lower:
            col_map["population"] = cols_lower[candidate]
            break

    print(f"  Column mapping: {col_map}")

    # Check we have minimum required fields
    missing = []
    for needed in ["tract_id"]:
        if needed not in col_map:
            missing.append(needed)
    if missing:
        print(f"\n  WARNING: Could not identify columns: {missing}")
        print(f"  Available columns: {list(gdf.columns)}")
        print("  Falling back to Mode B (synthetic tracts).")
        return run_mode_b()

    # ── 4. Build output dataframe ─────────────────────────────────
    print("\n=== Step 4: Compute derived fields ===")

    out = gdf[["geometry"]].copy()
    out["tract_id"] = gdf[col_map["tract_id"]].astype(str)

    # Pollution burden percentile
    if "pollution_burden_pctile" in col_map:
        out["pollution_burden_pctile"] = (
            gdf[col_map["pollution_burden_pctile"]]
            .apply(lambda x: round(float(x), 1) if x is not None and str(x).strip() != "" else None)
        )
    else:
        out["pollution_burden_pctile"] = None

    # Traffic / VMT proxy
    if "traffic_pctile_raw" in col_map:
        traffic_raw = gdf[col_map["traffic_pctile_raw"]].apply(
            lambda x: float(x) if x is not None and str(x).strip() != "" else None
        )
        # Compute VMT percentile from traffic density
        out["vmt_pctile"] = traffic_raw.rank(pct=True, na_option="keep").apply(
            lambda x: round(x * 100, 1) if x is not None else None
        )
        # VMT index: normalize to statewide mean = 100
        mean_traffic = traffic_raw.mean()
        if mean_traffic and mean_traffic > 0:
            out["vmt_index"] = traffic_raw.apply(
                lambda x: round(x / mean_traffic * 100, 1) if x is not None else None
            )
        else:
            out["vmt_index"] = None
    else:
        out["vmt_pctile"] = None
        out["vmt_index"] = None

    # CES percentile (for DAC flag)
    if "ces_pctile" in col_map:
        ces_p = gdf[col_map["ces_pctile"]].apply(
            lambda x: float(x) if x is not None and str(x).strip() != "" else None
        )
        out["dac_flag"] = ces_p.apply(
            lambda x: bool(x >= DAC_PCTILE_THRESHOLD) if x is not None else False
        )
    else:
        out["dac_flag"] = False

    # Derived flags
    out["high_burden_flag"] = (
        (out["vmt_pctile"].fillna(0) >= HIGH_PCTILE_THRESHOLD)
        & (out["pollution_burden_pctile"].fillna(0) >= HIGH_PCTILE_THRESHOLD)
        & (out["dac_flag"] == True)
    )

    # Drop tracts with no geometry or no data
    out = out.dropna(subset=["geometry"])
    out = out[out.geometry.is_valid]

    # ── 5. Simplify geometries ────────────────────────────────────
    print("\n=== Step 5: Simplify geometries ===")
    # Reproject to a meter-based CRS for simplification, then back to WGS84
    out_proj = out.to_crs(epsg=3310)  # California Albers
    out_proj["geometry"] = out_proj.geometry.simplify(tolerance=100)  # 100m tolerance
    out = out_proj.to_crs(epsg=4326)

    # Convert boolean columns to Python bool for JSON serialization
    out["dac_flag"] = out["dac_flag"].astype(bool)
    out["high_burden_flag"] = out["high_burden_flag"].astype(bool)

    # ── 6. Export GeoJSON ─────────────────────────────────────────
    print("\n=== Step 6: Export GeoJSON ===")
    keep_cols = ["tract_id", "vmt_index", "vmt_pctile",
                 "pollution_burden_pctile", "dac_flag", "high_burden_flag", "geometry"]
    out = out[[c for c in keep_cols if c in out.columns]]

    out.to_file(OUTPUT, driver="GeoJSON")
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"  Saved: {OUTPUT} ({size_mb:.1f} MB)")
    print(f"  Tracts: {len(out)}")
    print(f"  High burden (DAC + high VMT + high pollution): {out['high_burden_flag'].sum()}")
    print(f"  DAC tracts: {out['dac_flag'].sum()}")

    return True


def run_mode_b():
    """Fallback: generate synthetic representative tracts for 4 corridors."""
    print("\n=== Mode B: Generating synthetic representative tracts ===")
    print("  (Real CalEnviroScreen data not available — using corridor approximations)")

    # Approximate tract-like polygons for each corridor region
    # Each "tract" is a small polygon representing a cluster of real tracts
    corridors = {
        "I-80 (Yolo / Sacramento)": {
            "center": [-121.55, 38.56],
            "tracts": [
                {"offset": [-0.06, -0.02], "vmt_index": 82, "vmt_pctile": 68, "pb": 72, "dac": True, "hb": False},
                {"offset": [-0.02, -0.02], "vmt_index": 91, "vmt_pctile": 77, "pb": 78, "dac": True, "hb": True},
                {"offset": [0.02, -0.02],  "vmt_index": 75, "vmt_pctile": 62, "pb": 69, "dac": True, "hb": False},
                {"offset": [-0.06, 0.02],  "vmt_index": 68, "vmt_pctile": 55, "pb": 65, "dac": False, "hb": False},
                {"offset": [-0.02, 0.02],  "vmt_index": 88, "vmt_pctile": 74, "pb": 75, "dac": True, "hb": False},
                {"offset": [0.02, 0.02],   "vmt_index": 95, "vmt_pctile": 80, "pb": 82, "dac": True, "hb": True},
                {"offset": [0.06, -0.02],  "vmt_index": 72, "vmt_pctile": 58, "pb": 60, "dac": False, "hb": False},
                {"offset": [0.06, 0.02],   "vmt_index": 85, "vmt_pctile": 71, "pb": 70, "dac": True, "hb": False},
            ]
        },
        "SR-99 (Central Valley)": {
            "center": [-119.75, 36.71],
            "tracts": [
                {"offset": [-0.05, -0.04], "vmt_index": 92, "vmt_pctile": 78, "pb": 84, "dac": True, "hb": True},
                {"offset": [0.01, -0.04],  "vmt_index": 86, "vmt_pctile": 73, "pb": 80, "dac": True, "hb": False},
                {"offset": [-0.05, 0.0],   "vmt_index": 98, "vmt_pctile": 83, "pb": 88, "dac": True, "hb": True},
                {"offset": [0.01, 0.0],    "vmt_index": 80, "vmt_pctile": 67, "pb": 76, "dac": True, "hb": False},
                {"offset": [-0.05, 0.04],  "vmt_index": 90, "vmt_pctile": 76, "pb": 82, "dac": True, "hb": True},
                {"offset": [0.01, 0.04],   "vmt_index": 75, "vmt_pctile": 61, "pb": 72, "dac": True, "hb": False},
                {"offset": [-0.02, -0.08], "vmt_index": 70, "vmt_pctile": 55, "pb": 65, "dac": False, "hb": False},
                {"offset": [-0.02, 0.08],  "vmt_index": 78, "vmt_pctile": 64, "pb": 70, "dac": True, "hb": False},
            ]
        },
        "I-105 (Los Angeles)": {
            "center": [-118.28, 33.94],
            "tracts": [
                {"offset": [-0.06, -0.01], "vmt_index": 95, "vmt_pctile": 81, "pb": 90, "dac": True, "hb": True},
                {"offset": [-0.02, -0.01], "vmt_index": 100,"vmt_pctile": 85, "pb": 92, "dac": True, "hb": True},
                {"offset": [0.02, -0.01],  "vmt_index": 88, "vmt_pctile": 75, "pb": 86, "dac": True, "hb": True},
                {"offset": [0.06, -0.01],  "vmt_index": 82, "vmt_pctile": 69, "pb": 80, "dac": True, "hb": False},
                {"offset": [-0.06, 0.01],  "vmt_index": 78, "vmt_pctile": 64, "pb": 75, "dac": True, "hb": False},
                {"offset": [-0.02, 0.01],  "vmt_index": 92, "vmt_pctile": 79, "pb": 88, "dac": True, "hb": True},
                {"offset": [0.02, 0.01],   "vmt_index": 70, "vmt_pctile": 56, "pb": 68, "dac": False, "hb": False},
                {"offset": [0.06, 0.01],   "vmt_index": 65, "vmt_pctile": 50, "pb": 60, "dac": False, "hb": False},
            ]
        },
        "I-710 (Long Beach)": {
            "center": [-118.19, 33.82],
            "tracts": [
                {"offset": [-0.03, -0.03], "vmt_index": 105,"vmt_pctile": 88, "pb": 97, "dac": True, "hb": True},
                {"offset": [0.01, -0.03],  "vmt_index": 110,"vmt_pctile": 92, "pb": 95, "dac": True, "hb": True},
                {"offset": [-0.03, -0.01], "vmt_index": 100,"vmt_pctile": 85, "pb": 93, "dac": True, "hb": True},
                {"offset": [0.01, -0.01],  "vmt_index": 98, "vmt_pctile": 83, "pb": 90, "dac": True, "hb": True},
                {"offset": [-0.03, 0.01],  "vmt_index": 92, "vmt_pctile": 78, "pb": 88, "dac": True, "hb": True},
                {"offset": [0.01, 0.01],   "vmt_index": 88, "vmt_pctile": 75, "pb": 85, "dac": True, "hb": True},
                {"offset": [-0.03, 0.03],  "vmt_index": 80, "vmt_pctile": 67, "pb": 78, "dac": True, "hb": False},
                {"offset": [0.01, 0.03],   "vmt_index": 75, "vmt_pctile": 61, "pb": 72, "dac": False, "hb": False},
                {"offset": [-0.01, -0.05], "vmt_index": 115,"vmt_pctile": 95, "pb": 98, "dac": True, "hb": True},
                {"offset": [0.03, 0.0],    "vmt_index": 85, "vmt_pctile": 72, "pb": 82, "dac": True, "hb": False},
            ]
        },
    }

    features = []
    tract_counter = 0

    for corridor_name, corridor in corridors.items():
        cx, cy = corridor["center"]
        for t in corridor["tracts"]:
            tract_counter += 1
            ox, oy = t["offset"]
            # Create a small polygon (approx 1km × 1km tract-like shape)
            dx, dy = 0.015, 0.012
            x, y = cx + ox, cy + oy
            coords = [
                [round(x - dx, 6), round(y - dy, 6)],
                [round(x + dx, 6), round(y - dy, 6)],
                [round(x + dx, 6), round(y + dy, 6)],
                [round(x - dx, 6), round(y + dy, 6)],
                [round(x - dx, 6), round(y - dy, 6)],
            ]
            features.append({
                "type": "Feature",
                "properties": {
                    "tract_id": f"06_synth_{tract_counter:04d}",
                    "corridor": corridor_name,
                    "vmt_index": t["vmt_index"],
                    "vmt_pctile": t["vmt_pctile"],
                    "pollution_burden_pctile": t["pb"],
                    "dac_flag": t["dac"],
                    "high_burden_flag": t["hb"],
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords],
                },
            })

    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "source": "Synthetic representative tracts — replace with CalEnviroScreen 4.0 exports",
            "corridors": list(corridors.keys()),
            "note": "Run with geopandas installed + internet access for real CES 4.0 tract polygons",
        },
        "features": features,
    }

    OUTPUT.write_text(json.dumps(geojson, indent=2), encoding="utf-8")
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"  Saved: {OUTPUT} ({size_kb:.1f} KB)")
    print(f"  Tracts: {len(features)}")
    hb_count = sum(1 for f in features if f["properties"]["high_burden_flag"])
    print(f"  High burden: {hb_count}")

    return True


def main():
    print("=" * 60)
    print("build_tracts_geojson.py — CalEnviroScreen ETL Pipeline")
    print("=" * 60)

    # Try Mode A first (full pipeline with geopandas)
    try:
        import geopandas  # noqa: F401
        has_geopandas = True
    except ImportError:
        has_geopandas = False

    if has_geopandas:
        print("\n✓ GeoPandas available — attempting Mode A (full pipeline)")
        try:
            success = run_mode_a()
            if success:
                print("\n✅ Mode A complete — real CalEnviroScreen tract polygons exported")
                return
        except Exception as e:
            print(f"\n⚠ Mode A failed: {e}")
            print("  Falling back to Mode B (synthetic tracts)")

    else:
        print("\n⚠ GeoPandas not installed — using Mode B (synthetic tracts)")
        print("  To use real data:  pip install geopandas shapely requests")

    run_mode_b()
    print("\n✅ Mode B complete — synthetic representative tracts exported")
    print("  ⚠ Replace with real CalEnviroScreen data when available")


if __name__ == "__main__":
    main()
