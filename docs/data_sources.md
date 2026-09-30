# Verified data inventory — starter assessment (2026-09-30)

## Recommended baseline

### Administrative boundaries
Use **UN SALB Nigeria administrative units** as the primary State/FCT and LGA/Area
Council source. The official Nigeria SALB page identifies the dataset as
**Validated**, contributed by the **Office of the Surveyor General of the
Federation, Federal Surveys of Nigeria**, with temporal validity from
2000-01-01 to the current last update **2024-08-08**.

The validated course copy contains 37 ADM1 units and 774 ADM2 units in EPSG:4326.
Use stable SALB identifiers `adm1cd` and `adm2cd`, not names alone. FCT is
`NGA015` and contains six Area Councils.

The source national GeoJSON is archived in the repository as 37 unchanged
State/FCT partitions under
`data/boundaries/source/BNDA_NGA_2000-01-01_lastupdate/by_state/`. This avoids
geometry simplification and also lets the student notebook download only the
selected State/FCT.

GRID3 Operational State/LGA boundaries remain useful as an older comparison/
cross-check, but are no longer the primary administrative source.

SALB Terms of Use apply: non-commercial use, required attribution, and
restrictions on changing source geometry/content. Derived products may aggregate
SALB data and add attributes when the required SALB/Contributor credit is kept.

### Population and demographics
Use one WorldPop family:
**Global2 / R2025A v1 / 2025 / constrained / 100 m age-sex**.

Required rasters:
- total male (`T_M`)
- total female (`T_F`)
- male age 0 to <1 (`m_00`)
- female age 0 to <1 (`f_00`)
- male age 1 to <5 (`m_01`)
- female age 1 to <5 (`f_01`)

Derived:
- total = T_M + T_F
- under-1 = m_00 + f_00
- under-5 = m_00 + f_00 + m_01 + f_01

This keeps totals and demographic components inside the same release/model family.

### Settlements
Use GRID3 Settlement Extents v4.1 only after exact v4.1 licence/release notes
have been captured. The current live table exposes `block_id`, `building_count`,
`extent_type` and other metrics.

Use GRID3 Settlement Names as a separate point layer. A name is attached only
when a defensible relationship exists. Unmatched extents keep their settlement/
block ID. Multiple contained names remain multiple/ambiguous rather than being
silently collapsed.

### Buildings
Google Open Buildings V3 is a valid raw footprint source, but national raw
footprints must remain source-hosted. Instructor processing should work tile by
tile or through Earth Engine. A confidence threshold and the date/freshness
limitations must be recorded.

For the first pilot, the GRID3 v4.1 `building_count` field may be inspected as
an interim teaching metric, but it should not replace explicit footprint
provenance until v4.1 methodology is verified.

### Health facilities
Use GRID3 Health Facilities v2.0 as the first **nationally consistent** baseline.
As of the 2026-08 GRID3 Nigeria page, v3.0 covers only 24 states. v2.0 covers all
states and incorporates NHFR 2024 inputs plus GRID3 updates.

The current federal NHFR also exposes a read-only API, but it requires an API
key. Do not embed that key in notebooks or repositories.

## Unresolved before public national release

1. Exact licence and release documentation for Settlement Extents v4.1.
2. Exact current v3.0 health-facility item/terms if v3 is later adopted.
3. Settlement-name-to-v4.1 block relationship and ambiguity rate.
4. Pilot evidence that source administrative codes remain stable and unique.
5. Pilot measurement of state-package size and national processing cost.
