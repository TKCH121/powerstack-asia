# PowerStack Asia — Project Specification

**Status:** Current technical implementation authority

**Baseline date:** 17 August 2026

## Technical mission

PowerStack Asia is an evidence-first Power & Digital Infrastructure
Intelligence system for Southeast Asia, beginning in Johor. The current
repository connects public planning and mapped-grid data with source-backed
data-centre project, location, infrastructure, agreement, milestone, and
historical-outcome evidence.

The central analytical object is the **Power Pathway**: the commercial
commitments, physical infrastructure, approvals, delivery parties, and
milestones required to obtain a stated electrical quantity by a stated date.

The product definition is governed by [PRODUCT_MEMO.md](PRODUCT_MEMO.md). This
specification defines the current technical scope and implementation boundary.

## Applications and shared layers

The approved applications are:

- Site Diligence;
- Origination Intelligence;
- Market Intelligence;
- Historical Calibration as a research layer.

All four are intended to use one shared evidence and intelligence spine. The
normalized Intelligence Core described in
[MARKET_INTELLIGENCE_MODEL.md](MARKET_INTELLIGENCE_MODEL.md) is designed but not
implemented. Existing historical tables remain authoritative until a
canonical-event and crosswalk design is implemented and validated.

## Current architecture

### Evidence layer

Curated records use `VERIFIED`, `DERIVED`, `INFERRED`, and `NOT_FOUND`, explicit
source URLs/dates, date precision, typed power values, and notes. Missing
evidence is not converted to zero or false.

### Current-state geospatial layer

The canonical Johor pipeline uses:

- PLANMalaysia planning geometries;
- Geofabrik regional OSM PBF data;
- Osmium extraction;
- GeoPandas geometry and proximity processing;
- EPSG:3375 for metric calculations.

Current outputs include industrial planning polygons, mapped HV lines/cables,
mapped HV substations, and derived proximity features. These features describe
mapped topology. They do not establish available capacity, physical
commissioning, utility willingness, site availability, or development
feasibility.

### Historical geospatial layer

The hardened historical OSM prototype uses a dated ohsome inventory plus
versioned OSM API geometry, conservative request caching, exact primitive IDs,
and explicit failure states. It has been regression-tested for PDG JH1 only.
Historical OSM presence means `OSM_MAPPED_AS_OF_CUTOFF`, not independently
verified physical existence or capacity.

### Curated geometry layer

Project polygons are stored separately from point/proxy locations in:

- `data/manual/dc_project_geometries_seed.geojson`;
- `data/manual/dc_project_geometry_sources_seed.csv`.

Digital Halo is classified `AUTHORITATIVE_PROJECT_POLYGON`. TM Nxera is
classified `BOUNDED_PARCEL`; Tier B interval-aware feature engineering is not
implemented. The geometry files are validated but are not loaded into DuckDB or
the current historical endpoint builder.

### Power Pathway layer

The implemented three-table model is preserved:

1. `power_pathways`: assessment envelope, prediction boundary, information
   cutoff, context, typed power, pathway type, and source;
2. `power_pathway_components`: physical component, requirement state,
   infrastructure timing, asset attributes, delivery, completion, and source;
3. `power_pathway_milestones`: dated agreement, study, supply, construction,
   commissioning, energisation, handover, planning, or operating milestone.

The model permits realistic project-enabled infrastructure and phased supply.
It does not infer missing components or require a project to fit a predefined
pathway category.

## Power Pathway principles

Power readiness is not simply proximity to an existing substation. A pathway
may involve:

1. existing suitable connection infrastructure;
2. extension, consumer landing station, or SSU;
3. new PMU or substation plus line/cable works;
4. upstream transmission reinforcement;
5. phased interim-to-permanent supply;
6. source-backed onsite generation or renewable procurement.

New infrastructure may be developed concurrently with the data centre. It must
remain `PROJECT_ENABLED` rather than being presented as a pre-existing feature.

`fact_type` and `infrastructure_timing` are separate dimensions. Explicitly
verified absence uses `NOT_REQUIRED_VERIFIED`; an evidence gap uses
`NOT_FOUND`.

## Capacity semantics

The implementation keeps IT capacity outside Power Pathway power fields.
Pathway power and milestone quantities identify their measure as:

- `ELECTRICAL_SUPPLY`;
- `MAXIMUM_DEMAND`;
- `CONTRACTED_CAPACITY`;
- `CONNECTION_CAPACITY`;
- `NOT_FOUND`.

The future broader intelligence model also requires `IT_CAPACITY` and
`GENERATION_CAPACITY`, but those are not implemented pathway power values.
Different measures, phases, agreements, and units must not be silently summed
or converted.

## Historical Training Methodology v1

The implemented fixed-threshold research question is:

> Once a specific site had been committed, did a verified, project-specific
> >=100 MW qualifying power agreement occur within 48 months?

The strict core is:

```text
POST_SITE_COMMITMENT
+ PRE_QUALIFYING_OR_EQUIVALENT_POWER_COMMITMENT
```

Time zero is the earliest verifiable binding commitment to the exact site. An
earlier binding commitment cannot be replaced by a later completion,
replacement agreement, or announcement.

Construction and project-specific grid-work states at the cutoff are
prediction-time evidence variables and review triggers, not universal hard
inclusion gates. A pre-existing qualifying or functionally equivalent binding
>=100 MW power commitment excludes the observation. Verified >=100 MW
commissioning or energisation at or before time zero also excludes it.

The current database does not store the two project-state variables, and the
current label code does not automate equivalent-commitment review. Strict
eligibility therefore requires documented review in addition to generated
output until a later implementation aligns the code.

A positive endpoint label requires a verified executed agreement milestone
whose own evidence explicitly attributes at least 100 MW of electrical supply,
maximum demand, contracted capacity, or connection capacity to the exact
project. Project-level Power Pathway MW, IT capacity, portfolio totals, and
later commissioning or demand cannot fill a missing agreement quantity.

The endpoint is an agreement-stage outcome. It is not evidence that power was
commissioned, energised, or delivered. Missing agreement evidence or source
silence is not a negative.

Detailed rules are governed by
[HISTORICAL_ENDPOINT_LABELS.md](HISTORICAL_ENDPOINT_LABELS.md).

## Current implemented outputs

- source-backed project, location, connection, grid-asset, component, and
  milestone evidence;
- current-state zoning and mapped-grid topology;
- derived site proximity features;
- curated project geometry and geometry-source manifest;
- dated historical OSM features for the PDG regression case;
- conservative derived historical endpoint labels;
- a thin Streamlit research viewer.

The current UI does not implement the analyst-led Power Pathway Assessment,
origination workflow, market-intelligence workflow, or Intelligence Core.

## Near-term implementation sequence

1. Lock the documentation baseline.
2. Define canonical event identity and evidence crosswalks.
3. Implement Intelligence Core v0.1 and unit-test it with the existing eight
   projects without changing historical facts.
4. Build a breadth-first Johor project master.
5. Produce transparent non-ML analytics.
6. Complete one prospective analyst-led Power Pathway Assessment.
7. Validate with experts and prospective users before broad productization.

## Non-goals

- Estimating confidential substation or network headroom.
- Real-time power-flow analysis or private utility studies.
- ML, statistical scoring, arbitrary pathway weights, or hard distance rules.
- Autonomous acceptance of LLM-extracted material facts.
- A parallel intelligence database that duplicates historical evidence.
- A graph database or distributed data platform without demonstrated need.
- Broad SaaS, API, or ASEAN expansion before the Johor workflow is validated.
- Replacing utility, engineering, legal, title, planning, surveying, or lender
  technical diligence.

## Golden rule

Every material factual field must be sourceable and classified as `VERIFIED`,
`DERIVED`, `INFERRED`, or `NOT_FOUND`. Current mapped topology is not available
capacity, and later project facts are not historical prediction features.
