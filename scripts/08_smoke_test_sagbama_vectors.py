from __future__ import annotations
import json
import requests
from pathlib import Path
from common import query_feature_layer_geojson

REPO_ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = json.loads((REPO_ROOT / "config/source_endpoints.json").read_text(encoding="utf-8"))

def props(fc):
    return [f.get("properties", {}) for f in fc.get("features", [])]

def geometry_bbox(geometry):
    coords = geometry.get("coordinates")
    xy = []
    def walk(x):
        if isinstance(x, (list, tuple)):
            if len(x) >= 2 and all(isinstance(v, (int, float)) for v in x[:2]):
                xy.append((float(x[0]), float(x[1])))
            else:
                for v in x:
                    walk(v)
    walk(coords)
    if not xy:
        raise ValueError("Could not derive bounding box from geometry.")
    xs, ys = zip(*xy)
    return min(xs), min(ys), max(xs), max(ys)

def require_fields(records, fields, label):
    if not records:
        raise ValueError(f"{label}: no records returned")
    available = set().union(*(r.keys() for r in records[:50]))
    missing = [f for f in fields if f not in available]
    if missing:
        raise ValueError(f"{label}: missing expected fields {missing}; available sample fields: {sorted(available)}")

def main():
    out_dir = REPO_ROOT / "checks" / "smoke_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    state_url = ENDPOINTS["grid3_state_boundaries"]["layer_url"]
    lga_url = ENDPOINTS["grid3_lga_boundaries"]["layer_url"]
    settlements_record = ENDPOINTS["grid3_settlement_extents_v3_1"]
    names_url = ENDPOINTS["grid3_settlement_names"]["layer_url"]
    health_url = ENDPOINTS["grid3_health_facilities_v2"]["layer_url"]

    states = query_feature_layer_geojson(state_url)
    state_records = props(states)
    require_fields(state_records, ["statename", "statecode"], "State boundaries")
    if len(state_records) != 37:
        raise ValueError(f"Expected 37 State/FCT records, got {len(state_records)}")

    lgas = query_feature_layer_geojson(lga_url)
    lga_records = props(lgas)
    require_fields(lga_records, ["lganame", "lgacode", "statename", "statecode"], "LGA boundaries")
    if len(lga_records) != 774:
        raise ValueError(f"Expected 774 LGA/Area Council records, got {len(lga_records)}")

    fct = [
        r for r in lga_records
        if any(term in str(r.get("statename", "")).casefold()
               for term in ("fct", "federal capital", "abuja"))
    ]
    if len(fct) != 6:
        raise ValueError(
            f"Expected 6 FCT Area Councils, got {len(fct)}. "
            f"Observed state names: {sorted(set(str(r.get('statename')) for r in fct))}"
        )

    sagbama_features = [
        f for f in lgas["features"]
        if str(f.get("properties", {}).get("statename", "")).casefold() == "bayelsa"
        and str(f.get("properties", {}).get("lganame", "")).casefold() == "sagbama"
    ]
    if len(sagbama_features) != 1:
        raise ValueError(f"Expected exactly one Bayelsa/Sagbama feature, got {len(sagbama_features)}")
    sagbama = sagbama_features[0]
    bbox = geometry_bbox(sagbama["geometry"])
    lga_id = str(sagbama["properties"]["lgacode"])
    state_id = str(sagbama["properties"]["statecode"])

    # GRID3 v3.1 is distributed as an official HDX GeoPackage ZIP rather than
    # the v4.x ArcGIS feature layer. Verify that the selected resource is reachable
    # without downloading the full national archive during this lightweight smoke test.
    download_url = settlements_record["download_url"]
    with requests.get(
        download_url,
        stream=True,
        allow_redirects=True,
        timeout=60,
        headers={"User-Agent": "nigeria-population-demography-course/1.0", "Range": "bytes=0-0"},
    ) as response:
        if response.status_code not in (200, 206):
            raise ValueError(
                f"GRID3 Settlement Extents v3.1 HDX resource returned HTTP {response.status_code}"
            )
        content_length = response.headers.get("Content-Length")
        content_type = response.headers.get("Content-Type", "")
        settlement_source_check = {
            "status_code": response.status_code,
            "content_length_header": content_length,
            "content_type": content_type,
            "doi": settlements_record["doi"],
            "resource_page": settlements_record["resource_page"],
        }

    names_fc = query_feature_layer_geojson(names_url, geometry=bbox)
    name_records = props(names_fc)
    require_fields(name_records, ["set_id", "set_name", "lganame", "lgacode"], "Settlement Names")

    health_fc = query_feature_layer_geojson(health_url, geometry=bbox)
    health_records = props(health_fc)
    require_fields(
        health_records,
        ["globalid", "nhfr_uid", "facility_name", "ownership", "facility_level", "latitude", "longitude"],
        "Health Facilities v2.0"
    )

    # Preserve smoke-test downloads as transient CI artifacts; do not commit third-party data.
    for name, fc in [
        ("states.geojson", states),
        ("lgas.geojson", lgas),
        ("sagbama_settlement_names_bbox.geojson", names_fc),
        ("sagbama_health_facilities_bbox.geojson", health_fc),
    ]:
        (out_dir / name).write_text(json.dumps(fc), encoding="utf-8")

    summary = {
        "status": "PASS",
        "state_fct_records": len(state_records),
        "lga_area_council_records": len(lga_records),
        "fct_area_councils": len(fct),
        "pilot_state": "Bayelsa",
        "pilot_lga": "Sagbama",
        "statecode": state_id,
        "lgacode": lga_id,
        "pilot_bbox_wgs84": bbox,
        "settlement_extent_source": "GRID3 NGA Settlement Extents v3.1",
        "settlement_extent_resource_check": settlement_source_check,
        "settlement_name_bbox_records": len(name_records),
        "health_facility_bbox_records": len(health_records),
        "note": "Boundary/name/health bbox records are smoke tests. GRID3 v3.1 settlement extents are supplied as the official HDX GeoPackage ZIP and are clipped locally in the preparation workflow."
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
