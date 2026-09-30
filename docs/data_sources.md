# Verified data inventory — starter assessment (2026-09-30)

## Recommended baseline

### Administrative boundaries
Use GRID3 Operational State and LGA Boundaries as the initial linked-dropdown source.
The LGA schema contains source codes (`statecode`, `lgacode`) in published copies,
which is preferable to matching by name alone. FCT is handled as first-level
selection and its Area Councils are represented at the LGA-equivalent level.

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
