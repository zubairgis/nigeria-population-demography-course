# Sagbama pilot validation — 2026-09-30

## Scope

Pilot area:
- State: Bayelsa (`statecode=BY`)
- LGA: Sagbama (`lgacode=6006`)
- LGA bounding box used for source subsetting: 5.9598651°E, 4.8132629°N to 6.5696321°E, 5.3805661°N

This document summarizes validation evidence only. It does not redistribute raw WorldPop, GRID3 or Google Open Buildings source data.

## 1. Administrative and vector-source validation

The real vector smoke test verified:
- 37 State/FCT records;
- 774 LGA/Area Council records;
- 6 FCT Area Councils;
- correct Bayelsa and Sagbama source identifiers;
- live retrieval of settlement extents, settlement-name points and health-facility points for the pilot area.

## 2. Population and demographic pilot

GitHub Actions run: **36707350042**  
Result: **PASS**

Six compatible WorldPop 2025 R2025A constrained 100 m age-sex rasters were downloaded and processed:
- total male;
- total female;
- male age 0 to <1;
- female age 0 to <1;
- male age 1 to <5;
- female age 1 to <5.

Total download size: **940,306,608 bytes**.

All six rasters used:
- CRS: EPSG:4326;
- pixel size: 0.00083333333 degrees;
- data type: float32;
- NoData: -99999.

Population aggregation used exactextract fractional cell-overlap sums. No raster resampling was applied.

### LGA estimates

| Metric | Estimate |
|---|---:|
| Total population | 183,450.83 |
| Male | 93,309.96 |
| Female | 90,140.87 |
| Under 1 year | 4,324.76 |
| Under 5 years | 20,507.90 |

Definitions:
- under 1 = male age 0 + female age 0;
- under 5 = under 1 + male age 1–4 + female age 1–4.

Under-one is contained within under-five and is not added again as a separate category.

## 3. Settlement reconciliation

Mapped settlement components inside Sagbama: **832**.

Population reconciliation:

| Metric | LGA estimate | Inside mapped settlements | Outside mapped settlements | Coverage |
|---|---:|---:|---:|---:|
| Total | 183,450.83 | 154,091.49 | 29,359.34 | 84.00% |
| Male | 93,309.96 | 78,381.99 | 14,927.97 | 84.00% |
| Female | 90,140.87 | 75,709.50 | 14,431.38 | 83.99% |
| Under 1 | 4,324.76 | 3,632.12 | 692.64 | 83.98% |
| Under 5 | 20,507.90 | 17,223.42 | 3,284.48 | 83.98% |

Settlement-overlap validation passed.

The result confirms that settlement population must not be assumed to equal the LGA total.

## 4. Settlement-name matching

Contained GRID3 settlement-name points per settlement component:
- one name point: **90**;
- multiple name points: **57**;
- no contained name point: **685**.

This is treated as a data-quality result, not as a reason to force nearest-name matching. Components without a defensible name retain their source settlement/block identifier.

## 5. Health facilities

After coordinate checks, identifier-based deduplication and strict LGA-boundary assignment:
- **53** health-facility points were inside Sagbama.

This count does not imply that every facility is operational, staffed, open or providing a specific service.

## 6. Google Open Buildings pilot

GitHub Actions run: **36709066830**  
Result: **PASS**

Processing:
- Google Open Buildings v3;
- 3 S2 level-6 tiles considered;
- 605,578,591 source bytes downloaded during the workflow;
- 5,956,216 rows read;
- 19,160 source centroids fell inside the LGA before thresholding;
- Google per-level-4 90% precision thresholds were applied to level-6 shards;
- 13,638 detected building footprints remained after thresholding and deduplication;
- exact duplicates removed: 0.

Allocation:
- 13,578 detected footprints allocated to exactly one mapped settlement component;
- 60 detected footprints remained inside Sagbama but outside mapped settlement components;
- allocation reconciliation passed.

Allocation rule: source centroid strictly within a component. A centroid exactly on a component boundary is not assigned to either neighbour.

These are counts of **detected building footprints**, not households, residential units, occupied dwellings or people.

## 7. Publication and licensing gate

Raw national third-party data were not committed to GitHub.

The analytical pilot is considered passed. Public publication of a pilot package containing GRID3 Settlement Extents v4.1-derived geometry remains blocked until the exact v4.1 redistribution licence is verified.

A current search confirms that:
- Settlement Extents v4.0 metadata explicitly specifies CC BY-SA 4.0;
- the GRID3 Nigeria catalogue lists Settlement Extents v4.1 as the August 2026 current release;
- the exact v4.1 licence text has not yet been captured from v4.1-specific metadata/release notes.

The repository therefore does **not** assume that the v4.0 licence automatically applies to v4.1.

## 8. Gate decision

**Analytical pilot: PASS**  
**Public v4.1-derived data packaging: BLOCKED pending exact licence confirmation**

The next safe data-foundation tasks are:
1. obtain/record the exact Settlement Extents v4.1 licence and citation;
2. create a redistribution-safe pilot package;
3. measure final pilot package size;
4. use that evidence to design state-level packages for national scaling.
