# PowerStack Asia

PowerStack Asia is an evidence-first Power & Digital Infrastructure
Intelligence system for Southeast Asia, beginning in Johor. It connects
projects, sites, land, power agreements, grid and generation infrastructure,
planning, renewable procurement, contractors, capital, and dated source
evidence.

The central analytical object is the **Power Pathway**: what commercial
commitments, physical infrastructure, approvals, delivery parties, and
milestones are required to obtain a stated electrical quantity by a stated
date.

```text
POWERSTACK INTELLIGENCE
    |
    +-- Site Diligence
    +-- Origination Intelligence
    +-- Market Intelligence
    +-- Historical Calibration
```

All applications use one evidence and intelligence spine. The future shared
Intelligence Spine is designed but not implemented. The current repository is a
functional research prototype, not a production platform or customer SaaS
product.

## Product boundary

PowerStack v1 is intended to be an **analyst-led Power Pathway Assessment**
supported by software and evidence infrastructure.

PowerStack is not:

- a spare-grid-capacity oracle;
- a guaranteed utility-connection or energisation predictor;
- a Power Pathway Score or ML probability engine;
- proof that proximity establishes feasibility;
- a substitute for utility, engineering, legal, title, planning, surveying, or
  lender technical diligence.

Current and historical OSM features describe public mapped topology. They do
not establish physical commissioning, utility headroom, or available capacity.

## Evidence rules

Every material assertion is `VERIFIED`, `DERIVED`, `INFERRED`, or `NOT_FOUND`.
Unknown is not zero or false. Evidence classification is separate from
infrastructure timing:

- `CURRENT_STATE`
- `PRE_EXISTING_VERIFIED`
- `PROJECT_ENABLED`
- `POST_DECISION`
- `NOT_FOUND`

Historical analysis uses only information admissible at its information
cutoff. Project-enabled or post-decision infrastructure cannot be used as a
pre-decision feature.

See [Methodology Overview](docs/METHODOLOGY_OVERVIEW.md) for the conceptual
method and [Data Dictionary](docs/DATA_DICTIONARY.md) for implemented fields.

## Current repository state

Curated DuckDB evidence currently contains:

- 8 data-centre projects;
- 26 connection events;
- 8 project-location records;
- 6 grid-asset events;
- 8 Power Pathways;
- 5 pathway components;
- 24 pathway milestones.

The current Johor geospatial artifacts contain:

- 4,103 canonical industrial planning geometries;
- 526 mapped HV line/cable features;
- 63 cleaned mapped Johor HV substations.

Digital Halo has a curated `AUTHORITATIVE_PROJECT_POLYGON`. TM Nxera has a
curated `BOUNDED_PARCEL`; it is not accepted as the exact project/title polygon.
Neither is described as JUPEM-certified cadastral geometry.

The historical endpoint output contains 40 project/endpoint rows. For
`POWER_AGREEMENT_100MW_WITHIN_48M`, TM Nxera and Digital Halo are the two
verified observed positives. There is no mature negative. The endpoint is an
agreement-stage outcome, not proof of commissioning, energisation, or delivery.

## Setup

Run commands from the repository root:

```powershell
conda env create -f environment.yml
conda activate powerstack
python src/check_setup.py
python src/init_db.py
python src/load_seed_data.py
streamlit run app/app.py
```

The current Streamlit application is a thin research viewer. It is not the
defined commercial workflow.

## Current-state Johor pipeline

With local raw inputs already present, run:

```powershell
python src/inspect_johor_zoning.py
python src/build_site_grid_features.py
python src/audit_industrial_sites.py
python src/deduplicate_industrial_sites.py
python src/extract_johor_substations.py
python src/clean_johor_hv_substations.py
python src/build_site_substation_features.py
```

`download_johor_zoning.py` and `download_johor_grid_bulk.py` refresh external
sources and write ignored local artifacts. The grid pipeline uses Geofabrik
plus Osmium; the retired regional Overpass/OSMnx approach is not canonical.

## Historical OSM

The hardened PDG JH1 regression can be run with:

```powershell
python src/build_historical_osm_features.py
```

It caches API responses under ignored `data/raw/research/` and writes derived
outputs under ignored `data/processed/research/`. Read
[Historical OSM Prototype](docs/HISTORICAL_OSM_PROTOTYPE.md) before applying the
method to another project.

## Historical endpoint labels

After loading the seed database:

```powershell
python src/build_historical_endpoint_labels.py --evaluation-date 2026-08-14
python src/validate_historical_endpoint_labels.py
```

The strict 100 MW historical core is:

```text
POST_SITE_COMMITMENT
+ PRE_QUALIFYING_OR_EQUIVALENT_POWER_COMMITMENT
```

Construction and project-grid-work states at the cutoff are research variables
and review triggers, not universal hard gates. The current code does not yet
store those states or automate equivalent-commitment review. See
[Historical Endpoint Labels](docs/HISTORICAL_ENDPOINT_LABELS.md) for the
detailed rules and the documented implementation gap.

## Repository structure

- `src/`: Python pipelines, loaders, diagnostics, and validators
- `app/app.py`: current Streamlit research viewer
- `data/manual/`: curated source-backed records committed to Git
- `data/raw/`: ignored downloaded/source artifacts
- `data/processed/`: ignored derived artifacts
- `database/`: ignored local DuckDB database
- `docs/`: product, methodology, source, implementation, and handoff authorities

Do not silently change manual evidence. Raw data, processed data, and the local
DuckDB database are not intended to be committed.

## Documentation authority

- `README.md`: repository entry point
- [PRODUCT_MEMO.md](docs/PRODUCT_MEMO.md): product authority
- [INVESTMENT_MEMO.md](docs/INVESTMENT_MEMO.md): investment and gating authority
- [METHODOLOGY_OVERVIEW.md](docs/METHODOLOGY_OVERVIEW.md): conceptual
  methodology authority
- [MARKET_INTELLIGENCE_MODEL.md](docs/MARKET_INTELLIGENCE_MODEL.md): shared
  intelligence data-model authority
- [PROJECT_SPEC.md](docs/PROJECT_SPEC.md): technical implementation authority
- [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md): implemented field and
  vocabulary authority
- [HISTORICAL_ENDPOINT_LABELS.md](docs/HISTORICAL_ENDPOINT_LABELS.md): detailed
  historical endpoint authority
- [HISTORICAL_OSM_PROTOTYPE.md](docs/HISTORICAL_OSM_PROTOTYPE.md): historical
  OSM authority
- [SOURCE_REGISTER.md](docs/SOURCE_REGISTER.md): source inventory
- [CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md): current operational state

## Next implementation gate

The recommended next engineering task is **Intelligence Core v0.1**: define
canonical event identity and map the existing eight projects into a minimal
normalized intelligence spine without duplicating or altering historical facts.
No ML, score, broad SaaS, or new UI is authorized by the product pivot.
