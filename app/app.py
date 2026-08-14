from pathlib import Path
import sys
import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from config import DB_PATH

st.set_page_config(page_title="PowerStack Asia", layout="wide")
st.title("PowerStack Asia — SiteFinder v0.1")
st.caption("Evidence-first prototype for Johor large-load power readiness")

if not DB_PATH.exists():
    st.error(
        "Database not found. Run `python src/init_db.py` and "
        "`python src/load_seed_data.py` first."
    )
    st.stop()

con = duckdb.connect(str(DB_PATH), read_only=True)

projects = con.execute(
    "SELECT * FROM dc_projects ORDER BY source_date"
).fetchdf()

events = con.execute(
    "SELECT * FROM connection_events ORDER BY event_date"
).fetchdf()

col1, col2, col3 = st.columns(3)
col1.metric("Seed projects", len(projects))
col2.metric("Connection events", len(events))
col3.metric(
    "Verified events",
    int((events["fact_type"] == "VERIFIED").sum()) if len(events) else 0
)

st.subheader("Data-centre projects")
st.dataframe(projects, use_container_width=True, hide_index=True)

st.subheader("Connection-event timeline")
st.dataframe(events, use_container_width=True, hide_index=True)

st.info(
    "Next milestone: expand the historical event database. "
    "Do not train ML until there is enough labelled history."
)

con.close()
