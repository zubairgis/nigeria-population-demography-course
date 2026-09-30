from __future__ import annotations
import argparse, json
from pathlib import Path
from common import query_feature_layer_geojson, get_json, download_stream, sha256sum

REPO_ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS_FILE = REPO_ROOT / "config" / "source_endpoints.json"

DATASET_KEYS = {
    "state_boundaries": "grid3_state_boundaries",
    "lga_boundaries": "grid3_lga_boundaries",
    "settlement_names": "grid3_settlement_names",
    "settlement_extents": "grid3_settlement_extents_v4_1",
    "health_v2": "grid3_health_facilities_v2",
}

WORLDPOP_BASE = (
    "https://data.worldpop.org/GIS/AgeSex_structures/Global_2015_2030/"
    "R2025A/2025/NGA/v1/100m/constrained"
)
WORLDPOP_REQUIRED = [
    "nga_T_M_2025_CN_100m_R2025A_v1.tif",
    "nga_T_F_2025_CN_100m_R2025A_v1.tif",
    "nga_m_00_2025_CN_100m_R2025A_v1.tif",
    "nga_f_00_2025_CN_100m_R2025A_v1.tif",
    "nga_m_01_2025_CN_100m_R2025A_v1.tif",
    "nga_f_01_2025_CN_100m_R2025A_v1.tif",
]

def load_endpoints():
    if not ENDPOINTS_FILE.exists():
        raise FileNotFoundError(f"Missing endpoint registry: {ENDPOINTS_FILE}")
    return json.loads(ENDPOINTS_FILE.read_text(encoding="utf-8"))

def validate_arcgis_layer(layer_url: str):
    info = get_json(layer_url, params={"f":"json"})
    if "error" in info:
        raise RuntimeError(f"ArcGIS layer error: {info['error']}")
    if info.get("type") != "Feature Layer":
        raise RuntimeError(f"Expected a Feature Layer, got: {info.get('type')}")
    sr = (info.get("extent") or {}).get("spatialReference", {})
    print("Layer:", info.get("name"))
    print("Geometry:", info.get("geometryType"))
    print("CRS WKID:", sr.get("latestWkid") or sr.get("wkid"))
    print("Max record count:", info.get("maxRecordCount"))
    return info

def worldpop_urls():
    return {name: f"{WORLDPOP_BASE}/{name}" for name in WORLDPOP_REQUIRED}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=list(DATASET_KEYS) + ["worldpop_core"], required=True)
    p.add_argument("--output", default="downloads")
    p.add_argument("--bbox", nargs=4, type=float, metavar=("XMIN","YMIN","XMAX","YMAX"))
    p.add_argument("--metadata-only", action="store_true")
    args = p.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    if args.dataset == "worldpop_core":
        urls = worldpop_urls()
        print("Verified WorldPop 2025 R2025A 100 m directory:")
        print(WORLDPOP_BASE)
        for name, url in urls.items():
            print(name, "->", url)
        if args.metadata_only:
            return
        for name, url in urls.items():
            target = download_stream(url, out / name)
            print("Downloaded:", target, "sha256:", sha256sum(target))
        return

    endpoints = load_endpoints()
    key = DATASET_KEYS[args.dataset]
    record = endpoints[key]
    layer_url = record["layer_url"]

    print("Dataset key:", key)
    print("ArcGIS item:", record.get("item_id") or "not recorded")
    print("Layer URL:", layer_url)
    validate_arcgis_layer(layer_url)

    if args.metadata_only:
        return

    if args.dataset == "settlement_extents" and not args.bbox:
        raise SystemExit(
            "Settlement extents are very large. Supply --bbox; "
            "national bulk download is intentionally blocked."
        )

    gj = query_feature_layer_geojson(
        layer_url,
        geometry=tuple(args.bbox) if args.bbox else None
    )
    target = out / f"{args.dataset}.geojson"
    target.write_text(json.dumps(gj), encoding="utf-8")
    print("Saved", len(gj["features"]), "features to", target)
    print("sha256:", sha256sum(target))

if __name__ == "__main__":
    main()
