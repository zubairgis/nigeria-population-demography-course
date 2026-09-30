# Nigeria administrative boundary source archive

Source file supplied for the course on 2026-09-30: `BNDA_NGA_2000-01-01_lastupdate.geojson`.

## Validation before ingestion
- 774 ADM2 features
- 37 ADM1 units
- CRS EPSG:4326
- 759 Polygon and 15 MultiPolygon geometries
- 0 invalid, empty or null geometries
- 774 unique `adm2cd` values
- Nigeria / NGA throughout
- FCT has 6 Area Councils
- Bayelsa has 8 LGAs
- Sagbama source code: `NGA006006`
- Original size: 5,639,266 bytes
- Original SHA-256: `a67a3add567c5ee1ee7bc8411992b385c589d2c1d0294fe3487d8bb1bccecbe0`

## Storage
The original national file exceeded the connected upload transport body limit. It is stored here as **37 logical State/FCT partitions**, preserving all 774 original features without geometry simplification or attribute edits. This is also the preferred teaching architecture because Colab can download only the selected State/FCT.

## Name QA
Raw source names are deliberately preserved. Some source strings need separate UI normalization, including examples `Akwa lbom`, `Nassarawa`, `Yenegoa`, and `Aiyekire\r\n`. Do not silently overwrite raw fields.

## Provenance/licence
The GeoJSON itself does not embed a licence statement or complete provider metadata. Record the exact official landing page, release/update metadata and redistribution terms in the dataset manifest before publishing redistributed course data or derivatives.
