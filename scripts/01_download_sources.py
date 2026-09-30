from __future__ import annotations
import argparse, json
from pathlib import Path
from common import (
    resolve_arcgis_feature_service, first_feature_layer,
    query_feature_layer_geojson, get_json, download_stream, sha256sum
)

TITLES = {
    "state_boundaries": "GRID3 NGA - Operational State Boundaries",
    "lga_boundaries": "GRID3 NGA - Operational LGA Boundaries",
    "settlement_names": "GRID3 NGA - Settlement Names",
    "settlement_extents": "GRID3 NGA - Settlement Extents v4.1",
    "health_v2": "GRID3 NGA - Health Facilities v2.0",
}

WORLDPOP_ITEM = "nga_agesex_2025_CN_100m_R2025A_v1"
WORLDPOP_STAC = "https://api.stac.worldpop.org"
WORLDPOP_REQUIRED = [
    "nga_T_M_2025_CN_100m_R2025A_v1.tif",
    "nga_T_F_2025_CN_100m_R2025A_v1.tif",
    "nga_m_00_2025_CN_100m_R2025A_v1.tif",
    "nga_f_00_2025_CN_100m_R2025A_v1.tif",
    "nga_m_01_2025_CN_100m_R2025A_v1.tif",
    "nga_f_01_2025_CN_100m_R2025A_v1.tif",
]

def worldpop_assets():
    url = f"{WORLDPOP_STAC}/collections/NGA/items/{WORLDPOP_ITEM}"
    item = get_json(url)
    assets = item.get("assets", {})
    by_name = {}
    for key, a in assets.items():
        href = a.get("href")
        if href:
            by_name[href.rsplit("/",1)[-1]] = {"key":key, **a}
    missing = [n for n in WORLDPOP_REQUIRED if n not in by_name]
    if missing:
        raise RuntimeError(
            "Required WorldPop assets were not found in the live STAC item. "
            f"Missing: {missing}. Do not guess URLs; inspect the item."
        )
    return by_name

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=list(TITLES)+["worldpop_core"], required=True)
    p.add_argument("--output", default="downloads")
    p.add_argument("--bbox", nargs=4, type=float, metavar=("XMIN","YMIN","XMAX","YMAX"))
    p.add_argument("--metadata-only", action="store_true")
    args = p.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    if args.dataset == "worldpop_core":
        assets = worldpop_assets()
        print("WorldPop live STAC item resolved successfully.")
        for name in WORLDPOP_REQUIRED:
            print(name, "->", assets[name]["href"])
        if args.metadata_only:
            return
        for name in WORLDPOP_REQUIRED:
            target = download_stream(assets[name]["href"], out/name)
            print("Downloaded:", target, "sha256:", sha256sum(target))
        return

    title = TITLES[args.dataset]
    service = resolve_arcgis_feature_service(title)
    layer = first_feature_layer(service["url"])
    print("Resolved:", title)
    print("ArcGIS item:", service["item_id"])
    print("Layer URL:", layer)
    if args.metadata_only:
        return

    if args.dataset == "settlement_extents" and not args.bbox:
        raise SystemExit("Settlement extents are large. Supply --bbox; national bulk download is intentionally blocked.")

    gj = query_feature_layer_geojson(layer, geometry=tuple(args.bbox) if args.bbox else None)
    target = out / f"{args.dataset}.geojson"
    target.write_text(json.dumps(gj), encoding="utf-8")
    print("Saved", len(gj["features"]), "features to", target)
    print("sha256:", sha256sum(target))

if __name__ == "__main__":
    main()
