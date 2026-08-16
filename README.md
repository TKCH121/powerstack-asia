# PowerStack Asia

PowerStack Asia is an evidence-first research project for Johor data-centre development. Its question is whether public evidence supports a **bankable >=100 MW power pathway by a specified energisation date**. A pathway may include infrastructure developed concurrently with the data centre; it is not a measure of distance to a substation alone.

## Evidence rules

Every material fact is `VERIFIED`, `DERIVED`, `INFERRED`, or `NOT_FOUND`. Never guess missing facts, claim confidential grid headroom, or treat crowdsourced OSM topology as confirmed utility capacity.

Keep two uses of infrastructure separate:

- **Current-state features** describe today’s mapped topology for site research.
- **Ex-ante/as-of-date features** support historical analysis and exclude infrastructure built after, or because of, the project decision.

## Setup

```powershell
conda env create -f environment.yml
conda activate powerstack
python src/check_setup.py
python src/init_db.py
python src/load_seed_data.py
streamlit run app/app.py
```

The DuckDB loader imports all curated manual evidence: projects, connection events, location evidence, and time-aware grid-asset events.

## Local geospatial pipeline

With local raw inputs already present, run the pipeline in this order:

```powershell
python src/inspect_johor_zoning.py
python src/build_site_grid_features.py
python src/audit_industrial_sites.py
python src/deduplicate_industrial_sites.py
python src/extract_johor_substations.py
python src/clean_johor_hv_substations.py
python src/build_site_substation_features.py
```

`download_johor_zoning.py` and `download_johor_grid_bulk.py` refresh external source data and write ignored local artifacts. The latter uses Geofabrik plus Osmium; the earlier regional Overpass/OSMnx approach has been retired.

## Historical OSM features

Run the PDG historical-topology regression case with:

```powershell
python src/build_historical_osm_features.py
```

The extractor caches API responses under ignored `data/raw/research/` and writes
derived outputs under ignored `data/processed/research/`. Historical OSM
presence is public map-state evidence, not proof of physically pre-existing or
available infrastructure. See `docs/HISTORICAL_OSM_PROTOTYPE.md` before using a
different project.

## Derived historical endpoint labels

After loading the seed database, build conservative endpoint labels with:

```powershell
python src/build_historical_endpoint_labels.py --evaluation-date 2026-08-14
```

The ignored output is written to
`data/processed/research/historical_endpoint_labels.csv`. Labels are derived
from verified evidence and are never entered manually in seed CSVs. See
`docs/HISTORICAL_ENDPOINT_LABELS.md` for event mappings, censoring, and negative
label safeguards. The 100 MW endpoint records a qualifying power agreement; it
does not represent physical commissioning, energisation, or delivery. It is a
fixed-threshold outcome: only MW explicitly attributed to the qualifying
agreement may determine the label, and that later outcome must never be included
in features reconstructed at the prediction date. A separate pathway-level MW,
IT capacity, portfolio total, or later commissioning quantity cannot fill a
missing agreement quantity.

The Historical Training Methodology v1 cohort is post-site-commitment but
pre-ESA, pre-construction, and pre-project-grid-works. Its question is: once a
specific site had been committed, how credible was securing a project-specific
>=100 MW power agreement within 48 months? Earlier pre-site-commitment screening
is a separate future cohort.

Run the lightweight endpoint regressions after generating labels:

```powershell
python src/validate_historical_endpoint_labels.py
```

## Current boundary

This repository does not yet build ML or assign Power Pathway Score weights. The next data task is source-backed historical pathway evidence, including what was pre-existing, project-enabled, or post-decision.
