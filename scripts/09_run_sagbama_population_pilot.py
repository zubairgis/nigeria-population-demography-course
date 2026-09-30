from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

def run(args):
    print("\n$", " ".join(str(x) for x in args), flush=True)
    subprocess.run([str(x) for x in args], check=True)

def main():
    work = REPO_ROOT / "work" / "sagbama_population_pilot"
    out_dir = REPO_ROOT / "checks" / "population_pilot_output"
    if work.exists():
        shutil.rmtree(work)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    work.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    download_script = REPO_ROOT / "scripts" / "01_download_sources.py"
    population_script = REPO_ROOT / "scripts" / "03_prepare_population.py"
    settlement_script = REPO_ROOT / "scripts" / "04_prepare_settlements.py"
    health_script = REPO_ROOT / "scripts" / "06_prepare_health_facilities.py"

    # 1. Administrative boundary and stable pilot identifiers.
    run([PY, download_script, "--dataset", "lga_boundaries", "--output", work])
    lgas = gpd.read_file(work / "lga_boundaries.geojson").to_crs(4326)
    pilot = lgas[
        lgas["statename"].astype(str).str.casefold().eq("bayelsa")
        & lgas["lganame"].astype(str).str.casefold().eq("sagbama")
    ].copy()
    if len(pilot) != 1:
        raise ValueError(f"Expected one Bayelsa/Sagbama feature, found {len(pilot)}")
    if not bool(pilot.geometry.iloc[0].is_valid):
        raise ValueError("Sagbama geometry is invalid.")

    lga_id = str(pilot.iloc[0]["lgacode"])
    state_id = str(pilot.iloc[0]["statecode"])
    lga_file = work / "sagbama_lga.gpkg"
    pilot.to_file(lga_file, driver="GPKG")
    bbox = tuple(float(x) for x in pilot.total_bounds)
    bbox_args = [str(v) for v in bbox]

    # 2. Small real pilot vectors; bbox first, then exact-LGA processing.
    for dataset in ["settlement_extents", "settlement_names", "health_v2"]:
        run([
            PY, download_script,
            "--dataset", dataset,
            "--output", work,
            "--bbox", *bbox_args
        ])

    settlements_file = work / "settlement_components.gpkg"
    run([
        PY, settlement_script,
        "--extents", work / "settlement_extents.geojson",
        "--names", work / "settlement_names.geojson",
        "--lga", lga_file,
        "--lga-id", lga_id,
        "--out", settlements_file,
    ])

    health_file = work / "health_facilities_sagbama.gpkg"
    run([
        PY, health_script,
        "--facilities", work / "health_v2.geojson",
        "--lga", lga_file,
        "--out", health_file,
    ])

    # 3. Download exactly six compatible WorldPop 2025 R2025A layers.
    worldpop_dir = work / "worldpop"
    run([
        PY, download_script,
        "--dataset", "worldpop_core",
        "--output", worldpop_dir,
    ])

    expected_rasters = sorted(worldpop_dir.glob("*.tif"))
    if len(expected_rasters) != 6:
        raise ValueError(f"Expected six WorldPop rasters, found {len(expected_rasters)}")

    raster_info = {}
    worldpop_bytes = 0
    for path in expected_rasters:
        worldpop_bytes += path.stat().st_size
        with rasterio.open(path) as ds:
            raster_info[path.name] = {
                "bytes": path.stat().st_size,
                "crs": ds.crs.to_string() if ds.crs else None,
                "width": ds.width,
                "height": ds.height,
                "nodata": ds.nodata,
                "dtype": ds.dtypes[0],
                "transform": tuple(ds.transform),
            }

    # 4. Fractional-overlap aggregation to the exact LGA.
    lga_pop_csv = work / "lga_population_summary.csv"
    run([
        PY, population_script,
        "--dir", worldpop_dir,
        "--zones", lga_file,
        "--id-field", "lgacode",
        "--out", lga_pop_csv,
    ])
    lga_pop = pd.read_csv(lga_pop_csv, dtype={"lgacode": str})
    if len(lga_pop) != 1:
        raise ValueError("Expected one LGA population summary row.")

    # 5. Fractional-overlap aggregation to non-overlapping settlement components.
    settlement_pop_csv = work / "settlement_population.csv"
    run([
        PY, population_script,
        "--dir", worldpop_dir,
        "--zones", settlements_file,
        "--id-field", "settlement_component_id",
        "--out", settlement_pop_csv,
    ])
    settlement_pop = pd.read_csv(settlement_pop_csv)
    settlements = gpd.read_file(settlements_file)
    health = gpd.read_file(health_file)

    # 6. Reconciliation: settlement components are not forced to equal the LGA.
    metrics = [
        "population_total_est",
        "population_male_est",
        "population_female_est",
        "population_u1_est",
        "population_u5_est",
    ]
    reconciliation_rows = []
    for metric in metrics:
        lga_value = float(lga_pop.loc[0, metric])
        inside_value = float(settlement_pop[metric].sum(skipna=True))
        outside_value = lga_value - inside_value
        coverage = inside_value / lga_value * 100.0 if lga_value else None
        tolerance = max(1.0, abs(lga_value) * 0.001)
        if outside_value < -tolerance:
            raise ValueError(
                f"Settlement aggregation exceeds LGA {metric} by more than tolerance: "
                f"LGA={lga_value}, inside={inside_value}"
            )
        reconciliation_rows.append({
            "metric": metric,
            "lga_estimate": lga_value,
            "inside_mapped_settlements": inside_value,
            "outside_mapped_settlements": outside_value,
            "settlement_coverage_pct": coverage,
        })
    reconciliation = pd.DataFrame(reconciliation_rows)

    # 7. Logical demographic checks.
    row = lga_pop.iloc[0]
    total = float(row["population_total_est"])
    male = float(row["population_male_est"])
    female = float(row["population_female_est"])
    u1 = float(row["population_u1_est"])
    u5 = float(row["population_u5_est"])

    if abs((male + female) - total) > max(0.01, total * 1e-9):
        raise ValueError("Male + female does not reconcile to total.")
    if not (0 <= u1 <= u5 <= total):
        raise ValueError(f"Demographic hierarchy failed: u1={u1}, u5={u5}, total={total}")

    name_counts = settlements["name_match_status"].value_counts(dropna=False).to_dict()
    building_status = settlements["building_count_status"].value_counts(dropna=False).to_dict()
    overlap_checks = sorted(set(settlements["component_overlap_check"].astype(str)))

    # Persist validation-level aggregate summaries only; raw third-party national data are not committed.
    lga_pop.to_csv(out_dir / "lga_population_summary.csv", index=False)
    reconciliation.to_csv(out_dir / "population_reconciliation.csv", index=False)

    summary = {
        "status": "PASS",
        "pilot": {
            "state": "Bayelsa",
            "statecode": state_id,
            "lga": "Sagbama",
            "lgacode": lga_id,
            "bbox_wgs84": bbox,
        },
        "worldpop": {
            "dataset_id": "worldpop_agesex_2025_100m_r2025a",
            "reference_year": 2025,
            "required_raster_count": len(expected_rasters),
            "downloaded_bytes": worldpop_bytes,
            "rasters": raster_info,
        },
        "lga_population_estimates": {
            "total": total,
            "male": male,
            "female": female,
            "under_1": u1,
            "under_5": u5,
        },
        "settlements": {
            "component_count": int(len(settlements)),
            "name_match_status": {str(k): int(v) for k, v in name_counts.items()},
            "building_count_status": {str(k): int(v) for k, v in building_status.items()},
            "overlap_checks": overlap_checks,
        },
        "health_facilities": {
            "strictly_inside_lga_after_dedup_and_coordinate_checks": int(len(health))
        },
        "reconciliation": reconciliation.to_dict(orient="records"),
        "scientific_notes": [
            "WorldPop raster values are treated as estimated people per grid square, not density.",
            "Under-1 = m_00 + f_00; under-5 = under-1 + m_01 + f_01.",
            "Population aggregation uses exactextract fractional pixel overlap without raster resampling.",
            "Settlement components are clipped to the exact LGA and checked for overlap before reconciliation.",
            "Whole-source-block building counts are not assigned to partial cross-boundary components.",
            "Health-facility inclusion does not imply operational status or service availability."
        ],
        "raw_third_party_data_committed": False,
        "settlement_source_version": "GRID3 NGA Settlement Extents v3.1",
        "settlement_v3_1_derived_geometry_published_in_git_history": False,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== SAGBAMA FULL PILOT SUMMARY ===")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
