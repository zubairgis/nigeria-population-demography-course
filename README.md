# Estimating Population and Demographic Characteristics in Nigeria Using Google Colab

Repository foundation for a beginner-friendly Moodle + Google Colab course.

## Intended final system

A student will select a Nigerian State/FCT and then an LGA/Area Council using stable identifiers. The notebook will display the administrative boundary and provide modelled estimates of total population, male population, female population, children under 1 year, and children under 5 years; settlement extents/names where defensible; detected-building counts; health-facility locations and summaries; and downloadable maps/tables.

## Current stage

**Stage 2 — validated pilot plus student notebook development.** The Bayelsa/Sagbama validation gate has passed and the seven-chapter student notebook is now available. National teaching packages are still being optimized.

1. Verify source metadata, schemas, licences and access methods.
2. Build and validate a Bayelsa/Sagbama pilot.
3. Measure storage and processing requirements.
4. Package state-level teaching assets.
5. Only then create the seven-chapter student notebook and Moodle pages.

See `STATUS.md` and `checks/validation_summary.csv`.

## Instructor pilot notebook

Open the preparation notebook directly in Google Colab:

https://colab.research.google.com/github/zubairgis/nigeria-population-demography-course/blob/main/notebooks/00_Prepare_Nigeria_Data.ipynb

The notebook is intended for the instructor/data-preparation stage. It downloads only documented sources, builds the Bayelsa → Sagbama pilot, applies fractional-overlap WorldPop aggregation, checks settlement-name matching and health facilities, performs settlement/LGA reconciliation, and creates a pilot ZIP.

Open the seven-chapter student notebook directly in Google Colab:

https://colab.research.google.com/github/zubairgis/nigeria-population-demography-course/blob/main/notebooks/01_Population_Demography_7_Chapters.ipynb

It uses the validated SALB State/LGA lookup, GRID3 Settlement Extents v3.1, WorldPop 2025 R2025A, Google Open Buildings V3, and GRID3/NHFR health-facility workflow.

## Scientific rules

- Population rasters are treated according to their documented units. Count rasters are not confused with density.
- The planned primary demographic family is WorldPop Global2 R2025A v1, 2025, 100 m constrained age-sex data.
- Under-1 = age 0 to <1 year.
- Under-5 = under-1 plus ages 1 to <5 years.
- Under-1 is a subset of under-5 and is never added to under-5 as a separate population group.
- Settlement extents use **GRID3 NGA Settlement Extents v3.1** (CIESIN/GRID3, 2024; CC BY-SA 4.0) and are mapped settlement extents, not official community boundaries.
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

## Automated checks

- `Validate data foundation`: compiles the preparation scripts and checks the configured live data endpoints.
- `Sagbama vector smoke test`: downloads real small vector subsets for the pilot and verifies expected national counts, FCT handling, pilot identifiers and key source fields. Smoke-test downloads are temporary workflow artifacts, not committed third-party data.

## GitHub storage policy

Git history is for code, documentation, manifests, small lookup tables, compact boundaries and a small validated pilot. Raw national rasters and national building footprints remain source-hosted. The official GRID3 NGA Settlement Extents v3.1 GeoPackage ZIP is stored as a **versioned GitHub Release asset** (not in Git history) because its CC BY-SA 4.0 terms permit redistribution with attribution/share-alike. Course preparation code downloads the mirrored GitHub asset, while HDX remains the authoritative provenance source. Processed state teaching packages may also be attached to versioned GitHub Releases when appropriate.
