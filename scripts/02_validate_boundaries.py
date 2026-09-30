from __future__ import annotations
import argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd

def choose(cols, candidates, label):
    for c in candidates:
        if c in cols:
            return c
    raise ValueError(f"Could not find {label}. Available columns: {list(cols)}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--states", required=True)
    p.add_argument("--lgas", required=True)
    p.add_argument("--out-dir", default="data/lookups")
    args = p.parse_args()

    states = gpd.read_file(args.states)
    lgas = gpd.read_file(args.lgas)

    if states.crs is None or lgas.crs is None:
        raise ValueError("Boundary CRS must be present.")
    states = states.to_crs(4326)
    lgas = lgas.to_crs(4326)

    for name, gdf in [("states",states),("lgas",lgas)]:
        if gdf.empty:
            raise ValueError(f"{name} is empty.")
        bad = ~gdf.geometry.is_valid
        if bad.any():
            raise ValueError(f"{name}: {bad.sum()} invalid geometries; inspect before continuing.")

    state_name = choose(states.columns, ["statename","state_name","state"], "state name")
    state_code = choose(states.columns, ["statecode","state_code","uniq_id"], "state code")
    lga_name = choose(lgas.columns, ["lganame","lga_name","lga"], "LGA name")
    lga_code = choose(lgas.columns, ["lgacode","lga_code","uniq_id"], "LGA code")
    lga_state_name = choose(lgas.columns, ["statename","state_name","state"], "LGA state name")
    lga_state_code = choose(lgas.columns, ["statecode","state_code"], "LGA state code")

    if states[state_code].astype(str).duplicated().any():
        raise ValueError("State codes are not unique.")
    if lgas[lga_code].astype(str).duplicated().any():
        raise ValueError("LGA codes are not unique.")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    states_df = states[[state_code,state_name]].copy()
    states_df.columns = ["state_id","state_name"]
    states_df["source_dataset_id"] = "grid3_state_boundaries"
    states_df.sort_values("state_name").to_csv(out/"states.csv", index=False)

    lgas_df = lgas[[lga_code,lga_name,lga_state_code,lga_state_name]].copy()
    lgas_df.columns = ["lga_id","lga_name","state_id","state_name"]
    lgas_df["source_dataset_id"] = "grid3_lga_boundaries"
    lgas_df.sort_values(["state_name","lga_name"]).to_csv(out/"lgas.csv", index=False)

    fct = lgas_df[lgas_df["state_name"].astype(str).str.contains("FCT|Abuja", case=False, regex=True)]
    print("States:", len(states_df))
    print("LGAs/Area Councils:", len(lgas_df))
    print("FCT-equivalent records:", len(fct))
    print(fct.to_string(index=False))
    print("Wrote:", out/"states.csv", "and", out/"lgas.csv")

if __name__ == "__main__":
    main()
