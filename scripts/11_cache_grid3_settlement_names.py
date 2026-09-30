from __future__ import annotations
import json, re, shutil
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from common import query_feature_layer_geojson, sha256sum

ENDPOINTS = json.loads((REPO_ROOT / "config/source_endpoints.json").read_text())
LAYER = ENDPOINTS["grid3_settlement_names"]["layer_url"]
OUT_ROOT = REPO_ROOT / "data" / "settlement_names"
NATIONAL = OUT_ROOT / "GRID3_NGA_settlement_names.geojson"
BY_STATE = OUT_ROOT / "by_state"

def safe(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(s)).strip("_")

def main():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    if BY_STATE.exists():
        shutil.rmtree(BY_STATE)
    BY_STATE.mkdir(parents=True, exist_ok=True)

    gj = query_feature_layer_geojson(LAYER, page_size=2000)
    feats = gj.get("features", [])
    if not feats:
        raise RuntimeError("GRID3 Settlement Names query returned no features.")

    fields = set().union(*(f.get("properties", {}).keys() for f in feats[:200]))
    required = {"set_id", "set_name"}
    missing = required - fields
    if missing:
        raise RuntimeError(f"Missing expected GRID3 Settlement Names fields: {sorted(missing)}")

    compact = json.dumps({"type":"FeatureCollection","features":feats}, separators=(",",":"))
    NATIONAL.write_text(compact, encoding="utf-8")
    national_bytes = NATIONAL.stat().st_size

    mode = "national"
    manifest = []

    # GitHub's normal file limit is 100 MB. Keep a safety margin.
    if national_bytes >= 90_000_000:
        NATIONAL.unlink()
        mode = "by_state"
        groups = {}
        for f in feats:
            p = f.get("properties", {})
            state = p.get("statename") or p.get("state") or "UNKNOWN"
            groups.setdefault(str(state), []).append(f)
        for state, fs in sorted(groups.items()):
            fn = f"{safe(state)}.geojson"
            path = BY_STATE / fn
            path.write_text(
                json.dumps({"type":"FeatureCollection","features":fs}, separators=(",",":")),
                encoding="utf-8"
            )
            manifest.append({
                "statename": state,
                "file": f"by_state/{fn}",
                "feature_count": len(fs),
                "size_bytes": path.stat().st_size,
                "sha256": sha256sum(path),
            })
    else:
        shutil.rmtree(BY_STATE)
        manifest.append({
            "statename": "ALL_NIGERIA",
            "file": NATIONAL.name,
            "feature_count": len(feats),
            "size_bytes": national_bytes,
            "sha256": sha256sum(NATIONAL),
        })

    (OUT_ROOT / "manifest.json").write_text(
        json.dumps({
            "dataset":"GRID3 NGA Settlement Names",
            "source_layer":LAYER,
            "licence":"CC BY 4.0",
            "storage_mode":mode,
            "feature_count":len(feats),
            "files":manifest,
        }, indent=2),
        encoding="utf-8"
    )

    print("GRID3 settlement-name features:", len(feats))
    print("Storage mode:", mode)
    for x in manifest[:5]:
        print(x)

if __name__ == "__main__":
    main()
