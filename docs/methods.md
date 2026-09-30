# Methods policy

## Population
Raster values are counts of estimated people per grid square. Do not sum
population density values as counts.

For polygon aggregation, use fractional pixel overlap without raster
resampling. This assumes population is uniformly distributed within a pixel
when only part of a pixel intersects a polygon. This assumption must be stated.

Keep `NoData` distinct from a valid zero.

## Demographics
- Under 1: age 0 to <1 year.
- Under 5: age 0 to <5 years.
- Under 1 is contained within under 5.
- Do not estimate under 1 as under 5 / 5.

## Settlement components
If a source settlement/block intersects more than one LGA, create an
LGA-specific component. Preserve the original source ID and construct a
component ID. Population is aggregated to the component geometry, not copied
wholesale into every intersecting LGA.

Check for overlapping component geometries before raster aggregation. The
preparation script stops if overlap is large enough to create meaningful
population double counting.

## Settlement names
Prefer a shared source ID if one is documented. Otherwise:
1. use point-in-polygon containment;
2. keep all contained names;
3. flag zero-name and multi-name components;
4. separately inspect points on boundaries;
5. never force every polygon to the nearest name.

## Buildings
A building result is a count of **detected building footprints**. It is not a
household count, occupied-dwelling count, residential-building count or
population estimate.

For the validated building path, use Google Open Buildings V3 polygons and
Google's documented regional-download pattern:
- identify the level-6 S2 shards covering the selected LGA;
- filter detections using Google's level-4 tile score threshold for a requested
  precision target (90% precision for the pilot);
- retain only detections whose documented source centroid is strictly inside
  the selected LGA;
- remove only exact duplicate detections;
- assign each retained detection to at most one non-overlapping settlement
  component using its source centroid;
- report detections inside the LGA but outside mapped settlement components.

A footprint whose centroid falls exactly on a settlement-component boundary is
left unallocated rather than assigned to both sides.

GRID3 Settlement Extents v4.1 also contains a source `building_count` field.
That whole-source-block count may be retained as a diagnostic for a component
that is effectively the full source block. It must **not** be copied to a
partial cross-LGA component. Partial components require actual footprint
allocation.

Record the Open Buildings confidence policy, tile identifiers, source download
bytes, duplicates removed and allocation reconciliation.

## Health facilities
Construct a deterministic facility identifier using the strongest available
documented ID (`nhfr_uid`, then `nhfr_facility_code`, then `globalid`).
Do not collapse unrelated rows merely because an identifier is null. Where
`last_updated` exists, keep the newest record for duplicate stable IDs.

Check coordinate plausibility, use strict point-in-polygon assignment to the
selected LGA, and report points exactly on the LGA boundary separately. Do not
infer operational status, staffing or services.

## Reconciliation
Report:
- LGA modelled population;
- population inside mapped settlement components;
- population outside mapped settlement components;
- difference and percentage coverage;
- detected buildings allocated to settlement components;
- detected buildings inside the LGA but outside mapped settlement components.

No reconciliation total is forced to match by altering source values.
