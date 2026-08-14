# Repository Guidelines

## Purpose and Evidence Discipline

PowerStack Asia is an evidence-first Johor power-pathway research project. Preserve `VERIFIED`, `DERIVED`, `INFERRED`, and `NOT_FOUND`; do not guess facts or infer spare grid capacity. Current mapped infrastructure is topology, not confirmed capacity.

## Structure

`src/` contains runnable Python pipeline scripts; `app/app.py` is the Streamlit viewer. Curated source-backed records live in `data/manual/`. Downloaded and derived artifacts belong in `data/raw/` and `data/processed/`; the local DuckDB database belongs in `database/`. These locations are ignored by Git.

`src/search_*.py` files are diagnostics: their candidates do not establish verified project parcels. `download_johor_grid_lines.py` was retired in favour of the Geofabrik plus Osmium pipeline.

## Run Locally

```powershell
conda env create -f environment.yml
conda activate powerstack
python src/check_setup.py
python src/init_db.py
python src/load_seed_data.py
streamlit run app/app.py
```

Run pipeline scripts from the repository root. Execute dependent geospatial steps in documented order; do not refresh external data merely to test a code change.

## Code and Data Changes

Use four-space Python indentation, `snake_case`, `UPPER_SNAKE_CASE` constants, `pathlib.Path`, and explicit provenance fields. Keep the stack limited to Python, Pandas/GeoPandas, DuckDB, Streamlit, Osmium, and public sources unless approved.

Do not silently alter manual evidence CSVs. Historical analysis must use information available as of its prediction date; project-enabled infrastructure is not a pre-decision predictor. Keep `fact_type` separate from `infrastructure_timing`, and use `NOT_REQUIRED_VERIFIED` only for explicitly verified absence. Do not add ML models, capacity claims, arbitrary pathway-score weights, or hard proximity rules.

## Validation and Review

There is no test suite. Run `python src/check_setup.py`, reload the seed database after schema changes, and validate geospatial row counts, CRS, required columns, and sample geometries. PRs should state affected sources, commands run, data/schema effects, and screenshots for UI changes.
