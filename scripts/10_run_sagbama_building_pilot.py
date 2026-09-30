from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

def run(args):
    print("\n$", " ".join(str(x) for x in args), flush=True)
    subprocess.run([str(x) for x in args], check=True)

def main():
    work = REPO_ROOT / "work" / "sagbama_building_pilot"
    out_dir = REPO_ROOT / "checks" / "building_pilot_output"
    if work.exists():
        shutil.rmtree(work)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    work.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    download_sources = REPO_ROOT / "scripts" / "01_download_sources.py"
    prepare_settlements = REPO_ROOT / "scripts" / "04_prepare_settlements.py"
    download_buildings = REPO_ROOT / "scripts" / "05_download_open_buildings.py"
    count_buildings = REPO_ROOT / "scripts" / "05_count_buildings.py"

    # Resolve the exact pilot LGA from source identifiers.
    run([PY, download_sources, "--dataset", "lga_boundaries", "--output", work])
    lgas = gpd.read_file(work / "lga_boundaries.geojson").to_crs(4326)
    pilot = lgas[
        lgas["statename"].astype(str).str.casefold().eq("bayelsa")
        & lgas["lganame"].astype(str).str.casefold().eq("sagbama")
    ].copy()
    if len(pilot) != 1:
        raise ValueError(f"Expected one Bayelsa/Sagbama feature, found {len(pilot)}")
    lga_id = str(pilot.iloc[0]["lgacode"])
    state_id = str(pilot.iloc[0]["statecode"])
    lga_file = work / "sagbama_lga.gpkg"
    pilot.to_file(lga_file, driver="GPKG")
    bbox = tuple(float(x) for x in pilot.total_bounds)
    bbox_args = [str(v) for v in bbox]

    # Build exact-LGA non-overlapping settlement components.
    for dataset in ["settlement_extents", "settlement_names"]:
        run([
            PY, download_sources,
            "--dataset", dataset,
            "--output", work,
            "--bbox", *bbox_args,
        ])
    settlements_file = work / "settlement_components.gpkg"
    run([
        PY, prepare_settlements,
        "--extents", work / "settlement_extents.geojson",
        "--names", work / "settlement_names.geojson",
        "--lga", lga_file,
        "--lga-id", lga_id,
        "--out", settlements_file,
    ])

    # Download Google Open Buildings V3 only for Sagbama using official S2 shards.
    buildings_file = work / "google_open_buildings_sagbama.parquet"
    building_download_summary = work / "open_buildings_download_summary.json"
    run([
        PY, download_buildings,
        "--aoi", lga_file,
        "--out", buildings_file,
        "--summary", building_download_summary,
        "--precision", "90",
    ])

    # Deterministic one-component allocation by Google's source centroid.
    counts_file = work / "settlement_building_counts.csv"
    allocation_summary = work / "building_allocation_summary.json"
    run([
        PY, count_buildings,
        "--buildings", buildings_file,
        "--zones", settlements_file,
        "--zone-id", "settlement_component_id",
        "--out", counts_file,
        "--summary", allocation_summary,
    ])

    download_info = json.loads(building_download_summary.read_text(encoding="utf-8"))
    allocation_info = json.loads(allocation_summary.read_text(encoding="utf-8"))
    counts = pd.read_csv(counts_file)
    settlements = gpd.read_file(settlements_file)

    detected = int(download_info["detected_footprints_output"])
    allocated = int(allocation_info["allocated_to_one_component"])
    outside = int(allocation_info["inside_lga_but_outside_mapped_settlement_components"])
    if allocated + outside != detected:
        raise ValueError(
            f"Building reconciliation failed: allocated {allocated} + outside {outside} != detected {detected}"
        )
    if int(counts["detected_building_count"].sum()) != allocated:
        raise ValueError("Settlement building-count CSV does not sum to allocated building detections.")

    # Compare with GRID3 source-block counts only for full, uncut blocks as a diagnostic.
    full = settlements[
        settlements["building_count_status"].astype(str).eq("source_full_block_count_provisional")
    ].copy()
    source_full_count_sum = pd.to_numeric(
        full.get("source_building_count", pd.Series(dtype=float)),
        errors="coerce"
    ).sum(min_count=1)
    if pd.isna(source_full_count_sum):
        source_full_count_sum = None
    else:
        source_full_count_sum = float(source_full_count_sum)

    summary = {
        "status": "PASS",
        "pilot": {
            "state": "Bayelsa",
            "statecode": state_id,
            "lga": "Sagbama",
            "lgacode": lga_id,
            "bbox_wgs84": bbox,
        },
        "google_open_buildings_v3": {
            "confidence_policy": "Google per-level-4 90% precision threshold applied to level-6 shards",
            "s2_level6_tiles_considered": int(download_info["tiles_considered"]),
            "download_bytes": int(download_info["download_bytes"]),
            "rows_read": int(download_info["rows_read"]),
            "centroids_inside_lga_before_threshold": int(
                download_info["centroids_inside_aoi_before_threshold"]
            ),
            "detected_footprints_after_threshold_and_dedup": detected,
            "exact_duplicates_removed": int(download_info["exact_duplicates_removed"]),
        },
        "allocation": {
            "settlement_component_count": int(len(counts)),
            "detected_footprints_allocated_to_one_settlement_component": allocated,
            "detected_footprints_inside_lga_but_outside_mapped_settlement_components": outside,
            "allocation_reconciliation_passed": True,
            "rule": allocation_info["allocation_method"],
            "boundary_rule": allocation_info["boundary_rule"],
        },
        "grid3_diagnostic": {
            "full_uncut_components": int(len(full)),
            "sum_of_GRID3_source_building_count_for_full_uncut_components": source_full_count_sum,
            "note": (
                "This is only a source diagnostic. GRID3 whole-block counts are not copied "
                "to partial cross-LGA components and are not substituted for Open Buildings counts."
            ),
        },
        "scientific_interpretation": (
            "All counts are counts of detected building footprints. They are not interpreted "
            "as households, occupied dwellings, or residential buildings."
        ),
        "raw_third_party_building_data_committed": False,
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    counts[["settlement_component_id", "detected_building_count"]].to_csv(
        out_dir / "settlement_building_counts_validation.csv", index=False
    )

    print("\n=== SAGBAMA BUILDING PILOT SUMMARY ===")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
