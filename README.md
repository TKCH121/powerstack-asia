# PowerStack Asia

A learning-and-validation project for estimating **power-pathway readiness** for large electricity loads in Johor, starting with data centres.

## First MVP question

> For a candidate location in Johor, what public evidence indicates that a viable >=100 MW power pathway could be available within 48 months?

This repository intentionally starts simple:

1. Verified public source register
2. Manually curated data-centre and connection-event seed data
3. Johor land-use/zoning downloader
4. DuckDB database
5. Streamlit inspection app
6. Later: grid geometry, engineered features, retrospective labels, and ML

## Important modelling rule

We do **not** claim to know confidential substation headroom.

We distinguish:
- `VERIFIED`: directly supported by a source
- `DERIVED`: mechanically calculated from verified data
- `INFERRED`: model or analyst inference
- `NOT_FOUND`: searched for but not verified

## Setup

Open Anaconda Prompt or PowerShell where `conda` works:

```powershell
conda env create -f environment.yml
conda activate powerstack
python -m ipykernel install --user --name powerstack --display-name "Python (powerstack)"
```

Initialize the local database:

```powershell
python src/init_db.py
python src/load_seed_data.py
```

Optional: download Johor planning/zoning data from the Malaysian government ArcGIS service:

```powershell
python src/download_johor_zoning.py
```

Run the starter app:

```powershell
streamlit run app/app.py
```

Then open the local URL shown by Streamlit, usually `http://localhost:8501`.

## First milestone

Do **not** train ML yet.

First build a reliable historical dataset of:
- 30+ Johor data-centre projects/phases
- 100+ dated power/grid/connection events
- source URLs and evidence levels
- target/actual energisation milestones where publicly verifiable

Only after that should we build a retrospective scoring model and then ML.
