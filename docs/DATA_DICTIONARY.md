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

### `power_pathways`

An empty, future evidence table for prediction date, target and ultimate MW, pathway type, connection/infrastructure components, interim and permanent supply, target energisation, delivery/planning status, provenance, and notes. Populate only from source-backed evidence.

### `source_registry`

Reserved for a future structured source register. The authoritative current register is `docs/SOURCE_REGISTER.md`.

## Geospatial artifacts

`data/processed/johor_powerstack_site_features_v01.parquet` is a current-state, derived proximity table. It does not establish available capacity or historical suitability. Raw and processed artifacts are local and ignored by Git.
