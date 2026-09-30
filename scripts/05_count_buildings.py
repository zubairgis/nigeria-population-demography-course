from __future__ import annotations
import argparse
import geopandas as gpd

def main():
    p = argparse.ArgumentParser(
        description="Allocate detected building footprints once using footprint-centroid containment."
    )
    p.add_argument("--buildings", required=True, help="Pilot/state building polygons")
    p.add_argument("--zones", required=True, help="Non-overlapping settlement/LGA component polygons")
    p.add_argument("--zone-id", default="settlement_component_id")
    p.add_argument("--min-confidence", type=float, default=None)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    b = gpd.read_file(args.buildings).to_crs(4326)
    z = gpd.read_file(args.zones).to_crs(4326)
    if args.zone_id not in z.columns:
        raise ValueError(f"Missing zone id: {args.zone_id}")

    if args.min_confidence is not None:
        if "confidence" not in b.columns:
            raise ValueError("A confidence threshold was requested but the building layer has no 'confidence' field.")
        b = b[b["confidence"] >= args.min_confidence].copy()

    proj = b.estimate_utm_crs()
    bp = b.to_crs(proj)
    cent = bp.copy()
    cent.geometry = bp.geometry.centroid
    cent = cent.to_crs(4326)

    j = gpd.sjoin(cent, z[[args.zone_id,"geometry"]], how="left", predicate="within")
    dup = j.index.duplicated(keep=False)
    if dup.any():
        raise ValueError(f"{dup.sum()} building records matched multiple zones. Resolve zone overlaps first.")

    counts = j.groupby(args.zone_id).size().rename("detected_building_count").reset_index()
    counts.to_csv(args.out, index=False)
    print("Input detections after filtering:", len(b))
    print("Allocated:", j[args.zone_id].notna().sum())
    print("Unallocated:", j[args.zone_id].isna().sum())
    print("Saved:", args.out)

if __name__ == "__main__":
    main()
