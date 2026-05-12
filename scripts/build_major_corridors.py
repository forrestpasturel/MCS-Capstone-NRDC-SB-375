#!/usr/bin/env python3
"""
build_major_corridors.py
========================
Extract top-DVMT road segments from the traffic segments GeoPackage and
output a simplified GeoJSON line file for use as a Leaflet overlay.

Input
-----
  data/raw/traffic_segments.gpkg  (layer: segments)
     Columns: geometry, aadt, segment_miles (optional), truck_share (optional)

Output
------
  data/major_corridors.geojson
     Line features for segments in the top 10 % of DVMT, with properties:
       dvmt, relative_class ("high" | "very_high" | "extreme")

Usage
-----
  cd <project root>
  python scripts/build_major_corridors.py
"""

import pathlib
import sys
import numpy as np
import geopandas as gpd
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
SEGMENT_PATH = ROOT / "data" / "raw" / "traffic_segments.gpkg"
SEGMENT_LAYER = "segments"
OUTPUT_PATH = ROOT / "data" / "major_corridors.geojson"

CRS_PROJECTED = "EPSG:3310"          # California Albers (meters)
METERS_PER_MILE = 1_609.344

MAJOR_PCTILE = 90                    # top 10 % of DVMT
SIMPLIFY_TOLERANCE_M = 25            # geometry simplification in meters


def load_segments(path: pathlib.Path, layer: str) -> gpd.GeoDataFrame:
    """Load road segments, ensure aadt exists, compute DVMT."""
    print(f"  Reading segments: {path.name} (layer={layer})")
    gdf = gpd.read_file(path, layer=layer)
    print(f"  ✓ {len(gdf)} segments loaded")

    if "aadt" not in gdf.columns:
        print("  ✖ Segments must have an 'aadt' column"); sys.exit(1)

    gdf["aadt"] = pd.to_numeric(gdf["aadt"], errors="coerce").fillna(0)

    # Project for length calculation
    gdf = gdf.to_crs(CRS_PROJECTED)

    # Use segment_miles if present, otherwise compute from geometry
    if "segment_miles" in gdf.columns:
        gdf["segment_miles"] = pd.to_numeric(gdf["segment_miles"], errors="coerce")
        missing = gdf["segment_miles"].isna()
        if missing.any():
            gdf.loc[missing, "segment_miles"] = (
                gdf.loc[missing].geometry.length / METERS_PER_MILE
            )
    else:
        gdf["segment_miles"] = gdf.geometry.length / METERS_PER_MILE

    # DVMT proxy = AADT × segment length
    gdf["dvmt"] = gdf["aadt"] * gdf["segment_miles"]

    return gdf


def classify_corridors(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Filter to top-DVMT segments and assign a relative_class.

    Thresholds (of the segments that pass the top-10 % cut):
      - bottom third  → "high"
      - middle third  → "very_high"
      - top third     → "extreme"
    """
    threshold = np.percentile(gdf["dvmt"].dropna(), MAJOR_PCTILE)
    major = gdf[gdf["dvmt"] >= threshold].copy()
    print(f"\n  DVMT threshold (p{MAJOR_PCTILE}): {threshold:,.0f}")
    print(f"  Major corridor segments: {len(major)}")

    # Assign class within the major set
    q33 = major["dvmt"].quantile(1 / 3)
    q66 = major["dvmt"].quantile(2 / 3)
    major["relative_class"] = "high"
    major.loc[major["dvmt"] >= q33, "relative_class"] = "very_high"
    major.loc[major["dvmt"] >= q66, "relative_class"] = "extreme"

    counts = major["relative_class"].value_counts()
    for cls in ["high", "very_high", "extreme"]:
        print(f"    {cls}: {counts.get(cls, 0)}")

    return major


def main():
    print("=" * 60)
    print("build_major_corridors.py — DVMT Major Corridor Layer")
    print("=" * 60)

    if not SEGMENT_PATH.exists():
        print(f"\n  ✖ Segment file not found: {SEGMENT_PATH}")
        print(f"    Place your traffic GeoPackage there first.")
        sys.exit(1)

    gdf = load_segments(SEGMENT_PATH, SEGMENT_LAYER)

    # Stats before filtering
    dvmt = gdf["dvmt"]
    print(f"\n  All segments DVMT  min={dvmt.min():,.0f}  mean={dvmt.mean():,.0f}  max={dvmt.max():,.0f}")

    major = classify_corridors(gdf)

    # Simplify geometry
    major = major.copy()
    major["geometry"] = major.geometry.simplify(SIMPLIFY_TOLERANCE_M)

    # Keep only needed columns, round dvmt
    major["dvmt"] = major["dvmt"].round(0).astype(int)
    out = major[["geometry", "dvmt", "relative_class"]]

    # Convert back to WGS 84 for the web
    out = out.to_crs("EPSG:4326")

    out.to_file(OUTPUT_PATH, driver="GeoJSON")
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"\n  ✓ Saved: {OUTPUT_PATH} ({size_kb:.0f} KB)")

    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
