from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

def main():
    p = argparse.ArgumentParser(
        description=(
            "Allocate detected building footprints exactly once to non-overlapping "
            "settlement/LGA components using a documented centroid rule."
        )
    )
    p.add_argument("--buildings", required=True, help="Building polygons, preferably Google Open Buildings pilot GeoParquet")
    p.add_argument("--zones", required=True, help="Non-overlapping settlement/LGA component polygons")
    p.add_argument("--zone-id", default="settlement_component_id")
    p.add_argument("--min-confidence", type=float, default=None)
    p.add_argument("--out", required=True, help="Output CSV of counts per zone")
    p.add_argument("--summary", help="Optional JSON allocation summary")
    args = p.parse_args()

    b = gpd.read_file(args.buildings).to_crs(4326)
    z = gpd.read_file(args.zones).to_crs(4326)
    if b.empty:
        raise ValueError("Building layer is empty.")
    if z.empty:
        raise ValueError("Zone layer is empty.")
    if args.zone_id not in z.columns:
        raise ValueError(f"Missing zone id: {args.zone_id}")
    if z[args.zone_id].isna().any() or z[args.zone_id].astype(str).duplicated().any():
        raise ValueError("Zone IDs must be non-null and unique.")
    if (~z.geometry.is_valid).any():
        raise ValueError("Zone layer contains invalid geometry.")

    if args.min_confidence is not None:
        if "confidence" not in b.columns:
            raise ValueError(
                "A confidence threshold was requested but the building layer has no 'confidence' field."
            )
        b["confidence"] = pd.to_numeric(b["confidence"], errors="coerce")
        b = b[b["confidence"] >= args.min_confidence].copy()

    # Prefer Google's documented source centroid coordinates when present.
    if {"latitude", "longitude"}.issubset(b.columns):
        lat = pd.to_numeric(b["latitude"], errors="coerce")
        lon = pd.to_numeric(b["longitude"], errors="coerce")
        good = lat.notna() & lon.notna()
        dropped_missing_centroid = int((~good).sum())
        b = b[good].copy()
        cent = b.copy()
        cent.geometry = gpd.points_from_xy(
            pd.to_numeric(b["longitude"]),
            pd.to_numeric(b["latitude"]),
            crs=4326,
        )
        allocation_method = "source centroid coordinates strictly within component"
    else:
        dropped_missing_centroid = 0
        proj = b.estimate_utm_crs()
        if proj is None:
            raise ValueError("Could not determine projected CRS for footprint centroid calculation.")
        bp = b.to_crs(proj)
        cent = bp.copy()
        cent.geometry = bp.geometry.centroid
        cent = cent.to_crs(4326)
        allocation_method = "footprint centroid calculated in local projected CRS, strictly within component"

    # Each detection may match at most one non-overlapping component.
    j = gpd.sjoin(
        cent,
        z[[args.zone_id, "geometry"]],
        how="left",
        predicate="within",
    )
    multi = j.index.duplicated(keep=False)
    if multi.any():
        raise ValueError(
            f"{int(multi.sum())} building detections matched multiple zones. "
            "Resolve zone overlaps before allocation."
        )

    allocated_mask = j[args.zone_id].notna()
    allocated = int(allocated_mask.sum())
    unallocated = int((~allocated_mask).sum())

    counts = (
        j[allocated_mask]
        .groupby(args.zone_id)
        .size()
        .rename("detected_building_count")
        .reset_index()
    )

    # Include zero-building components explicitly.
    counts = (
        z[[args.zone_id]]
        .drop_duplicates()
        .merge(counts, on=args.zone_id, how="left", validate="one_to_one")
    )
    counts["detected_building_count"] = (
        counts["detected_building_count"].fillna(0).astype("int64")
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(out, index=False)

    summary = {
        "input_detections_after_confidence_filter": int(len(b)),
        "dropped_missing_centroid": dropped_missing_centroid,
        "allocated_to_one_component": allocated,
        "inside_lga_but_outside_mapped_settlement_components": unallocated,
        "zone_count": int(len(counts)),
        "allocation_method": allocation_method,
        "boundary_rule": (
            "strict within; a centroid exactly on a component boundary is not assigned "
            "to either neighboring component and remains unallocated"
        ),
        "interpretation": (
            "Counts represent detected building footprints, not households, occupied "
            "dwellings, or residential buildings."
        ),
    }

    if args.summary:
        summary_path = Path(args.summary)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print("Saved:", out)

if __name__ == "__main__":
    main()
