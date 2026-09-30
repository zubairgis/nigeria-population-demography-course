from __future__ import annotations
import json, re, subprocess, shutil
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PBF_URL="https://download.geofabrik.de/africa/nigeria-latest.osm.pbf"
TMP=ROOT/"_drainage_cache_tmp"
OUT=ROOT/"data/drainage/by_state"
META=ROOT/"data/drainage"

def safe(s):
    return re.sub(r"[^A-Za-z0-9]+","_",str(s)).strip("_")

def main():
    TMP.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    pbf=TMP/"nigeria-latest.osm.pbf"
    filtered=TMP/"nigeria-waterways.osm.pbf"
    geojson=TMP/"nigeria-waterways.geojson"

    if not pbf.exists():
        subprocess.run(["curl","-L","--retry","4","--fail","-o",str(pbf),PBF_URL],check=True)

    subprocess.run([
        "osmium","tags-filter",str(pbf),
        "w/waterway=river,stream,canal,drain",
        "-o",str(filtered),"--overwrite"
    ],check=True)

    subprocess.run([
        "osmium","export",str(filtered),
        "-f","geojson",
        "-o",str(geojson),
        "--geometry-types=linestring",
        "--overwrite"
    ],check=True)

    water=gpd.read_file(geojson).to_crs(4326)
    if water.empty:
        raise RuntimeError("No OSM waterway features were extracted.")

    # Normalize the class field from OSM tags.
    if "waterway" not in water.columns:
        raise RuntimeError(f"Expected 'waterway' field missing. Fields: {list(water.columns)}")
    water=water[water["waterway"].isin(["river","stream","canal","drain"])].copy()
    keep=[c for c in ["osm_id","name","waterway","geometry"] if c in water.columns]
    water=water[keep]

    admin_dir=ROOT/"data/boundaries/source/BNDA_NGA_2000-01-01_lastupdate/by_state"
    records=[]
    for state_file in sorted(admin_dir.glob("*.geojson")):
        adm=gpd.read_file(state_file).to_crs(4326)
        state_name=str(adm.iloc[0]["adm1nm"])
        state_id=str(adm.iloc[0]["adm1cd"])
        state_geom=adm.geometry.union_all()

        # spatial subset then exact state clip
        cand=water[water.intersects(state_geom)].copy()
        if len(cand):
            cand=gpd.clip(cand,gpd.GeoDataFrame(geometry=[state_geom],crs=4326))
            cand=cand[~cand.geometry.is_empty].copy()

        target=OUT/f"{state_id}_{safe(state_name)}_drainage.geojson"
        cand.to_file(target,driver="GeoJSON")

        records.append({
            "adm1cd":state_id,
            "adm1nm":state_name,
            "file":f"by_state/{target.name}",
            "feature_count":int(len(cand))
        })
        print(state_id,state_name,len(cand))

    (META/"manifest.json").write_text(json.dumps({
        "dataset":"OpenStreetMap waterways for Nigeria",
        "source":"Geofabrik Nigeria latest OSM extract",
        "source_url":PBF_URL,
        "classes":["river","stream","canal","drain"],
        "licence":"OpenStreetMap data © OpenStreetMap contributors, ODbL 1.0",
        "states":records
    },indent=2),encoding="utf-8")

if __name__=="__main__":
    main()
