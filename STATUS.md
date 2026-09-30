# Repository status

This repository is in **Stage 1 — data foundation and pilot validation**.

As of 2026-09-30:

- the repository scaffold, source manifest, preparation scripts and instructor pilot notebook are on `main`;
- live endpoint, Python syntax and real Sagbama vector smoke tests are passing;
- the live administrative data returned 37 State/FCT records, 774 LGA/Area Council records and 6 FCT Area Councils;
- Bayelsa uses source `statecode=BY`; Sagbama uses source `lgacode=6006`;
- the full Sagbama WorldPop population/demographic pilot **PASSED** in GitHub Actions run `36707350042`;
- six WorldPop 2025 R2025A constrained 100 m age-sex rasters (about 940.3 MB total) were resolved and processed without raster resampling;
- Sagbama modelled 2025 population was 183,450.83 people: 93,309.96 male and 90,140.87 female;
- estimated under-one population was 4,324.76 and estimated under-five population was 20,507.90;
- fractional-overlap aggregation placed 154,091.49 people (84.00%) inside mapped settlement components and 29,359.34 outside them;
- 832 settlement components were analysed; 90 had one contained settlement-name point, 57 had multiple contained name points, and 685 had no contained name point;
- 53 deduplicated/coordinate-valid health-facility points were strictly inside the Sagbama LGA boundary;
- the Google Open Buildings v3 Sagbama pilot **PASSED** in GitHub Actions run `36709066830`;
- 13,638 detected building footprints passed the documented Google precision-threshold policy; 13,578 were allocated exactly once to mapped settlement components and 60 remained inside the LGA but outside mapped settlement components;
- no nationwide third-party dataset has been downloaded into or committed to this repository;
- no nationwide processing has been completed and no third-party national dataset has been uploaded to GitHub.

## Current decision

The **analytical Sagbama pilot has passed** the main boundary, population, demographic, settlement, building and health-facility validation checks.

Public packaging remains deliberately blocked because the exact redistribution licence for **GRID3 NGA Settlement Extents v4.1** has not yet been verified from the exact v4.1 metadata/release notes. GRID3 Settlement Extents v4.0 is documented as CC BY-SA 4.0, but that licence is not being silently transferred to v4.1.

Until the v4.1 licence is confirmed:
- do not publish v4.1-derived settlement geometries as repository or release assets;
- keep raw national third-party data source-hosted;
- continue developing code, manifests, validation summaries and non-redistributed instructor workflows.

See `checks/pilot_validation_2026-09-30.md` for the evidence summary.
