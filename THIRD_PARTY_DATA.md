# Third-party data

The repository's MIT licence does **not** relicense third-party data.

Before placing any dataset or derived dataset in a public GitHub repository or
GitHub Release, check the exact licence/version recorded in
`config/dataset_manifest.csv`.

Current working choices:

- **UN SALB Nigeria Administrative Units (current through 2024-08-08)**:
  copyright is vested in the United Nations under the SALB Terms of Use. The
  Nigeria contributor is the Office of the Surveyor General of the Federation,
  Federal Surveys of Nigeria. SALB Data may be used for **non-commercial
  purposes**; required source credit must include **“from SALB Data, United
  Nations”** and the contributor. Users are prohibited from changing source
  geometry/content without contributor consent. SALB-derived products may add
  attributes and aggregate original SALB data when the required credit is kept.
  The repository stores the 774 source ADM2 features as 37 unchanged State/FCT
  partitions; the root MIT licence does not apply to these data files.


- GRID3 Operational State Boundaries: CC BY 4.0 according to source metadata.
- GRID3 Operational LGA Boundaries: CC BY 4.0 according to source metadata.
- GRID3 Settlement Names: CC BY 4.0 according to source metadata.
- WorldPop Global2 R2025A v1: CC BY 4.0 according to the WorldPop data page.
- Google Open Buildings V3: dual licensed CC BY 4.0 / ODbL 1.0; this project
  plans to use the CC BY 4.0 route unless another downstream dataset requires
  ODbL compatibility.
- GRID3 Health Facilities v2.0: CC BY 4.0 according to its current metadata.
- **GRID3 NGA - Settlement Extents v3.1**: selected settlement baseline for this
  course. CIESIN/GRID3, 2024. DOI: https://doi.org/10.7916/x9xg-e262.
  The official metadata states **CC BY-SA 4.0**. The v3.1 product family includes settlement polygons and a settled-grid product. The
  selected HDX resource `GRID3_NGA_settlement_extents_v3_1_gpkg.zip` contains the
  settlement-extents GeoPackage, XML metadata and the data-release-notes PDF.
  Redistribution is permitted with attribution and share-alike terms.
  Official HDX dataset page:
  https://data.humdata.org/dataset/grid3-nga-settlement-extents-v3_1
  Official resource:
  https://data.humdata.org/dataset/grid3-nga-settlement-extents-v3_1/resource/0a22d6fc-7f1f-4f50-aead-09ef7be0455d

The root MIT licence does **not** apply to the GRID3 v3.1 data. Any mirrored or
derived settlement geometry must retain the GRID3/CIESIN attribution and
CC BY-SA 4.0 terms.
