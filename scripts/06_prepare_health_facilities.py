from __future__ import annotations
import argparse
from pathlib import Path
import geopandas as gpd

IDS = ["nhfr_uid","nhfr_facility_code","globalid"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--facilities", required=True)
    p.add_argument("--lga", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    h = gpd.read_file(args.facilities).to_crs(4326)
    lga = gpd.read_file(args.lga).to_crs(4326)
    if len(lga) != 1:
        raise ValueError("--lga must contain exactly one polygon.")

    xy_ok = h.geometry.geom_type.eq("Point") & h.geometry.x.between(2.0, 15.5) & h.geometry.y.between(3.5, 14.5)
    h["coordinate_valid_nigeria_bbox"] = xy_ok
    h = h[xy_ok].copy()

    id_col = next((c for c in IDS if c in h.columns and h[c].notna().any()), None)
    if id_col:
        before = len(h)
        h = h.sort_values(id_col).drop_duplicates(subset=[id_col], keep="first")
        print("Deduplicated on", id_col, "removed", before-len(h))

    inside = gpd.sjoin(h, lga[["geometry"]], how="inner", predicate="within").drop(columns=["index_right"], errors="ignore")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    inside.to_file(out, driver="GPKG")
    print("Facilities inside selected LGA:", len(inside))
    print("No claim is made that these facilities are operational or provide a specific service.")
    print("Saved:", out)

if __name__ == "__main__":
    main()
