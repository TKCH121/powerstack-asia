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

### Curated project geometry files

`data/manual/dc_project_geometries_seed.geojson` stores source-backed project
polygons separately from the point/proxy-oriented `dc_project_locations` table.
It is not loaded into DuckDB in v1. Each feature preserves a stable
`geometry_id`, project join, evidence classification, source feature identifiers,
title and PTD references, source/stored CRS, source and independently calculated
areas, effective-date status, retrieval date, geometry hash, and provenance.

`data/manual/dc_project_geometry_sources_seed.csv` is the many-to-one source
manifest for those geometries. It keeps primary geometry evidence separate from
title/project-use evidence and candidate-lot cross-checks. Raw API responses do
not belong in either manual file; retained downloads belong under ignored
`data/raw/` paths.

Current geometry classifications are:

- `AUTHORITATIVE_PROJECT_POLYGON`: an authoritative project-linked polygon plus
  independent evidence that the represented land is the project site. It does
  not imply JUPEM cadastral certification.
- `BOUNDED_PARCEL`: an official project-linked boundary that is not accepted as
  the exact project/title polygon because its completeness or area reconciliation
  remains unresolved.

An unknown title successor or effective date remains `NOT_FOUND`; a candidate
lot must not be promoted to a final surveyed lot without a documented title
chain. Validate the files with:

```powershell
python src/validate_dc_project_geometries.py
```

### `grid_asset_events`

Project-linked asset events: asset identity/type/voltage, dated event, and `status_relative_to_project_decision`. Use this to distinguish `PRE_EXISTING_VERIFIED`, `PROJECT_ENABLED`, `POST_DECISION`, and `NOT_FOUND` when evidence supports them.

## Power Pathway model

The three Power Pathway tables contain the source-backed schema unit-test records for the three current historical projects. Stable `pathway_id`, `component_id`, and `milestone_id` values identify records.

### `power_pathways`

One assessment envelope per project and prediction date:

- `pathway_id`, `project_id`
- `prediction_date`, `prediction_date_precision`: the decision or event boundary being assessed
- `information_cutoff_date`, `information_cutoff_date_precision`: optional latest information an ex-ante assessment may use; leave both null when no defensible cutoff is established
- `assessment_scope`: `CURRENT_STATE` or `EX_ANTE`
- `prediction_context`: optional context such as `PRE_LAND_ACQUISITION`, `PRE_ESA`, `PRE_CONSTRUCTION`, or `CURRENT_SCREEN`
- `target_power_mw`, `ultimate_power_mw`: electricity-related quantities only, never IT capacity
- `target_power_measure_type`, `ultimate_power_measure_type`: `ELECTRICAL_SUPPLY`, `MAXIMUM_DEMAND`, `CONTRACTED_CAPACITY`, `CONNECTION_CAPACITY`, or `NOT_FOUND`
- `target_power_mw_qualifier`, `ultimate_power_mw_qualifier`: `EXACT`, `APPROXIMATE`, `GREATER_THAN`, `LESS_THAN`, or `NOT_FOUND`
- `pathway_type`, `connection_voltage_kv`
- `fact_type`, `source_url`, `source_date`, `notes`

Power MW is distinct from IT capacity recorded in `dc_projects`. Its measure type records whether the source describes electrical supply, maximum demand, contracted capacity, or connection capacity. Do not convert qualified or missing values into invented exact numbers.

Pathway-level power values describe the assessment envelope. They do not, by
themselves, establish the quantity covered by an ESA or other power agreement.
`POWER_AGREEMENT_100MW_WITHIN_48M` may use only a qualifying `VERIFIED`
agreement milestone whose own `power_mw`, `power_measure_type`, and
`power_mw_qualifier` explicitly establish at least 100 MW. A later project-level
maximum demand or commissioning quantity cannot be joined to an earlier
unquantified agreement merely because both concern the same pathway.

`prediction_date` and `information_cutoff_date` are not interchangeable. A historical outcome may occur at the prediction boundary, while model inputs must be limited to information on or before the independently established cutoff. This separation prevents project-enabled or post-decision infrastructure from leaking into ex-ante analysis.

### `power_pathway_components`

One source-backed physical component per row. `component_type` is one of `EXISTING_GRID`, `CONSUMER_LANDING_STATION`, `SSU`, `PMU`, `SUBSTATION`, `LINE`, `CABLE`, `UPSTREAM_REINFORCEMENT`, `RIGHT_OF_WAY`, or `ONSITE_GENERATION`. Do not add hypothetical component rows or use `ONSITE_GENERATION` without project-specific evidence.

`capacity_value` and `capacity_unit` preserve a source-stated component rating. Both must be populated together or both left null. Permitted units are `MW`, `MWac`, `MWp`, and `MVA`; retain the source unit and do not silently convert between them. Component rows also record requirement status, timing, asset identity, voltage, target and actual completion evidence, delivery/handover parties, optional links to existing event records, and provenance.

`requirement_status` distinguishes `REQUIRED`, `NOT_REQUIRED_VERIFIED`, and `NOT_FOUND`. Use `NOT_REQUIRED_VERIFIED` only when a source explicitly verifies that the component is unnecessary.

`infrastructure_timing` is one of:

- `CURRENT_STATE`: present in the current snapshot; historical timing is not established.
- `PRE_EXISTING_VERIFIED`: directly verified as existing by the prediction date.
- `PROJECT_ENABLED`: developed as part of the project's pathway.
- `POST_DECISION`: observed after the prediction date without verified pre-existence.
- `NOT_FOUND`: timing or existence was searched for but not established.

### `power_pathway_milestones`

One source-backed milestone per row. Fields cover milestone type/status, date and precision, power semantics, delivery party, an optional connection-event link, and provenance. Milestones may represent interim power, permanent power, target or actual energisation, a TNB study, ESA, planning approval, or TNB handover.

- `power_mw`: a source-stated electricity-related quantity, never IT capacity
- `power_measure_type`: `ELECTRICAL_SUPPLY`, `MAXIMUM_DEMAND`, `CONTRACTED_CAPACITY`, `CONNECTION_CAPACITY`, or `NOT_FOUND`
- `power_mw_qualifier`: `EXACT`, `APPROXIMATE`, `GREATER_THAN`, `LESS_THAN`, or `NOT_FOUND`

When `power_mw` is null, both semantic fields must be `NOT_FOUND`; when it is populated, neither may be `NOT_FOUND`. An ESA milestone does not by itself establish that its quantity is `ELECTRICAL_SUPPLY`; use the source's stated meaning.

For strict agreement endpoints, attribution is row-level: project/pathway,
agreement type and status, date, typed quantity, qualifier, `VERIFIED` evidence,
and source must be represented by the same source-backed milestone. This rule
does not change the table schema.

### Evidence versus timing

`fact_type` (`VERIFIED`, `DERIVED`, `INFERRED`, `NOT_FOUND`) describes how a fact is supported. `infrastructure_timing` describes when an infrastructure component relates to the prediction decision. These dimensions must never be substituted for one another.

### `source_registry`

Reserved for a future structured source register. The authoritative current register is `docs/SOURCE_REGISTER.md`.

## Geospatial artifacts

`data/processed/johor_powerstack_site_features_v01.parquet` is a current-state, derived proximity table. It does not establish available capacity or historical suitability. Raw and processed artifacts are local and ignored by Git.
