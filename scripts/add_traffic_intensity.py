#!/usr/bin/env python3
"""
add_traffic_intensity.py
========================
Augment the tract-level GeoJSON with a corridor-sensitive traffic/freight
intensity index computed from road-segment AADT data.

Inputs
------
  data/ca_tract_vmt_ces_pp.geojson          – tract polygons (from build_tract_dataset.py)
  data/raw/traffic_segments.gpkg (layer=segments) – road segments with:
      geometry  – LineString/MultiLineString (WGS 84 or similar)
      aadt      – average annual daily traffic (all vehicles)
      truck_share – fraction of trucks (0–1, optional)
      segment_miles – segment length in miles (optional; computed from geometry if missing)

Output
------
  data/ca_tract_vmt_ces_pp_with_traffic.geojson

Usage
-----
  cd <project root>
  python scripts/add_traffic_intensity.py
"""

import pathlib
import sys
import numpy as np
import geopandas as gpd
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACT_PATH = ROOT / "data" / "ca_tract_vmt_ces_pp.geojson"
SEGMENT_PATH = ROOT / "data" / "raw" / "traffic_segments.gpkg"
SEGMENT_LAYER = "segments"
OUTPUT_PATH = ROOT / "data" / "ca_tract_vmt_ces_pp_with_traffic.geojson"

# California Albers (meters) for area / length calculations
CRS_PROJECTED = "EPSG:3310"

# Conversion: meters → miles
METERS_PER_MILE = 1_609.344


# ── Data loading ──────────────────────────────────────────────────────
def load_tracts(path: pathlib.Path) -> gpd.GeoDataFrame:
    """Load tract polygons and ensure a geoid column exists."""
    print(f"  Reading tracts: {path.name}")
    gdf = gpd.read_file(path)
    if "geoid" not in gdf.columns:
        raise KeyError("Tract GeoJSON must have a 'geoid' column")
    print(f"  ✓ {len(gdf)} tracts loaded")
    return gdf


def load_segments(path: pathlib.Path, layer: str) -> gpd.GeoDataFrame:
    """Load road segments and prepare columns."""
    print(f"  Reading segments: {path.name} (layer={layer})")
    gdf = gpd.read_file(path, layer=layer)
    print(f"  ✓ {len(gdf)} raw segments loaded")

    # Ensure required column
    if "aadt" not in gdf.columns:
        raise KeyError("Segments must have an 'aadt' column")

    # Coerce types
    gdf["aadt"] = pd.to_numeric(gdf["aadt"], errors="coerce").fillna(0)

    # truck_share is optional
    has_truck = "truck_share" in gdf.columns
    if has_truck:
        gdf["truck_share"] = pd.to_numeric(gdf["truck_share"], errors="coerce").fillna(0)
        print(f"    truck_share column found ({(gdf['truck_share'] > 0).sum()} segments with data)")
    else:
        print("    No truck_share column — truck indices will be skipped")

    # segment_miles: use if present, else will be computed after projection
    has_miles = "segment_miles" in gdf.columns
    if has_miles:
        gdf["segment_miles"] = pd.to_numeric(gdf["segment_miles"], errors="coerce")
        print(f"    segment_miles column found")
    else:
        print("    No segment_miles column — will compute from geometry")

    return gdf


# ── Core computation ──────────────────────────────────────────────────
def compute_traffic_intensity(
    tracts: gpd.GeoDataFrame,
    segments: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """
    Intersect road segments with tract polygons, compute traffic VMT
    (AADT × miles within each tract), then derive indices.

    Returns a DataFrame indexed by geoid with new columns.
    """
    print("\n  Projecting to EPSG:3310 …")
    tracts_proj = tracts[["geoid", "geometry"]].to_crs(CRS_PROJECTED)
    segs_proj = segments.to_crs(CRS_PROJECTED)

    has_truck = "truck_share" in segs_proj.columns
    has_miles_col = "segment_miles" in segs_proj.columns

    # ── Spatial intersection ──────────────────────────────────────────
    print("  Intersecting segments with tract polygons …")
    # gpd.overlay with 'intersection' keeps only the portions of segments
    # that fall within each tract.
    pieces = gpd.overlay(
        segs_proj[["aadt"] + (["truck_share"] if has_truck else []) + (["segment_miles"] if has_miles_col else []) + ["geometry"]],
        tracts_proj,
        how="intersection",
        keep_geom_type=False,
    )
    print(f"    {len(pieces)} segment–tract intersection pieces")

    # ── Compute length in miles for each intersection piece ───────────
    # Always use the intersected geometry length (accurate to what's inside)
    pieces["piece_miles"] = pieces.geometry.length / METERS_PER_MILE

    # ── Traffic VMT per piece ─────────────────────────────────────────
    pieces["traffic_vmt"] = pieces["aadt"] * pieces["piece_miles"]

    if has_truck:
        pieces["truck_vmt"] = pieces["aadt"] * pieces["truck_share"] * pieces["piece_miles"]

    # ── Aggregate to tract ────────────────────────────────────────────
    agg_cols = {"traffic_vmt": "sum"}
    if has_truck:
        agg_cols["truck_vmt"] = "sum"

    tract_traffic = pieces.groupby("geoid").agg(agg_cols).reset_index()

    # ── Compute indices (ratio to mean × 100) ─────────────────────────
    mean_traffic = tract_traffic["traffic_vmt"].mean()
    tract_traffic["traffic_intensity_index"] = np.round(
        tract_traffic["traffic_vmt"] / mean_traffic * 100, 1
    )

    # Percentile (rank ÷ count)
    tract_traffic["traffic_intensity_pctile"] = np.round(
        tract_traffic["traffic_vmt"].rank(pct=True) * 100, 1
    )

    if has_truck:
        mean_truck = tract_traffic["truck_vmt"].mean()
        if mean_truck > 0:
            tract_traffic["truck_intensity_index"] = np.round(
                tract_traffic["truck_vmt"] / mean_truck * 100, 1
            )
            tract_traffic["truck_intensity_pctile"] = np.round(
                tract_traffic["truck_vmt"].rank(pct=True) * 100, 1
            )
        else:
            tract_traffic["truck_intensity_index"] = np.nan
            tract_traffic["truck_intensity_pctile"] = np.nan

    # Drop raw VMT columns (keep indices only)
    out_cols = ["geoid", "traffic_intensity_index", "traffic_intensity_pctile"]
    if has_truck:
        out_cols += ["truck_intensity_index", "truck_intensity_pctile"]
    result = tract_traffic[out_cols]

    # ── Print summary ─────────────────────────────────────────────────
    n_with = len(result)
    print(f"\n  Tracts with traffic data: {n_with} / {len(tracts)}")
    ti = result["traffic_intensity_index"]
    print(f"  traffic_intensity_index  min={ti.min():.1f}  mean={ti.mean():.1f}  max={ti.max():.1f}")
    if has_truck and "truck_intensity_index" in result.columns:
        tk = result["truck_intensity_index"].dropna()
        if len(tk) > 0:
            print(f"  truck_intensity_index    min={tk.min():.1f}  mean={tk.mean():.1f}  max={tk.max():.1f}")

    return result


# ── Main ──────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("add_traffic_intensity.py — Corridor Traffic Index")
    print("=" * 60)

    # ── Load data ─────────────────────────────────────────────────────
    if not TRACT_PATH.exists():
        print(f"\n  ✖ Tract file not found: {TRACT_PATH}")
        print("    Run  cd data && python build_tract_dataset.py  first.")
        sys.exit(1)

    if not SEGMENT_PATH.exists():
        print(f"\n  ✖ Segment file not found: {SEGMENT_PATH}")
        print(f"    Please place your traffic segment GeoPackage at:")
        print(f"    {SEGMENT_PATH}")
        print(f"    It should contain a layer '{SEGMENT_LAYER}' with columns:")
        print(f"      geometry, aadt, truck_share (opt), segment_miles (opt)")
        sys.exit(1)

    tracts = load_tracts(TRACT_PATH)
    segments = load_segments(SEGMENT_PATH, SEGMENT_LAYER)

    # ── Compute ───────────────────────────────────────────────────────
    traffic_df = compute_traffic_intensity(tracts, segments)

    # ── Merge back into tracts and export ─────────────────────────────
    print(f"\n  Merging traffic indices into tract dataset …")
    merged = tracts.merge(traffic_df, on="geoid", how="left")

    # Fill tracts with no nearby roads
    merged["traffic_intensity_index"] = merged["traffic_intensity_index"].fillna(0)
    merged["traffic_intensity_pctile"] = merged["traffic_intensity_pctile"].fillna(0)
    if "truck_intensity_index" in merged.columns:
        # Leave truck as NaN where truly no truck data
        pass

    print(f"  ✓ Merged: {len(merged)} tracts, {len(merged.columns)} columns")
    print(f"    Tracts with traffic_intensity > 0: {(merged['traffic_intensity_index'] > 0).sum()}")

    # ── Write output ──────────────────────────────────────────────────
    merged.to_file(OUTPUT_PATH, driver="GeoJSON")
    size_mb = OUTPUT_PATH.stat().st_size / 1_048_576
    print(f"\n  ✓ Saved: {OUTPUT_PATH} ({size_mb:.1f} MB)")

    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
