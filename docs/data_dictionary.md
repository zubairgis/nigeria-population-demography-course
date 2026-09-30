# Teaching data dictionary (planned processed outputs)

## states.csv
- `state_id`: stable source state code
- `state_name`: display name
- `source_dataset_id`

## lgas.csv
- `lga_id`: stable source LGA/Area Council code
- `lga_name`
- `state_id`
- `state_name`
- `source_dataset_id`

## lga_summary.csv
- `state_id`, `lga_id`
- `population_total_est`
- `population_male_est`
- `population_female_est`
- `population_u1_est`
- `population_u5_est`
- `population_reference_year`
- `population_dataset_id`
- `aggregation_method`

## settlement_summary.csv
- `source_settlement_id`
- `settlement_component_id`
- `lga_id`
- `settlement_name`
- `name_match_status`
- `detected_building_count`
- demographic estimate fields
- `population_inside_component_est`
- data-quality flags

## health_facilities.csv
Retain source identifiers and documented attributes. At minimum:
- source facility ID(s)
- name
- ownership
- facility level/category
- longitude, latitude
- assigned state/LGA
- source last-updated field when available
- coordinate/admin quality flags
