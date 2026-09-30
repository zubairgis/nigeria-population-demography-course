# Updating the data foundation

1. Revisit each official source page.
2. Record release/version/reference year separately.
3. Re-check licence and redistribution terms for the exact version.
4. Update the manifest before downloading.
5. Download to `data/raw/` or `downloads/` (both ignored by Git).
6. Calculate SHA-256 for every downloaded source file.
7. Validate CRS, schema, feature counts, geometry and raster units.
8. Re-run the pilot.
9. Compare results and package sizes with the previous release.
10. Only publish a new GitHub Release after validation passes.
