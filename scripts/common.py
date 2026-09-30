from __future__ import annotations
from pathlib import Path
import hashlib
import json
import requests

UA = "nigeria-population-demography-course/0.1"

def sha256sum(path: str | Path, chunk_size=1024*1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def get_json(url: str, params=None, timeout=120):
    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return r.json()

def arcgis_search_exact(title: str):
    data = get_json(
        "https://www.arcgis.com/sharing/rest/search",
        params={"f":"json", "num":100, "q":f'title:"{title}"'}
    )
    exact = [x for x in data.get("results", []) if x.get("title","").strip() == title]
    if not exact:
        raise RuntimeError(f"No exact ArcGIS item found for title: {title}")
    exact.sort(key=lambda x: (x.get("type") not in {"Feature Service","Feature Layer"}, not bool(x.get("url"))))
    return exact

def resolve_arcgis_feature_service(title: str):
    candidates = arcgis_search_exact(title)
    for item in candidates:
        item_id = item["id"]
        meta = get_json(f"https://www.arcgis.com/sharing/rest/content/items/{item_id}", params={"f":"json"})
        url = meta.get("url")
        if url and "FeatureServer" in url:
            return {"item_id": item_id, "url": url, "metadata": meta}
    raise RuntimeError(f"Exact title found but no FeatureServer URL resolved: {title}")

def first_feature_layer(service_url: str):
    info = get_json(service_url, params={"f":"json"})
    layers = info.get("layers", [])
    if not layers:
        raise RuntimeError(f"No layers found: {service_url}")
    return f"{service_url.rstrip('/')}/{layers[0]['id']}"

def query_feature_layer_geojson(layer_url: str, where="1=1", geometry=None, out_fields="*", page_size=1000):
    features = []
    offset = 0
    while True:
        params = {
            "f":"geojson",
            "where":where,
            "outFields":out_fields,
            "returnGeometry":"true",
            "outSR":"4326",
            "resultOffset":offset,
            "resultRecordCount":page_size,
        }
        if geometry is not None:
            xmin, ymin, xmax, ymax = geometry
            params.update({
                "geometry": f"{xmin},{ymin},{xmax},{ymax}",
                "geometryType":"esriGeometryEnvelope",
                "inSR":"4326",
                "spatialRel":"esriSpatialRelIntersects",
            })
        r = requests.get(f"{layer_url.rstrip('/')}/query", params=params, headers={"User-Agent":UA}, timeout=180)
        r.raise_for_status()
        gj = r.json()
        batch = gj.get("features", [])
        features.extend(batch)
        if len(batch) < page_size:
            break
        offset += len(batch)
    return {"type":"FeatureCollection", "features":features}

def download_stream(url: str, target: str | Path):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    headers = {"User-Agent":UA}
    mode = "wb"
    existing = tmp.stat().st_size if tmp.exists() else 0
    if existing:
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"
    with requests.get(url, stream=True, headers=headers, timeout=180) as r:
        if existing and r.status_code == 200:
            existing = 0
            mode = "wb"
        r.raise_for_status()
        with open(tmp, mode) as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
    tmp.replace(target)
    return target
