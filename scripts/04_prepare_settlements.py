from __future__ import annotations
import argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd

NAME_FIELD = "set_name"
NAME_ID_FIELD = "set_id"
ALT_NAME_FIELD = "set_altnam"
BLOCK_ID_FIELD = "block_id"
SOURCE_BUILDING_FIELD = "building_count"

def _join_unique(values):
    cleaned = sorted({str(x).strip() for x in values.dropna() if str(x).strip()})
    return " | ".join(cleaned) if cleaned else None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--extents", required=True)
    p.add_argument("--names", required=True)
    p.add_argument("--lga", required=True, help="Single selected LGA polygon file")
    p.add_argument("--lga-id", required=True, help="Stable source LGA code, e.g. lgacode value")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    ext = gpd.read_file(args.extents).to_crs(4326)
    names = gpd.read_file(args.names).to_crs(4326)
    lga = gpd.read_file(args.lga).to_crs(4326)
    if len(lga) != 1:
        raise ValueError("--lga must contain exactly one selected LGA polygon.")

    if BLOCK_ID_FIELD not in ext.columns:
        raise ValueError("Expected GRID3 v4.1 field 'block_id' not found. Stop and inspect schema.")
    for field in [NAME_ID_FIELD, NAME_FIELD]:
        if field not in names.columns:
            raise ValueError(f"Expected GRID3 Settlement Names field '{field}' not found.")

    if ext[BLOCK_ID_FIELD].astype(str).duplicated().any():
        raise ValueError("Source settlement block_id values are not unique in the downloaded subset.")

    # Record source area before clipping so whole-block building counts are not
    # silently copied to a partial LGA component.
    area_crs = lga.estimate_utm_crs()
    if area_crs is None:
        raise ValueError("Could not determine a projected CRS for area checks.")
    ext["_source_area_m2_calc"] = ext.to_crs(area_crs).geometry.area.to_numpy()

    if SOURCE_BUILDING_FIELD in ext.columns:
        ext["source_building_count"] = pd.to_numeric(
            ext[SOURCE_BUILDING_FIELD], errors="coerce"
        )
    else:
        ext["source_building_count"] = pd.NA

    components = gpd.overlay(ext, lga[["geometry"]], how="intersection", keep_geom_type=True)
    components = components[~components.geometry.is_empty].copy()
    components["source_settlement_id"] = components[BLOCK_ID_FIELD].astype(str)
    components["lga_id"] = str(args.lga_id)
    components["settlement_component_id"] = (
        components["source_settlement_id"] + "__" + components["lga_id"]
    )

    # If overlay produced multiple fragments for the same source block/LGA,
    # dissolve them before any population aggregation.
    if components["settlement_component_id"].duplicated().any():
        first_cols = [
            c for c in components.columns
            if c not in {"geometry", "settlement_component_id"}
        ]
        agg = {c: "first" for c in first_cols}
        components = components.dissolve(
            by="settlement_component_id", aggfunc=agg, as_index=False
        )

    comp_proj = components.to_crs(area_crs)
    components["component_area_m2_calc"] = comp_proj.geometry.area.to_numpy()
    components["component_fraction_of_source"] = (
        components["component_area_m2_calc"] / components["_source_area_m2_calc"]
    ).clip(lower=0, upper=1)

    full_source = components["component_fraction_of_source"] >= 0.999999
    components["detected_building_count"] = pd.NA
    components.loc[full_source, "detected_building_count"] = (
        components.loc[full_source, "source_building_count"]
    )
    components["building_count_status"] = "requires_footprint_allocation"
    components.loc[full_source, "building_count_status"] = (
        "source_full_block_count_provisional"
    )

    # Prevent settlement population reconciliation from silently double counting
    # overlapping component polygons. Tiny floating-point slivers are tolerated.
    proj = components.to_crs(area_crs)
    summed_area = float(proj.geometry.area.sum())
    union_geom = proj.geometry.union_all()
    union_area = float(union_geom.area) if union_geom is not None else 0.0
    overlap_area = max(0.0, summed_area - union_area)
    overlap_fraction = overlap_area / summed_area if summed_area else 0.0
    if overlap_fraction > 1e-6:
        raise ValueError(
            "Settlement components overlap enough to risk population double counting: "
            f"overlap_fraction={overlap_fraction:.8f}. Resolve overlaps before aggregation."
        )
    components["component_overlap_check"] = f"PASS:{overlap_fraction:.10f}"

    joined = gpd.sjoin(
        names,
        components[["settlement_component_id", "geometry"]],
        how="inner",
        predicate="within",
    )

    if joined.empty:
        name_summary = pd.DataFrame(columns=[
            "settlement_component_id", "settlement_name", "settlement_name_ids",
            "settlement_alt_names", "name_point_count"
        ])
    else:
        grouped = joined.groupby("settlement_component_id")
        name_summary = pd.DataFrame({
            "settlement_name": grouped[NAME_FIELD].agg(_join_unique),
            "settlement_name_ids": grouped[NAME_ID_FIELD].agg(_join_unique),
            "name_point_count": grouped.size(),
        })
        if ALT_NAME_FIELD in joined.columns:
            name_summary["settlement_alt_names"] = grouped[ALT_NAME_FIELD].agg(_join_unique)
        else:
            name_summary["settlement_alt_names"] = None
        name_summary = name_summary.reset_index()

    components = components.merge(name_summary, on="settlement_component_id", how="left")
    components["name_point_count"] = components["name_point_count"].fillna(0).astype(int)
    components["name_match_status"] = components["name_point_count"].map(
        lambda n: "unmatched" if n == 0 else ("single" if n == 1 else "multiple")
    )

    components = components.drop(
        columns=["_source_area_m2_calc", "component_area_m2_calc"],
        errors="ignore"
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    components.to_file(out, driver="GPKG")
    print("Settlement components:", len(components))
    print("Name matching:")
    print(components["name_match_status"].value_counts(dropna=False).to_string())
    print("Building-count status:")
    print(components["building_count_status"].value_counts(dropna=False).to_string())
    print(f"Component overlap fraction: {overlap_fraction:.10f}")
    print("Saved:", out)

if __name__ == "__main__":
    main()
