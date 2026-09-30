# Estimating Population and Demographic Characteristics in Nigeria Using Google Colab

Repository foundation for a beginner-friendly Moodle + Google Colab course.

## Intended final system

A student will select a Nigerian State/FCT and then an LGA/Area Council using stable identifiers. The notebook will display the administrative boundary and provide modelled estimates of total population, male population, female population, children under 1 year, and children under 5 years; settlement extents/names where defensible; detected-building counts; health-facility locations and summaries; and downloadable maps/tables.

## Current stage

**Stage 1 — data foundation.** Do not treat this repository as nationally ready yet.

1. Verify source metadata, schemas, licences and access methods.
2. Build and validate a Bayelsa/Sagbama pilot.
3. Measure storage and processing requirements.
4. Package state-level teaching assets.
5. Only then create the seven-chapter student notebook and Moodle pages.

See `STATUS.md`.

## Scientific rules

- Population rasters are treated according to their documented units. Count rasters are not confused with density.
- The planned primary demographic family is WorldPop Global2 R2025A v1, 2025, 100 m constrained age-sex data.
- Under-1 = age 0 to <1 year.
- Under-5 = under-1 plus ages 1 to <5 years.
- Under-1 is a subset of under-5 and is never added to under-5 as a separate population group.
- Settlement extents are mapped settlement extents, not official community boundaries.
- Building footprints are detections, not households or occupied dwellings.
- Health-facility presence does not imply operational status or service availability.
- Exact/fractional raster-polygon aggregation is preferred over `all_touched=True`.

## Repository layout

```text
README.md
STATUS.md
LICENSE
CITATION.cff
requirements.txt
.gitignore
THIRD_PARTY_DATA.md
docs/
config/
data/
scripts/
notebooks/
checks/
```

## First run

```bash
python -m pip install -r requirements.txt
python scripts/01_download_sources.py --help
python scripts/02_validate_boundaries.py --help
```

For Colab/instructor use, open `notebooks/00_Prepare_Nigeria_Data.ipynb`.

## GitHub storage policy

Git history is for code, documentation, manifests, small lookup tables, compact boundaries and a small validated pilot. Raw national rasters and national building footprints remain source-hosted. Processed state teaching packages may later be attached to versioned GitHub Releases when each asset is comfortably below GitHub's release-asset limit and the dataset licence permits redistribution.
