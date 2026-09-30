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

Check for overlapping component geometries before raster aggregation.

## Settlement names
Prefer a shared source ID if one is documented. Otherwise:
1. use point-in-polygon containment;
2. keep all contained names;
3. flag zero-name and multi-name components;
4. separately inspect points on boundaries;
5. never force every polygon to the nearest name.

## Buildings
A count is a count of detected footprints. It is not a household count,
dwelling count or occupancy estimate.

When Google Open Buildings is used, record the confidence filtering policy and
tile-specific threshold if applicable. Assign buildings by centroid (or another
documented deterministic rule) so each footprint is allocated once.

## Health facilities
Deduplicate first by stable identifiers (`nhfr_uid`, `nhfr_facility_code`,
`globalid` as appropriate), then inspect coordinates and administrative
assignment. Do not infer operational status or services.

## Reconciliation
Report:
- LGA modelled population;
- population inside mapped settlement components;
- population outside mapped settlement components;
- difference and percentage coverage.
