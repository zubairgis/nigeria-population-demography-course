from __future__ import annotations
import argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd

NAME_FIELD = "set_name"
NAME_ID_FIELD = "set_id"
ALT_NAME_FIELD = "set_altnam"
BLOCK_ID_FIELD = "block_id"

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

    components = gpd.overlay(ext, lga[["geometry"]], how="intersection", keep_geom_type=True)
    components = components[~components.geometry.is_empty].copy()
    components["source_settlement_id"] = components[BLOCK_ID_FIELD].astype(str)
    components["lga_id"] = str(args.lga_id)
    components["settlement_component_id"] = (
        components["source_settlement_id"] + "__" + components["lga_id"]
    )

    if components["settlement_component_id"].duplicated().any():
        agg = {c: "first" for c in components.columns if c not in {"geometry", "settlement_component_id"}}
        components = components.dissolve(by="settlement_component_id", aggfunc=agg, as_index=False)

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

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    components.to_file(out, driver="GPKG")
    print("Settlement components:", len(components))
    print(components["name_match_status"].value_counts(dropna=False).to_string())
    print("Saved:", out)

if __name__ == "__main__":
    main()
