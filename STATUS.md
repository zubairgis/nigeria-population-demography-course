# Repository status

This repository is in **Stage 1 — data foundation and pilot validation**.

As of 2026-09-30:

- the repository scaffold, source manifest, preparation scripts and instructor pilot notebook are on `main`;
- live endpoint, Python syntax and real Sagbama vector smoke tests are passing;
- the live administrative data returned 37 State/FCT records, 774 LGA/Area Council records and 6 FCT Area Councils;
- Bayelsa uses source `statecode=BY`; Sagbama uses source `lgacode=6006`;
- the earlier Sagbama population/building validation results were produced before the settlement baseline was changed to GRID3 v3.1 and are therefore **superseded for teaching use**;
- fresh GRID3 v3.1 population, settlement-name, health-facility and building reconciliation workflows have been triggered and must pass before new numerical pilot results are recorded here;
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
