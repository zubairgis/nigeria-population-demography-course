from __future__ import annotations
import argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd

IDS = ["nhfr_uid", "nhfr_facility_code", "globalid"]

def _norm_id(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip()
    return s.mask(s.isin(["", "nan", "None", "<NA>"]))

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

    if h.empty:
        raise ValueError("Health-facility layer is empty.")

    xy_ok = (
        h.geometry.geom_type.eq("Point")
        & h.geometry.x.between(2.0, 15.5)
        & h.geometry.y.between(3.5, 14.5)
    )
    h["coordinate_valid_nigeria_bbox"] = xy_ok
    invalid_coord_count = int((~xy_ok).sum())
    h = h[xy_ok].copy()

    # Construct one deterministic identifier per row using the strongest
    # documented ID available. Missing NHFR IDs do not cause unrelated rows
    # with null IDs to be collapsed.
    canonical = pd.Series(pd.NA, index=h.index, dtype="string")
    source = pd.Series(pd.NA, index=h.index, dtype="string")
    for col in IDS:
        if col in h.columns:
            vals = _norm_id(h[col])
            take = canonical.isna() & vals.notna()
            canonical.loc[take] = vals.loc[take]
            source.loc[take] = col

    # If last_updated is available, prefer the newest record when an identifier
    # is duplicated. Rows with no usable identifier remain distinct.
    if "last_updated" in h.columns:
        h["_last_updated_sort"] = pd.to_datetime(h["last_updated"], errors="coerce", utc=True)
        h = h.sort_values("_last_updated_sort", ascending=False, na_position="last")
        canonical = canonical.reindex(h.index)
        source = source.reindex(h.index)

    h["_canonical_facility_id"] = canonical
    h["_canonical_id_source"] = source
    has_id = h["_canonical_facility_id"].notna()
    with_id = h[has_id].drop_duplicates(subset=["_canonical_facility_id"], keep="first")
    without_id = h[~has_id]
    before = len(h)
    h = pd.concat([with_id, without_id], axis=0)
    h = gpd.GeoDataFrame(h, geometry="geometry", crs=4326)
    duplicate_removed = before - len(h)

    # For the selected LGA, use strict point-in-polygon containment. Boundary
    # points are counted separately so they are not silently assigned to two
    # neighboring LGAs in a national workflow.
    within_mask = h.geometry.within(lga.geometry.iloc[0])
    boundary_mask = h.geometry.intersects(lga.geometry.iloc[0].boundary)
    inside = h[within_mask].copy()
    boundary_count = int(boundary_mask.sum())

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    inside = inside.drop(columns=["_last_updated_sort"], errors="ignore")
    inside.to_file(out, driver="GPKG")
    print("Invalid Nigeria-bbox coordinates excluded:", invalid_coord_count)
    print("Duplicate records removed:", duplicate_removed)
    print("Facilities strictly inside selected LGA:", len(inside))
    print("Facilities exactly on selected LGA boundary:", boundary_count)
    print("No claim is made that these facilities are operational or provide a specific service.")
    print("Saved:", out)

if __name__ == "__main__":
    main()
