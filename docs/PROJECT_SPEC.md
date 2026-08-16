# PowerStack SiteFinder v0.2 — Project Specification

## Objective

Estimate whether a candidate site has a **bankable >=100 MW power pathway by a specified energisation date**, using public evidence. The pathway may include grid infrastructure that can realistically be developed concurrently with the data centre.

This is an evidence database and research tool, not an investment-grade power-flow or confidential-capacity model.

## Core distinction

Power readiness is not simply proximity to an existing substation. A pathway may be:

1. Existing suitable connection infrastructure.
2. Extension or consumer landing station / SSU.
3. New PMU plus line or cable works.
4. Upstream transmission reinforcement.
5. Phased interim-to-permanent supply.
6. Generation, BESS, or renewable-assisted infrastructure.

## Feature timing

- **Current-state screening** may describe mapped lines, substations, zoning, and derived proximity.
- **Historical analysis** must use only evidence available on or before its explicit information cutoff. The prediction date is the decision/event boundary being assessed; it is not automatically the information cutoff. Project-enabled or post-decision infrastructure is not a pre-decision predictor.

Pathway power quantities must identify their measure type, such as electrical supply or maximum demand. IT capacity remains a separate project attribute and must not be inserted into pathway power fields.

## Historical Training Methodology v1

The first fixed-threshold historical question is:

> Once a specific site had been committed, how credible was securing a project-specific >=100 MW power agreement within 48 months?

The initial cohort is `POST_SITE_COMMITMENT`, `PRE_ESA`, `PRE_CONSTRUCTION`, and `PRE_PROJECT_GRID_WORKS`. Time zero is the earliest verifiable binding site commitment. An earlier binding commitment cannot be replaced by a later announcement, and unresolved construction or project-specific grid-work status prevents strict inclusion. `PRE_SITE_COMMITMENT` and `PRE_LAND_ACQUISITION` are separate future cohorts.

A positive requires a verified executed agreement whose own source-backed milestone explicitly attributes at least 100 MW of electrical supply, maximum demand, contracted capacity, or connection capacity to the project. Project-level pathway MW, IT capacity, portfolio totals, and later commissioning or demand cannot fill a missing agreement quantity. The endpoint records an agreement outcome, not physical delivery.

Historical spatial evidence may use exact authoritative project geometry or, in a future interval-aware method, an authoritative containing parcel with verified project containment. A containing-parcel centroid is never a project coordinate. Missing agreement evidence or source silence is not a negative outcome.

## MVP outputs

- Source-backed project, location, connection, and grid-asset timelines.
- Current-state site features with explicit `DERIVED` provenance.
- A three-table historical model: pathway assessments, physical components, and dated milestones. Each independently asserted record retains its evidence status and source.

Infrastructure timing (`CURRENT_STATE`, `PRE_EXISTING_VERIFIED`, `PROJECT_ENABLED`, `POST_DECISION`, or `NOT_FOUND`) is separate from evidence classification. Explicitly verified absence uses `NOT_REQUIRED_VERIFIED`, not `NOT_FOUND`.

## Non-goals

- Estimating confidential substation spare MW.
- Real-time power-flow analysis or private load data.
- ML, arbitrary Power Pathway Score weights, or a hard distance rule.
- Full ASEAN coverage, autonomous research, or additional infrastructure frameworks.

## Golden rule

Every factual field must be sourceable and classified as `VERIFIED`, `DERIVED`, `INFERRED`, or `NOT_FOUND`.
