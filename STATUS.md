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
- GRID3 NGA Settlement Extents **v3.1** has now been selected as the settlement baseline;
- the official HDX v3.1 GeoPackage ZIP is mirrored as a versioned GitHub Release asset rather than committed to Git history;
- no nationwide processing has yet been completed; raw national rasters and building footprints remain source-hosted.

## Current decision

Use **GRID3 NGA Settlement Extents v3.1** for settlement polygons in this course.
The v3.1 licence is verified as CC BY-SA 4.0, so the official ZIP may be mirrored
to a GitHub Release with attribution and share-alike terms.

The preparation workflow is version-locked to v3.1. It no longer assumes the
v4.x `block_id` schema; it validates the documented v3.1 fields and creates a
deterministic geometry-based source identifier for processing.

National raw population rasters and Google Open Buildings remain source-hosted.
