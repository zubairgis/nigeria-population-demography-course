from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
import shapely
from shapely.geometry import Polygon
from s2sphere import Cell, CellId, LatLng, LatLngRect, RegionCoverer

BASE = "https://storage.googleapis.com/open-buildings-data/v3"
LEVEL6_DIR = f"{BASE}/polygons_s2_level_6_gzip_no_header"
THRESHOLDS_URL = f"{BASE}/score_thresholds_s2_level_4.csv"
COLUMNS = [
    "latitude", "longitude", "area_in_meters", "confidence",
    "geometry", "full_plus_code"
]
UA = "nigeria-population-demography-course/0.1"

def s2_covering_tokens(geometry, level=6):
    xmin, ymin, xmax, ymax = geometry.bounds
    rect = LatLngRect.from_point_pair(
        LatLng.from_degrees(ymin, xmin),
        LatLng.from_degrees(ymax, xmax),
    )
    coverer = RegionCoverer()
    coverer.min_level = level
    coverer.max_level = level
    coverer.max_cells = 1_000_000
    return [c.to_token() for c in coverer.get_covering(rect)]

def token_polygon(token):
    cell = Cell(CellId.from_token(token))
    coords = []
    for i in range(4):
        ll = LatLng.from_point(cell.get_vertex(i))
        coords.append((ll.lng().degrees, ll.lat().degrees))
    return Polygon(coords)

def parent_l4_token(token_l6):
    return CellId.from_token(token_l6).parent(4).to_token()

def load_thresholds(precision):
    df = pd.read_csv(THRESHOLDS_URL)
    token_col = next((c for c in ["s2_token", "token"] if c in df.columns), None)
    threshold_col = f"confidence_threshold_{precision}%_precision"
    if token_col is None or threshold_col not in df.columns:
        raise ValueError(
            f"Expected score-threshold fields not found. Columns: {list(df.columns)}"
        )
    out = df[[token_col, threshold_col]].copy()
    out[token_col] = out[token_col].astype(str)
    out[threshold_col] = pd.to_numeric(out[threshold_col], errors="coerce")
    return dict(zip(out[token_col], out[threshold_col])), threshold_col

def download_file(url, target):
    headers = {"User-Agent": UA}
    with requests.get(url, stream=True, headers=headers, timeout=(30, 300)) as r:
        if r.status_code == 404:
            return False, 0
        r.raise_for_status()
        size = 0
        with open(target, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
    return True, size

def main():
    p = argparse.ArgumentParser(
        description="Download Google Open Buildings V3 polygons for one AOI using Google's level-6 S2 shard method."
    )
    p.add_argument("--aoi", required=True, help="Polygon file containing one selected LGA/AOI")
    p.add_argument("--out", required=True, help="Output GeoParquet of detected footprints")
    p.add_argument("--summary", required=True, help="Output JSON provenance/validation summary")
    p.add_argument("--precision", type=int, choices=[80, 85, 90], default=90)
    p.add_argument(
        "--min-confidence", type=float, default=None,
        help="Optional explicit threshold. If omitted, Google's per-level-4 tile threshold for requested precision is used."
    )
    p.add_argument("--chunk-size", type=int, default=250_000)
    args = p.parse_args()

    aoi = gpd.read_file(args.aoi)
    if aoi.empty or aoi.crs is None:
        raise ValueError("AOI must contain valid polygon geometry and a CRS.")
    aoi = aoi.to_crs(4326)
    if (~aoi.geometry.is_valid).any():
        raise ValueError("AOI contains invalid geometry.")
    aoi_geom = aoi.geometry.union_all()
    if aoi_geom.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"AOI geometry must be polygonal, got {aoi_geom.geom_type}")

    thresholds = None
    threshold_field = None
    if args.min_confidence is None:
        thresholds, threshold_field = load_thresholds(args.precision)

    tokens = s2_covering_tokens(aoi_geom, level=6)
    tokens = [t for t in tokens if token_polygon(t).intersects(aoi_geom)]
    if not tokens:
        raise RuntimeError("No level-6 S2 tiles intersect the AOI.")

    kept_parts = []
    tile_summaries = []
    total_download_bytes = 0
    total_rows_read = 0
    total_rows_in_aoi_before_threshold = 0
    total_rows_kept = 0

    xmin, ymin, xmax, ymax = aoi_geom.bounds

    with tempfile.TemporaryDirectory(prefix="open_buildings_") as tmp:
        tmp = Path(tmp)
        for token in tokens:
            parent4 = parent_l4_token(token)
            if args.min_confidence is None:
                threshold = thresholds.get(parent4)
                if threshold is None or pd.isna(threshold):
                    raise ValueError(
                        f"No Google {args.precision}% precision threshold found for level-4 tile {parent4}."
                    )
                threshold = float(threshold)
            else:
                threshold = float(args.min_confidence)

            url = f"{LEVEL6_DIR}/{token}_buildings.csv.gz"
            local = tmp / f"{token}_buildings.csv.gz"
            found, nbytes = download_file(url, local)
            total_download_bytes += nbytes

            tile_row_count = 0
            tile_inside_count = 0
            tile_kept_count = 0

            if found:
                chunks = pd.read_csv(
                    local,
                    compression="gzip",
                    header=None,
                    names=COLUMNS,
                    chunksize=args.chunk_size,
                    low_memory=False,
                )
                for chunk in chunks:
                    if len(chunk.columns) != len(COLUMNS):
                        raise ValueError(f"Unexpected Open Buildings schema for tile {token}.")

                    chunk["latitude"] = pd.to_numeric(chunk["latitude"], errors="coerce")
                    chunk["longitude"] = pd.to_numeric(chunk["longitude"], errors="coerce")
                    chunk["confidence"] = pd.to_numeric(chunk["confidence"], errors="coerce")
                    chunk["area_in_meters"] = pd.to_numeric(chunk["area_in_meters"], errors="coerce")
                    chunk = chunk.dropna(subset=["latitude", "longitude", "confidence"])

                    tile_row_count += len(chunk)
                    total_rows_read += len(chunk)

                    bbox_mask = (
                        chunk["longitude"].between(xmin, xmax)
                        & chunk["latitude"].between(ymin, ymax)
                    )
                    chunk = chunk[bbox_mask].copy()
                    if chunk.empty:
                        continue

                    inside = shapely.contains_xy(
                        aoi_geom,
                        chunk["longitude"].to_numpy(),
                        chunk["latitude"].to_numpy(),
                    )
                    chunk = chunk[inside].copy()
                    tile_inside_count += len(chunk)
                    total_rows_in_aoi_before_threshold += len(chunk)
                    if chunk.empty:
                        continue

                    chunk = chunk[chunk["confidence"] >= threshold].copy()
                    tile_kept_count += len(chunk)
                    total_rows_kept += len(chunk)
                    if chunk.empty:
                        continue

                    chunk["s2_token_l6"] = token
                    chunk["s2_token_l4"] = parent4
                    chunk["confidence_threshold_used"] = threshold
                    kept_parts.append(chunk)

            tile_summaries.append({
                "s2_token_l6": token,
                "s2_token_l4": parent4,
                "source_url": url,
                "source_found": found,
                "download_bytes": nbytes,
                "confidence_threshold_used": threshold,
                "rows_read": tile_row_count,
                "centroids_inside_aoi_before_threshold": tile_inside_count,
                "detections_kept": tile_kept_count,
            })

    if kept_parts:
        df = pd.concat(kept_parts, ignore_index=True)
    else:
        df = pd.DataFrame(columns=COLUMNS + [
            "s2_token_l6", "s2_token_l4", "confidence_threshold_used"
        ])

    exact_duplicates = 0
    if not df.empty:
        duplicate_keys = ["latitude", "longitude", "full_plus_code", "geometry"]
        dup = df.duplicated(subset=duplicate_keys, keep="first")
        exact_duplicates = int(dup.sum())
        df = df[~dup].copy()

        geometry = gpd.GeoSeries.from_wkt(df["geometry"], on_invalid="warn", crs=4326)
        invalid_wkt = int(geometry.isna().sum())
        if invalid_wkt:
            raise ValueError(f"{invalid_wkt} retained Open Buildings rows have invalid WKT geometry.")
        gdf = gpd.GeoDataFrame(df.drop(columns=["geometry"]), geometry=geometry, crs=4326)
    else:
        gdf = gpd.GeoDataFrame(
            df.drop(columns=["geometry"], errors="ignore"),
            geometry=gpd.GeoSeries([], crs=4326),
            crs=4326,
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(out, index=False)

    summary = {
        "dataset": "Google Open Buildings V3 polygons",
        "source_method": "Google official region-download pattern using S2 level-6 gzip shards",
        "aoi_centroid_rule": "source latitude/longitude centroid strictly within AOI",
        "precision_target": None if args.min_confidence is not None else args.precision,
        "explicit_min_confidence": args.min_confidence,
        "threshold_field": threshold_field,
        "tiles_considered": len(tokens),
        "download_bytes": total_download_bytes,
        "rows_read": total_rows_read,
        "centroids_inside_aoi_before_threshold": total_rows_in_aoi_before_threshold,
        "detections_after_confidence_filter_before_dedup": total_rows_kept,
        "exact_duplicates_removed": exact_duplicates,
        "detected_footprints_output": int(len(gdf)),
        "output_file": str(out),
        "tile_details": tile_summaries,
        "limitations": [
            "Detected footprints are not households, occupied dwellings, or necessarily residential buildings.",
            "Source imagery dates vary geographically; v3 inference was run in May 2023.",
            "Confidence filtering trades recall for precision.",
            "Centroid allocation is deterministic but a footprint can physically cross a polygon boundary."
        ],
    }
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
