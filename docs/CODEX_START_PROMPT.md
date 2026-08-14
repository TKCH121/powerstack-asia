# Codex handoff prompt

Use this prompt only after the repository opens and runs successfully.

You are helping me build PowerStack Asia as a learning project. I am a beginner in Python/data science, so explain meaningful code changes simply, but do not dumb down the underlying reasoning.

Current objective:
Build PowerStack SiteFinder v0.1 for Johor.

Critical modelling constraint:
Do not invent confidential grid capacity. The target is eventually to estimate the probability of a viable >=100 MW power pathway within 48 months using public evidence.

Repository rules:
1. Preserve source provenance for every factual record.
2. Use VERIFIED / DERIVED / INFERRED / NOT_FOUND explicitly.
3. Never replace missing data with guessed values.
4. Keep the stack simple: Python, Pandas/GeoPandas, DuckDB, scikit-learn, Streamlit.
5. Do not introduce LangChain, vector databases, cloud infrastructure, Docker, dbt or orchestration unless the current task genuinely requires them.
6. Make small commits and tests.
7. Before changing multiple files, tell me what you plan to change.
8. When errors occur, explain the error, the likely cause, and the exact fix.

First task:
Inspect the repository, run the existing scripts/tests, and confirm the starter pipeline works. Then propose the smallest next task to expand the historical Johor connection-event dataset without changing the architecture.
