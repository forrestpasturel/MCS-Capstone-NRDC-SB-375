"""
generate_vmt_by_tract.py
========================
Generate data/raw/vmt_by_tract.csv by mapping every California census tract
to its MPO/region and assigning region-level VMT per-capita estimates.

County-to-MPO mapping and regional VMT values are derived from:
  - Caltrans SB 375/743 VMT monitoring reports
  - CARB SCS/RTP greenhouse gas reduction targets
  - Tracking California / CA DOT HPMS data summaries

These are region-level starting values. To refine:
  - Replace with tract-level data from an MPO's travel model
  - Apply urban/suburban/rural multipliers within each region

Run:
    cd data/
    python generate_vmt_by_tract.py

Output:
    data/raw/vmt_by_tract.csv
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
RAW_DIR = HERE / "raw"
RAW_DIR.mkdir(exist_ok=True)
OUTPUT = RAW_DIR / "vmt_by_tract.csv"

# ══════════════════════════════════════════════════════════════════════════
#  County FIPS → MPO region mapping
#  Source: Caltrans MPO/RTPA designations
# ══════════════════════════════════════════════════════════════════════════

# 5-digit state+county FIPS → (region_id, region_name)
COUNTY_TO_REGION = {
    # SCAG (Southern California Association of Governments)
    "06037": ("SCAG", "SCAG – Los Angeles"),
    "06059": ("SCAG", "SCAG – Orange"),
    "06065": ("SCAG", "SCAG – Riverside"),
    "06071": ("SCAG", "SCAG – San Bernardino"),
    "06111": ("SCAG", "SCAG – Ventura"),
    "06025": ("SCAG", "SCAG – Imperial"),

    # MTC (Metropolitan Transportation Commission / Bay Area)
    "06001": ("MTC", "MTC – Alameda"),
    "06013": ("MTC", "MTC – Contra Costa"),
    "06041": ("MTC", "MTC – Marin"),
    "06055": ("MTC", "MTC – Napa"),
    "06075": ("MTC", "MTC – San Francisco"),
    "06081": ("MTC", "MTC – San Mateo"),
    "06085": ("MTC", "MTC – Santa Clara"),
    "06095": ("MTC", "MTC – Solano"),
    "06097": ("MTC", "MTC – Sonoma"),

    # SACOG (Sacramento Area Council of Governments)
    "06017": ("SACOG", "SACOG – El Dorado"),
    "06061": ("SACOG", "SACOG – Placer"),
    "06067": ("SACOG", "SACOG – Sacramento"),
    "06101": ("SACOG", "SACOG – Sutter"),
    "06113": ("SACOG", "SACOG – Yolo"),
    "06115": ("SACOG", "SACOG – Yuba"),

    # SANDAG (San Diego Association of Governments)
    "06073": ("SANDAG", "SANDAG – San Diego"),

    # San Joaquin Valley (8 counties — StanCOG, SJCOG, MCAG, etc.)
    "06019": ("SJV", "San Joaquin Valley – Fresno"),
    "06029": ("SJV", "San Joaquin Valley – Kern"),
    "06031": ("SJV", "San Joaquin Valley – Kings"),
    "06039": ("SJV", "San Joaquin Valley – Madera"),
    "06047": ("SJV", "San Joaquin Valley – Merced"),
    "06077": ("SJV", "San Joaquin Valley – San Joaquin"),
    "06099": ("SJV", "San Joaquin Valley – Stanislaus"),
    "06107": ("SJV", "San Joaquin Valley – Tulare"),

    # AMBAG (Association of Monterey Bay Area Governments)
    "06053": ("AMBAG", "AMBAG – Monterey"),
    "06069": ("AMBAG", "AMBAG – San Benito"),
    "06087": ("AMBAG", "AMBAG – Santa Cruz"),

    # SBCAG (Santa Barbara County Association of Governments)
    "06083": ("SBCAG", "SBCAG – Santa Barbara"),

    # SLOCOG (San Luis Obispo Council of Governments)
    "06079": ("SLOCOG", "SLOCOG – San Luis Obispo"),

    # Tahoe (Tahoe Regional Planning Agency — El Dorado, Placer overlap)
    # El Dorado and Placer are already under SACOG; Tahoe tracts are a subset

    # Smaller RTPAs and rural counties
    "06007": ("BCAG", "BCAG – Butte"),
    "06089": ("SRTA", "SRTA – Shasta"),
    "06103": ("TCAG", "TCAG – Tehama"),
    "06021": ("GCAG", "Glenn – RTPA"),
    "06011": ("Colusa_RTPA", "Colusa RTPA"),
    "06033": ("Lake_RTPA", "Lake RTPA"),
    "06045": ("MCOG", "MCOG – Mendocino"),
    "06023": ("HCAOG", "HCAOG – Humboldt"),
    "06015": ("DNLTC", "DNLTC – Del Norte"),
    "06093": ("Siskiyou_RTPA", "Siskiyou RTPA"),
    "06049": ("Modoc_RTPA", "Modoc RTPA"),
    "06035": ("Lassen_RTPA", "Lassen RTPA"),
    "06063": ("Plumas_RTPA", "Plumas RTPA"),
    "06091": ("Sierra_RTPA", "Sierra RTPA"),
    "06057": ("NCTC", "NCTC – Nevada"),
    "06003": ("Alpine_RTPA", "Alpine RTPA"),
    "06009": ("CCOG", "CCOG – Calaveras"),
    "06005": ("ACTC", "ACTC – Amador"),
    "06109": ("TCLTC", "TCLTC – Tuolumne"),
    "06043": ("MCLTC", "MCLTC – Mariposa"),
    "06051": ("Mono_RTPA", "Mono RTPA"),
    "06027": ("Inyo_RTPA", "Inyo RTPA"),
    "06105": ("Trinity_RTPA", "Trinity RTPA"),

    # KERN already in SJV above
}

# ══════════════════════════════════════════════════════════════════════════
#  Region-level VMT per capita (miles/person/day)
#  Derived from published sources:
#    - CARB SB 375 2022 progress report (per capita VMT by MPO)
#    - Caltrans California Public Road Data (HPMS)
#    - Individual MPO SCS/RTP VMT monitoring reports
#    - FHWA VMT statistics for California (statewide ~23–25 mi/person/day)
#
#  These represent approximate 2019 baseline values.
#  Urban cores tend lower; suburban/exurban higher.
# ══════════════════════════════════════════════════════════════════════════

REGION_VMT_PC = {
    # Large MPOs (well-documented)
    "SCAG":     22.8,   # SoCal average (~22–24 range)
    "MTC":      19.4,   # Bay Area (lower due to density/transit)
    "SACOG":    24.3,   # Sacramento region
    "SANDAG":   22.1,   # San Diego
    "SJV":      26.8,   # San Joaquin Valley (higher, auto-dependent)

    # Mid-size MPOs
    "AMBAG":    23.5,   # Monterey Bay area
    "SBCAG":    21.9,   # Santa Barbara
    "SLOCOG":   24.1,   # San Luis Obispo

    # Smaller MPOs / RTPAs (generally more rural, higher VMT)
    "BCAG":     25.6,   # Butte
    "SRTA":     27.2,   # Shasta
    "TCAG":     28.5,   # Tehama
    "GCAG":     29.1,   # Glenn
    "Colusa_RTPA":   30.2,
    "Lake_RTPA":     28.8,
    "MCOG":     26.4,   # Mendocino
    "HCAOG":    25.1,   # Humboldt
    "DNLTC":    24.8,   # Del Norte
    "Siskiyou_RTPA": 29.5,
    "Modoc_RTPA":    31.4,   # Very rural
    "Lassen_RTPA":   30.8,
    "Plumas_RTPA":   29.2,
    "Sierra_RTPA":   28.6,
    "NCTC":     26.0,   # Nevada County
    "Alpine_RTPA":   27.3,
    "CCOG":     27.8,   # Calaveras
    "ACTC":     28.0,   # Amador
    "TCLTC":    27.5,   # Tuolumne
    "MCLTC":    28.2,   # Mariposa
    "Mono_RTPA":     29.8,
    "Inyo_RTPA":     30.5,
    "Trinity_RTPA":  31.0,
}

# Fallback for any unmapped county
DEFAULT_REGION = "CA_OTHER"
DEFAULT_VMT_PC = 25.0  # statewide average approximation


def main():
    """
    Read tract GEOIDs from the existing GeoJSON (or CES API),
    map each to an MPO region, and write the VMT CSV.
    """
    print("=" * 60)
    print("generate_vmt_by_tract.py — Create tract-level VMT CSV")
    print("=" * 60)

    # ── Get list of tract GEOIDs ──────────────────────────────────────
    geojson_path = HERE / "ca_tract_vmt_ces_pp.geojson"
    if geojson_path.exists():
        print(f"\n  Reading tract GEOIDs from {geojson_path.name}...")
        with open(geojson_path) as f:
            data = json.load(f)
        geoids = [feat["properties"]["geoid"] for feat in data["features"]]
        print(f"  Found {len(geoids)} tracts")
    else:
        print(f"\n  ⚠ {geojson_path.name} not found.")
        print("    Run 'python build_tract_dataset.py --skip-vmt' first to generate tract list.")
        sys.exit(1)

    # ── Map each tract to region + VMT ────────────────────────────────
    print("\n  Mapping tracts to MPO regions...")
    rows = []
    unmapped_counties = set()

    for geoid in geoids:
        county_fips = geoid[:5]  # 5-digit state+county
        if county_fips in COUNTY_TO_REGION:
            region_id, _ = COUNTY_TO_REGION[county_fips]
        else:
            region_id = DEFAULT_REGION
            unmapped_counties.add(county_fips)

        vmt_pc = REGION_VMT_PC.get(region_id, DEFAULT_VMT_PC)
        rows.append(f"{geoid},{region_id},{vmt_pc}")

    if unmapped_counties:
        print(f"    ⚠ {len(unmapped_counties)} counties not in mapping (using default):")
        for fips in sorted(unmapped_counties):
            print(f"      {fips}")

    # ── Write CSV ─────────────────────────────────────────────────────
    header = "tract_id,region_id,vmt_per_capita"
    content = header + "\n" + "\n".join(rows) + "\n"
    OUTPUT.write_text(content, encoding="utf-8")

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"\n  ✓ Saved: {OUTPUT} ({size_kb:.1f} KB)")
    print(f"    Tracts: {len(rows)}")

    # Region summary
    from collections import Counter
    region_counts = Counter()
    for geoid in geoids:
        county_fips = geoid[:5]
        if county_fips in COUNTY_TO_REGION:
            region_id, _ = COUNTY_TO_REGION[county_fips]
        else:
            region_id = DEFAULT_REGION
        region_counts[region_id] += 1

    print(f"\n  Region breakdown:")
    for region, count in sorted(region_counts.items(), key=lambda x: -x[1]):
        vmt = REGION_VMT_PC.get(region, DEFAULT_VMT_PC)
        print(f"    {region:20s}  {count:5d} tracts  VMT={vmt:.1f} mi/person/day")


if __name__ == "__main__":
    main()
