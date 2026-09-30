# Repository status

This repository is in **Stage 1 — data foundation and pilot validation**.

As of 2026-09-30:
- the repository scaffold, source manifest, preparation scripts and instructor pilot notebook are on `main`;
- GitHub Actions run `36706549844` passed Python syntax and live endpoint checks;
- GitHub Actions run `36706846970` passed an **actual Sagbama vector download smoke test**;
- the live administrative data returned 37 State/FCT records, 774 LGA/Area Council records and 6 FCT Area Councils;
- Bayelsa uses source `statecode=BY`; Sagbama uses source `lgacode=6006`;
- the Sagbama WGS84 bounding-box download returned 6,820 settlement-extents records, 836 settlement-name points and 300 health-facility points; these bbox records are subsequently clipped/assigned to the exact LGA in the instructor workflow;
- no nationwide third-party dataset has been downloaded into or committed to this repository;
- no nationwide processing has been completed and no third-party national dataset has been uploaded to GitHub;
- the **full pilot population/demographic aggregation is still pending**, because it requires downloading and processing the six WorldPop rasters;
- the exact Settlement Extents v4.1 redistribution licence is still unresolved, so v4.1-derived data must not be published as repository/release assets yet.

The next validation step is the full Sagbama WorldPop population/demographic pilot. The seven-chapter student notebook remains intentionally blocked until the pilot validation gate passes.
