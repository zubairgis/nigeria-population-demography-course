from __future__ import annotations
import argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--extents", required=True)
    p.add_argument("--names", required=True)
    p.add_argument("--lga", required=True, help="Single selected LGA polygon file")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    ext = gpd.read_file(args.extents).to_crs(4326)
    names = gpd.read_file(args.names).to_crs(4326)
    lga = gpd.read_file(args.lga).to_crs(4326)
    if len(lga) != 1:
        raise ValueError("--lga must contain exactly one selected LGA polygon.")

    block_id = "block_id"
    if block_id not in ext.columns:
        raise ValueError("Expected GRID3 v4.1 field 'block_id' not found. Stop and inspect schema.")

    components = gpd.overlay(ext, lga[["geometry"]], how="intersection", keep_geom_type=True)
    components = components[~components.geometry.is_empty].copy()
    components["source_settlement_id"] = components[block_id].astype(str)
    components["settlement_component_id"] = components["source_settlement_id"] + "__LGA_COMPONENT"

    joined = gpd.sjoin(names, components[["settlement_component_id","geometry"]],
                       how="inner", predicate="within")
    name_col = next((c for c in ["settlement_name","name","Name","sett_name"] if c in joined.columns), None)
    if name_col:
        agg = (joined.groupby("settlement_component_id")[name_col]
               .agg(lambda s: " | ".join(sorted(set(str(x) for x in s.dropna() if str(x).strip()))))
               .rename("settlement_name"))
        count = joined.groupby("settlement_component_id").size().rename("name_point_count")
        components = components.merge(pd.concat([agg,count],axis=1), on="settlement_component_id", how="left")
    else:
        components["settlement_name"] = None
        components["name_point_count"] = 0

    components["name_point_count"] = components["name_point_count"].fillna(0).astype(int)
    components["name_match_status"] = components["name_point_count"].map(
        lambda n: "unmatched" if n==0 else ("single" if n==1 else "multiple")
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    components.to_file(out, driver="GPKG")
    print("Components:", len(components))
    print(components["name_match_status"].value_counts(dropna=False).to_string())
    print("Saved:", out)

if __name__ == "__main__":
    main()
