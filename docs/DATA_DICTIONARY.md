# Data Dictionary

## dc_projects

- project_id: internal unique ID
- operator: operator/developer
- project_name: project/campus name
- location_text: human-readable location
- state: state
- country: country
- announced_it_mw: announced IT capacity if explicitly stated
- secured_supply_mw: electricity supply explicitly stated as secured, if verified
- target_operation_date: public target date/text
- status: announced / construction / operating / unknown
- source_url: supporting source
- source_date: source publication date
- fact_type: VERIFIED / DERIVED / INFERRED / NOT_FOUND
- notes: caveats

## connection_events

- event_id
- project_id
- event_date: ISO-like text at the precision actually known, e.g. `2026-01-12`, `2022-10`, or `2023`
- date_precision: DAY / MONTH / YEAR
- event_type
- voltage_kv
- supply_mw
- interim_or_permanent
- grid_operator
- infrastructure_name
- contractor
- source_url
- fact_type
- notes

Suggested event types:
- ESA_SIGNED
- INTERIM_SUPPLY
- SUPPLY_INCREASE
- HV_CONNECTION_AWARD
- SUBSTATION_AWARD
- GRID_REINFORCEMENT
- ENERGISED
- OPERATION_STARTED

## land_zoning

Downloaded from official geospatial service. Keep original source fields and geometry.

## Future grid_assets

- asset_id
- asset_type
- name
- voltage_kv
- latitude
- longitude
- source
- confidence

## Future candidate_features

Examples:
- distance_to_275kv_km
- distance_to_132kv_km
- high_voltage_assets_5km
- known_dc_mw_10km
- recent_grid_events_10km
- industrial_zone_flag
- reinforcement_flag
