from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import geopandas as gpd
import rasterio
from exactextract import exact_extract

EXPECTED = {
    "male": "nga_T_M_2025_CN_100m_R2025A_v1.tif",
    "female": "nga_T_F_2025_CN_100m_R2025A_v1.tif",
    "m00": "nga_m_00_2025_CN_100m_R2025A_v1.tif",
    "f00": "nga_f_00_2025_CN_100m_R2025A_v1.tif",
    "m01": "nga_m_01_2025_CN_100m_R2025A_v1.tif",
    "f01": "nga_f_01_2025_CN_100m_R2025A_v1.tif",
}

OUTPUT_NAMES = {
    "male": "population_male_est",
    "female": "population_female_est",
    "m00": "population_male_u1_est",
    "f00": "population_female_u1_est",
    "m01": "population_male_1_4_est",
    "f01": "population_female_1_4_est",
}

def inspect(paths):
    meta0 = None
    for key, path in paths.items():
        with rasterio.open(path) as ds:
            if ds.crs is None:
                raise ValueError(f"Raster has no CRS: {path}")
            meta = (ds.crs.to_string(), ds.transform, ds.width, ds.height)
            print(key, path.name, "CRS", ds.crs, "size", ds.width, ds.height,
                  "nodata", ds.nodata, "dtype", ds.dtypes[0])
            if meta0 is None:
                meta0 = meta
            elif meta != meta0:
                raise ValueError(f"Raster grid mismatch: {key}")
    return meta0

def aggregate_one(raster_path: Path, zones: gpd.GeoDataFrame, id_field: str) -> pd.DataFrame:
    result = exact_extract(
        str(raster_path),
        zones[[id_field, "geometry"]],
        ["sum"],
        include_cols=[id_field],
        output="pandas",
    )
    if "sum" not in result.columns:
        raise RuntimeError(f"exactextract did not return a sum column for {raster_path.name}")
    return result[[id_field, "sum"]]

def main():
    p = argparse.ArgumentParser(
        description="Validate and fractionally aggregate the six compatible WorldPop demographic rasters."
    )
    p.add_argument("--dir", required=True, help="Directory containing the six WorldPop GeoTIFFs")
    p.add_argument("--zones", help="Polygon layer to aggregate; omit for raster validation only")
    p.add_argument("--id-field", help="Unique polygon identifier used when --zones is supplied")
    p.add_argument("--out", help="Output CSV used when --zones is supplied")
    args = p.parse_args()

    d = Path(args.dir)
    paths = {key: d / name for key, name in EXPECTED.items()}
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required files:\n" + "\n".join(missing))

    crs_text, *_ = inspect(paths)
    print("Definitions:")
    print(" total = T_M + T_F")
    print(" under1 = m_00 + f_00")
    print(" under5 = m_00 + f_00 + m_01 + f_01")
    print("Raster values are estimated people per grid square; no raster resampling is performed.")

    if not args.zones:
        return
    if not args.id_field or not args.out:
        raise ValueError("--id-field and --out are required when --zones is supplied.")

    zones = gpd.read_file(args.zones)
    if zones.empty:
        raise ValueError("Zone layer is empty.")
    if zones.crs is None:
        raise ValueError("Zone layer has no CRS.")
    if args.id_field not in zones.columns:
        raise ValueError(f"Missing zone ID field: {args.id_field}")
    if zones[args.id_field].isna().any() or zones[args.id_field].astype(str).duplicated().any():
        raise ValueError("Zone IDs must be non-null and unique.")
    if (~zones.geometry.is_valid).any():
        raise ValueError("Zone layer contains invalid geometry.")

    zones = zones.to_crs(crs_text)
    out = zones[[args.id_field]].copy()

    for key, raster_path in paths.items():
        stat = aggregate_one(raster_path, zones, args.id_field)
        stat = stat.rename(columns={"sum": OUTPUT_NAMES[key]})
        out = out.merge(stat, on=args.id_field, how="left", validate="one_to_one")

    numeric = list(OUTPUT_NAMES.values())
    out[numeric] = out[numeric].astype(float)
    out["population_total_est"] = out["population_male_est"] + out["population_female_est"]
    out["population_u1_est"] = out["population_male_u1_est"] + out["population_female_u1_est"]
    out["population_u5_est"] = (
        out["population_u1_est"]
        + out["population_male_1_4_est"]
        + out["population_female_1_4_est"]
    )
    out["population_reference_year"] = 2025
    out["population_dataset_id"] = "worldpop_agesex_2025_100m_r2025a"
    out["aggregation_method"] = "exactextract fractional cell-overlap sum"
    out["partial_cell_assumption"] = "population uniformly distributed within each raster cell"

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)
    print("Aggregated zones:", len(out))
    print("Saved:", output_path)

if __name__ == "__main__":
    main()
