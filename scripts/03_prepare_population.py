from __future__ import annotations
import argparse
from pathlib import Path
import rasterio

EXPECTED = {
    "male":"nga_T_M_2025_CN_100m_R2025A_v1.tif",
    "female":"nga_T_F_2025_CN_100m_R2025A_v1.tif",
    "m00":"nga_m_00_2025_CN_100m_R2025A_v1.tif",
    "f00":"nga_f_00_2025_CN_100m_R2025A_v1.tif",
    "m01":"nga_m_01_2025_CN_100m_R2025A_v1.tif",
    "f01":"nga_f_01_2025_CN_100m_R2025A_v1.tif",
}

def inspect(paths):
    meta0 = None
    for k,p in paths.items():
        with rasterio.open(p) as ds:
            meta = (ds.crs.to_string(), ds.transform, ds.width, ds.height, ds.nodata)
            print(k, p.name, "CRS", ds.crs, "size", ds.width, ds.height, "nodata", ds.nodata)
            if meta0 is None:
                meta0 = meta
            elif meta[:4] != meta0[:4]:
                raise ValueError(f"Raster grid mismatch: {k}")
    return meta0

def main():
    p = argparse.ArgumentParser(description="Validate the six compatible WorldPop demographic rasters.")
    p.add_argument("--dir", required=True)
    args = p.parse_args()
    d = Path(args.dir)
    paths = {k:d/name for k,name in EXPECTED.items()}
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required files:\n" + "\n".join(missing))
    inspect(paths)
    print("Definitions:")
    print(" total = T_M + T_F")
    print(" under1 = m_00 + f_00")
    print(" under5 = m_00 + f_00 + m_01 + f_01")
    print("No raster resampling has been performed.")

if __name__ == "__main__":
    main()
