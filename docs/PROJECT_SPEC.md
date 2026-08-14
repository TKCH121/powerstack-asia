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
- **Historical analysis** must use only evidence available on or before its prediction date. Project-enabled or post-decision infrastructure is not a pre-decision predictor.

## MVP outputs

- Source-backed project, location, connection, and grid-asset timelines.
- Current-state site features with explicit `DERIVED` provenance.
- A future `power_pathways` evidence table with unknown values recorded as `NOT_FOUND`.

## Non-goals

- Estimating confidential substation spare MW.
- Real-time power-flow analysis or private load data.
- ML, arbitrary Power Pathway Score weights, or a hard distance rule.
- Full ASEAN coverage, autonomous research, or additional infrastructure frameworks.

## Golden rule

Every factual field must be sourceable and classified as `VERIFIED`, `DERIVED`, `INFERRED`, or `NOT_FOUND`.
