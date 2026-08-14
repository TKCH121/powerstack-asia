# PowerStack Asia — Codex Handoff

## Project objective

PowerStack Asia is an early-stage data and underwriting product for data-centre power development in Southeast Asia, starting with Johor, Malaysia.

The current core question is:

> What is the probability that a site can obtain a bankable >=100 MW power pathway within a specified energisation period, including grid infrastructure that can realistically be developed concurrently with the data centre?

This is NOT simply a "distance to existing substation" product.

Existing grid infrastructure is the starting condition from which a viable power pathway may be engineered.

---

## Commercial thesis

Potential users include:

- data-centre developers
- infrastructure investors and lenders
- industrial land owners/developers
- renewable/BESS developers

A particularly important commercial angle is land origination/arbitrage:

Identify land where the market may underestimate the probability of achieving a bankable data-centre power pathway.

Do not assume that only currently industrial-zoned land can become viable.

---

## Evidence discipline

Every material fact should use one of:

- VERIFIED
- DERIVED
- INFERRED
- NOT_FOUND

Never guess missing information.

Do not convert missing information into zero or false.

Do not claim spare grid capacity unless there is direct evidence.

OSM topology is public/crowdsourced mapping, not utility-confirmed capacity.

---

## Technology constraints

Keep the stack simple:

- Python
- Pandas
- GeoPandas
- Shapely
- DuckDB
- scikit-learn later
- Streamlit
- Osmium
- public APIs / public documents

Avoid introducing unless clearly necessary:

- LangChain
- vector databases
- Docker
- dbt
- orchestration frameworks
- cloud infrastructure
- complex agent frameworks

The user is learning data science from beginner level.

When explaining changes, explicitly state:

- what changed
- why
- which file changed
- what command to run
- expected output
- how to troubleshoot errors

---

## Current verified/derived data state

### Johor zoning

Original relevant PLANMalaysia download contained:

- Industri
- Infrastruktur dan Utiliti

Relevant zoning polygons:
- 12,113

Industrial polygons before deduplication:
- 4,713

Exact duplicate groups:
- 610

Canonical industrial site geometries after deduplication:
- 4,103

No duplicate groups had conflicting source metadata.

Canonical file:
data/processed/johor_industrial_grid_features_clean.parquet

---

## Grid lines

Source:
OpenStreetMap / Geofabrik regional PBF processed locally with Osmium.

All mapped power-line/cable features:
- 8,094

Mapped >=100 kV:
- 526

Main voltage classes:
- 132 kV
- 275 kV
- 500 kV

Current grid capacity/headroom:
- NOT_FOUND

Canonical grid file:
data/processed/johor_hv_power_lines.parquet

The original OSMnx / Overpass approach timed out and was replaced by bulk Geofabrik + Osmium processing.

---

## Substations

Raw mapped substations:
- 2,617

After restricting to all 10 Johor districts and cleaning OSM geometry representation:

Canonical Johor HV substations:
- 63

Maximum-voltage distribution:
- 132 kV: 50
- 275 kV: 10
- 500 kV: 3

Mapped transmission substations:
- 54

Examples found:
- PMU Sedenak
- PMU Plentong
- PMU Pengerang
- Bukit Batu
- Yong Peng
- Sungai Mati
- Batu Pahat Timur

Capacity/headroom:
- NOT_FOUND

Canonical file:
data/processed/johor_hv_substations_clean.parquet

---

## Current site feature table

Canonical candidate universe:
- 4,103 industrial sites

Current master feature file:
data/processed/johor_powerstack_site_features_v01.parquet

Features currently include:

- site area
- planning metadata
- distance to 132 kV line
- distance to 275 kV line
- distance to 500 kV line
- distance to nearest HV substation
- distance to transmission substation
- distance to 132 kV substation
- distance to 275 kV substation
- distance to 500 kV substation

Current-state proximity does NOT establish available MW.

---

## Initial historical project dataset

DuckDB currently loads:

Projects:
- 3

Connection events:
- 9

Projects:

### DC-JHR-001 — GDS Nusajaya Tech Park

Initial IT design:
- 54 MW

Relevant historical evidence includes:
- October 2022 ESA
- 16 MW interim supply target
- plan for maximum demand of 85.5 MW

Location proxy:
- Nusajaya Tech Park mapped polygon

Precision:
- PARK_PROXY

### DC-JHR-002 — Yondr / Vantage JHB1 Sedenak

Campus:
- approximately 300 MW scale

Location proxy:
- STeP East

Precision:
- PARK_SECTION_PROXY / INFERRED

Current mapped PMU Sedenak sits within the proxy geography.

Important:
This creates historical look-ahead leakage because part of the HV infrastructure was developed as part of the project's power pathway.

### DC-JHR-003 — TM Nxera Iskandar Puteri

Power supply:
- 280 MW secured supply

Eventual IT scale:
- >200 MW, preserved in notes because the current numeric schema does not represent > correctly.

Verified plot identity:
- Plot 4A, Edupark West
- PTD 213429
- HSD 598990
- Jalan Kampung Lalang
- Mukim Pulai

Authoritative parcel geometry:
- NOT_FOUND

Do NOT substitute an Iskandar Puteri city centroid.

---

## Historical calibration result

Current calibration uses GDS and Yondr only.

### GDS

Current mapped 275 kV line:
- 1.4725 km
- proximity percentile: 95.44

Current mapped 275 kV substation:
- 10.0682 km
- proximity percentile: 94.35

Result:
The previous hard rule requiring a 275 kV substation <=5 km would incorrectly reject GDS.

Therefore the hard 5 km substation rule is rejected.

### Yondr / Sedenak

Current mapped 275 kV line:
- 0 km

Current mapped 275 kV substation:
- 0 km

Percentiles:
- approximately 100

However this is NOT valid as a historical prediction feature without time-awareness because project-enabled infrastructure is visible in today's OSM snapshot.

This is look-ahead leakage.

---

## Current conceptual model

Do NOT equate:

POWER READY = close to existing substation

Instead model a POWER PATHWAY.

Potential pathways include:

1. Existing-capacity pathway
2. New consumer landing station / SSU pathway
3. New PMU + HV line/cable pathway
4. Major grid-reinforcement pathway
5. Phased/interim-power pathway
6. Generation/BESS/renewable-assisted pathway

New grid infrastructure may legitimately be built concurrently with a data centre.

---

## Proposed connection-burden framework

For later testing:

CB0 — existing suitable connection infrastructure

CB1 — straightforward extension / local connection works

CB2 — new consumer landing station / switching station

CB3 — new PMU plus material HV line/cable works

CB4 — major upstream transmission reinforcement

CB5 — no credible pathway identified

This is currently a conceptual framework, NOT a trained or validated score.

---

## Critical historical modelling rule

Maintain separate concepts:

CURRENT STATE FEATURES

versus

EX-ANTE / AS-OF-DATE FEATURES

Historical ML or calibration must use only information available on or before the chosen prediction date.

Infrastructure subsequently built because of the project cannot be treated as a pre-decision predictor.

Suggested evidence statuses for infrastructure:

- PRE_EXISTING_VERIFIED
- PROJECT_ENABLED
- POST_DECISION
- NOT_FOUND

---

## Likely canonical pipeline scripts

Review before changing:

- src/check_setup.py
- src/init_db.py
- src/load_seed_data.py
- src/download_johor_zoning.py
- src/inspect_johor_zoning.py
- src/download_johor_grid_bulk.py
- src/build_site_grid_features.py
- src/audit_industrial_sites.py
- src/deduplicate_industrial_sites.py
- src/extract_johor_substations.py
- src/clean_johor_hv_substations.py
- src/build_site_substation_features.py
- src/calibrate_historical_projects.py

---

## Likely diagnostic / investigation scripts

Review and decide whether to retain under a diagnostics/research folder:

- search_dc_project_locations.py
- search_tm_nxera_location.py
- search_tm_nxera_parcel.py
- search_tm_nxera_lots.py

Do not delete until their useful findings are preserved in documentation/manual data.

---

## Likely superseded code

The original live Overpass/Osmnx regional grid download was replaced by bulk Geofabrik + Osmium processing.

Review:

- src/download_johor_grid_lines.py

If it is no longer referenced or needed, it can probably be removed after validation.

---

## Current manual evidence files

Important manual files include:

- data/manual/dc_projects_seed.csv
- data/manual/connection_events_seed.csv
- data/manual/dc_project_locations_seed.csv
- data/manual/grid_asset_events_seed.csv

Do not silently change historical evidence.

---

## Important documentation

Read:

- README.md
- docs/PROJECT_SPEC.md
- docs/DATA_DICTIONARY.md
- docs/SOURCE_REGISTER.md
- docs/CODEX_START_PROMPT.md
- docs/CALIBRATION_NOTES.md

---

## Immediate tasks

Do these in order.

### Phase 1 — Repository audit and cleanup

1. Inspect the whole repo.
2. Identify canonical, diagnostic and superseded scripts.
3. Identify duplicated helper logic.
4. Identify outdated docs.
5. Propose cleanup before deleting anything.
6. Preserve provenance.
7. Ensure raw/processed data remains ignored by Git.
8. Keep the project runnable.

### Phase 2 — Refactor

Potentially consolidate repeated utilities such as:

- voltage parsing
- geometry hashing
- CRS constants
- nearest-feature calculations
- evidence constants

Do not over-engineer.

### Phase 3 — Update product specification

Revise PROJECT_SPEC.md so that the target is approximately:

P(viable >=100 MW bankable power pathway by specified energisation date)

The model should allow realistic project-enabled grid infrastructure.

### Phase 4 — Power pathway data model

Design a simple historical `power_pathways` schema including fields such as:

- project_id
- prediction_date
- target_mw
- ultimate_demand_mw
- pathway_type
- connection_voltage_kv
- preexisting_grid
- new_consumer_landing_station
- new_ssu
- new_pmu
- new_line_or_cable
- major_upstream_reinforcement
- interim_supply_mw
- interim_supply_date
- permanent_supply_mw
- target_energisation_date
- right_of_way_required
- delivery_party
- handover_to_tnb
- tnb_study_status
- esa_status
- planning_status
- fact_type
- source
- notes

Do not invent missing facts.

### Phase 5 — Historical dataset expansion

After schema/refactor:

Expand from 3 projects toward approximately 15–30 Johor data-centre projects.

For each project collect not merely site and MW, but:

WHAT POWER PATHWAY DID THE PROJECT ACTUALLY USE?

Do not build ML or a weighted Power Pathway Score until the historical dataset is materially larger.

---

## Current prohibition

Do NOT:

- build ML yet
- assign arbitrary score weights
- treat distance <=5km as a requirement
- use today's project-enabled infrastructure as a historical predictor
- infer spare MW
- guess missing project coordinates
- over-engineer the software stack

The immediate priority is cleanup, time-aware evidence design, and historical dataset construction.