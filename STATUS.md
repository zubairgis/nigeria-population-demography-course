# Repository status

This repository is in **Stage 1 — data foundation and pilot validation**.

As of 2026-09-30:
- the repository scaffold, source manifest, preparation scripts and instructor pilot notebook are on `main`;
- GitHub Actions run `36706549844` completed successfully and verified Python syntax plus live metadata access for the configured GRID3 State, LGA, Settlement Names, Settlement Extents v4.1 and Health Facilities v2.0 endpoints and the six required WorldPop 2025 R2025A filenames;
- no nationwide third-party dataset has been downloaded into or committed to this repository;
- no nationwide processing has been completed;
- no third-party national dataset has been uploaded to GitHub;
- the planned real pilot is Bayelsa State / Sagbama LGA;
- the **full pilot population/demographic aggregation has not yet been validated**, because that requires downloading and processing the six WorldPop rasters;
- entries marked `UNRESOLVED` in the manifest must be resolved before public redistribution or national packaging.

The next validation step is a Sagbama vector smoke test followed by the full instructor-notebook pilot. The seven-chapter student notebook remains intentionally blocked until the pilot validation gate passes.
