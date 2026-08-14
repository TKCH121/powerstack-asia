# Data Dictionary

## Evidence fields

`fact_type` is one of `VERIFIED`, `DERIVED`, `INFERRED`, or `NOT_FOUND`. `source_type` may add context such as `PUBLIC_MAP`; it does not replace `fact_type`. Unknown is not zero.

## Loaded DuckDB tables

### `dc_projects`

Project identity, event-time/current operator, location text, announced IT MW, separately stated secured supply MW, location precision, status, source URL/date, fact type, and notes.

### `connection_events`

Dated electricity and project events: `event_id`, `project_id`, date/precision, event type, voltage, supply MW, interim/permanent status, parties, source URL, fact type, and notes.

### `dc_project_locations`

Project location evidence: coordinates when supported, location precision/reference, source, fact type, and notes. Missing coordinates must remain missing.

### `grid_asset_events`

Project-linked asset events: asset identity/type/voltage, dated event, and `status_relative_to_project_decision`. Use this to distinguish `PRE_EXISTING_VERIFIED`, `PROJECT_ENABLED`, `POST_DECISION`, and `NOT_FOUND` when evidence supports them.

## Power Pathway model

The three Power Pathway tables remain empty until source-backed records are curated. Stable `pathway_id`, `component_id`, and `milestone_id` values identify records.

### `power_pathways`

One assessment envelope per project and prediction date:

- `pathway_id`, `project_id`
- `prediction_date`, `prediction_date_precision`
- `assessment_scope`: `CURRENT_STATE` or `EX_ANTE`
- `prediction_context`: optional context such as `PRE_LAND_ACQUISITION`, `PRE_ESA`, `PRE_CONSTRUCTION`, or `CURRENT_SCREEN`
- `target_supply_mw`, `ultimate_supply_mw`
- `target_supply_mw_qualifier`, `ultimate_supply_mw_qualifier`: `EXACT`, `APPROXIMATE`, `GREATER_THAN`, `LESS_THAN`, or `NOT_FOUND`
- `pathway_type`, `connection_voltage_kv`
- `fact_type`, `source_url`, `source_date`, `notes`

Supply MW is distinct from IT capacity recorded in `dc_projects`. Do not convert qualified or missing values into invented exact numbers.

### `power_pathway_components`

One source-backed physical component per row. `component_type` may identify existing grid, a consumer landing station, SSU, PMU, line, cable, upstream reinforcement, or right-of-way. Component rows also record requirement status, timing, asset identity, voltage/capacity where stated, target and actual completion evidence, delivery/handover parties, optional links to existing event records, and provenance.

`requirement_status` distinguishes `REQUIRED`, `NOT_REQUIRED_VERIFIED`, and `NOT_FOUND`. Use `NOT_REQUIRED_VERIFIED` only when a source explicitly verifies that the component is unnecessary.

`infrastructure_timing` is one of:

- `CURRENT_STATE`: present in the current snapshot; historical timing is not established.
- `PRE_EXISTING_VERIFIED`: directly verified as existing by the prediction date.
- `PROJECT_ENABLED`: developed as part of the project's pathway.
- `POST_DECISION`: observed after the prediction date without verified pre-existence.
- `NOT_FOUND`: timing or existence was searched for but not established.

### `power_pathway_milestones`

One source-backed milestone per row. Fields cover milestone type/status, date and precision, supply MW, delivery party, an optional connection-event link, and provenance. Milestones may represent interim power, permanent power, target or actual energisation, a TNB study, ESA, planning approval, or TNB handover.

### Evidence versus timing

`fact_type` (`VERIFIED`, `DERIVED`, `INFERRED`, `NOT_FOUND`) describes how a fact is supported. `infrastructure_timing` describes when an infrastructure component relates to the prediction decision. These dimensions must never be substituted for one another.

### `source_registry`

Reserved for a future structured source register. The authoritative current register is `docs/SOURCE_REGISTER.md`.

## Geospatial artifacts

`data/processed/johor_powerstack_site_features_v01.parquet` is a current-state, derived proximity table. It does not establish available capacity or historical suitability. Raw and processed artifacts are local and ignored by Git.
