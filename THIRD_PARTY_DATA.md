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
- GRID3 Settlement Extents v4.0: exact ArcGIS metadata inspected on 2026-09-30
  states **CC BY-SA 4.0** and requires derivative distribution to maintain the
  same terms.
- GRID3 Settlement Extents v4.1: the GRID3 Nigeria catalogue identifies v4.1
  (August 2026) as the current release, but the exact v4.1-specific licence text
  has not yet been captured from its metadata/release notes.

Therefore **do not publicly redistribute v4.1 or v4.1-derived settlement
geometry until the exact v4.1 terms are verified**.

Do not copy a licence from an older release onto a newer release merely because
the titles, publisher or methodology are similar.
