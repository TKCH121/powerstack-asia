# PowerStack Asia — Codex Handoff

## Current baseline

PowerStack Asia is now defined as an evidence-first Power & Digital
Infrastructure Intelligence system for Southeast Asia, starting with Johor. The
first commercial product is an analyst-led Power Pathway Assessment: a
source-backed view of whether a site has a credible route to the required power
by a specified date. It is not a claim of spare grid capacity, a distance-only
site screen, a trained prediction model, or a Power Pathway Score.

The working branch at this documentation baseline is
`data/historical-pathways-v01`. Do not switch, merge, or push unless the user
explicitly requests it. Inspect live branch and status before every change.

## Documentation authority

- `docs/PRODUCT_MEMO.md`: authoritative internal product definition.
- `docs/INVESTMENT_MEMO.md`: authoritative current investment and venture case.
- `docs/METHODOLOGY_OVERVIEW.md`: conceptual methodological authority.
- `docs/MARKET_INTELLIGENCE_MODEL.md`: proposed Intelligence Core v0.1 design;
  it is not an implemented schema.
- `docs/PROJECT_SPEC.md`: current technical implementation and next sequence.
- `docs/DATA_DICTIONARY.md`: implemented tables, fields, and manual geometry
  artifacts.
- `docs/HISTORICAL_ENDPOINT_LABELS.md`: operational endpoint and cohort rules.
- `docs/HISTORICAL_OSM_PROTOTYPE.md`: historical spatial-extraction contract.
- `docs/SOURCE_REGISTER.md`: current human-readable source register.

If summaries conflict, follow the narrower authoritative document and verify the
implemented code or seed evidence. This handoff is a navigation aid, not a
second specification.

## Implemented repository state

The manual historical baseline contains:

- 8 projects (`DC-JHR-001` through `DC-JHR-008`);
- 26 connection events;
- 8 project-location records;
- 6 project-linked grid-asset events;
- 8 Power Pathway envelopes;
- 5 pathway components; and
- 24 pathway milestones.

The current-state Johor geospatial pipeline produces 4,103 canonical candidate
sites, 526 high-voltage line features, and 63 high-voltage substations. These
features describe mapped topology; they do not prove capacity or historical
availability.

The generated endpoint dataset contains 40 project/endpoint rows across five
endpoint definitions. For the target endpoint,
`POWER_AGREEMENT_100MW_WITHIN_48M`, the current evidence produces:

- 2 `OBSERVED_POSITIVE` cases: TM Nxera and Digital Halo/Nanda;
- 4 `RIGHT_CENSORED` cases;
- 2 `UNLABELABLE` cases; and
- no mature observed negative.

Both target-endpoint positives remain `CALIBRATION_ONLY`; the repository does
not yet contain a target-endpoint case that is fully training-ready.

## Critical case state

### TM Nxera — `DC-JHR-003`

- Prediction boundary: 2024-06-15 / `DAY`.
- Context: `POST_SITE_COMMITMENT`, based on the signed land-acquisition SPA.
- Prediction-time target power and pathway type: `NOT_FOUND`; the later outcome
  must not populate these fields.
- Later outcome: verified electricity-supply agreement on 2026-01-09 for
  280 MW `ELECTRICAL_SUPPLY`, exact.
- Geometry: `EXACT_PLOT_ID_NO_GEOMETRY` in the location table; the separately
  stored official recovered boundary is only `BOUNDED_PARCEL` because parcel
  completeness and area reconciliation are unresolved.
- No invented point or project polygon is permitted.

### Digital Halo / Nanda — `DC-JHR-006`

- Prediction boundary: 2024-06-11 / `DAY`.
- Context: `POST_SITE_COMMITMENT`, based on the original SPA.
- A 2024-07-12 replacement SPA is a later event, not time zero.
- Geometry: `AUTHORITATIVE_PROJECT_POLYGON`, supported by the official MBIP
  planning feature and separate project/site evidence; it is not described as
  JUPEM-certified cadastral geometry.
- Later outcome: the verified 150 MW agreement milestone remains post-boundary
  and does not enter prediction-time pathway fields.
- `PRE_CONSTRUCTION` and `PRE_PROJECT_GRID_WORKS` remain `NOT_FOUND` as research
  state variables.
- Historical OSM extraction has not been run for this geometry.

## Historical methodology lock

The common strict cohort is:

`POST_SITE_COMMITMENT + PRE_QUALIFYING_OR_EQUIVALENT_POWER_COMMITMENT`

A functionally equivalent prior commitment must be exact-site, binding and
effective by time zero, backed by a utility/supplier/connection provider, create
an enforceable supply or connection obligation, and explicitly cover at least
100 MW using a permitted electrical measure. Construction and project-specific
grid-work states are metadata and selection-bias diagnostics, not universal hard
gates. Source silence is never proof that work had not begun.

The existing label generator does not yet store those two state variables or
automate equivalent-commitment review. Treat that as a documented implementation
gap, not permission to infer values.

The agreement endpoint is an agreement-stage outcome only. It does not prove
that 100 MW was commissioned, energised, or delivered. The qualifying milestone
itself must carry verified project-specific power of at least 100 MW; never join
IT capacity, a pathway total, a later commissioning quantity, or a separate
unquantified agreement to manufacture a positive.

## Evidence and data rules

- Preserve `VERIFIED`, `DERIVED`, `INFERRED`, and `NOT_FOUND`.
- Keep `fact_type` separate from `infrastructure_timing`.
- Preserve `CURRENT_STATE`, `PRE_EXISTING_VERIFIED`, `PROJECT_ENABLED`,
  `POST_DECISION`, and `NOT_FOUND`.
- Keep IT MW separate from electrical supply, maximum demand, contracted
  capacity, and connection capacity.
- Do not infer spare grid capacity, exact geometry, missing dates, absent works,
  or title succession.
- Manual evidence changes require explicit source review. Generated raw,
  processed, and DuckDB artifacts remain local and ignored by Git.

## Next implementation sequence

The next planned build is Intelligence Core v0.1, only when the user requests
it. Start with the smallest normalized design for projects/campuses/phases,
organisations and roles, source evidence, capacities, and dated events. Before
loading facts, define canonical event identity and crosswalk existing
`connection_events`, `grid_asset_events`, and Power Pathway milestones so the
repository never gains competing copies of the same event.

Do not begin with ML, scoring, a public SaaS UI, cloud architecture, broad
regional expansion, or new historical project research.

## Standard validation

Use the configured `powerstack` interpreter and run only validations relevant to
the change. The current baseline commands are:

```powershell
python src/check_setup.py
python src/init_db.py
python src/load_seed_data.py
python src/build_historical_endpoint_labels.py --evaluation-date 2026-08-14
python src/validate_historical_endpoint_labels.py
python src/validate_dc_project_geometries.py
git diff --check
```

Do not refresh external data merely to test documentation or code changes.
