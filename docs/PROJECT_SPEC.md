# PowerStack SiteFinder v0.1 — Project Specification

## Objective

Create a public-data decision engine for Johor that eventually estimates:

`P(viable >=100 MW power pathway within 48 months)`

The first version is an evidence database and rules-based research tool, not an investment-grade grid model.

## Users

Initial hypothetical users:
- data-centre developers
- infrastructure investors/lenders
- land/industrial-park developers
- renewable/BESS developers

## First research question

Can public infrastructure, planning, project, utility and construction signals distinguish projects/areas that subsequently secure large-load power from those that do not?

## MVP outputs

For a project or candidate area:
- known load / announced capacity
- connection evidence
- voltage evidence
- interim/permanent-supply evidence
- grid-reinforcement evidence
- zoning class
- evidence timeline
- confidence
- later: rules-based Power Pathway Score
- later: ML probability

## Non-goals for v0.1

- estimating exact confidential substation spare MW
- real-time power-flow analysis
- customer-private load data
- PPA pricing engine
- autonomous LLM research
- full ASEAN coverage

## Golden rule

Every factual field must be sourceable. Unknown means `NOT_FOUND`, not guessed.
