import duckdb
from config import DB_PATH

SCHEMA_SQL = r'''
CREATE TABLE IF NOT EXISTS dc_projects (
    project_id VARCHAR PRIMARY KEY,
    operator VARCHAR,
    project_name VARCHAR,
    location_text VARCHAR,
    state VARCHAR,
    country VARCHAR,
    announced_it_mw DOUBLE,
    secured_supply_mw DOUBLE,
    target_operation_date VARCHAR,
    status VARCHAR,
    source_url VARCHAR,
    source_date DATE,
    fact_type VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS connection_events (
    event_id VARCHAR PRIMARY KEY,
    project_id VARCHAR,
    event_date VARCHAR,
    date_precision VARCHAR,
    event_type VARCHAR,
    voltage_kv DOUBLE,
    supply_mw DOUBLE,
    interim_or_permanent VARCHAR,
    grid_operator VARCHAR,
    infrastructure_name VARCHAR,
    contractor VARCHAR,
    source_url VARCHAR,
    fact_type VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS source_registry (
    source_id VARCHAR PRIMARY KEY,
    source_name VARCHAR,
    source_type VARCHAR,
    url VARCHAR,
    authority_level VARCHAR,
    notes VARCHAR
);
'''

def main():
    con = duckdb.connect(str(DB_PATH))
    con.execute(SCHEMA_SQL)
    print(f"Created/verified database at: {DB_PATH}")
    print(con.execute("SHOW TABLES").fetchdf())
    con.close()

if __name__ == "__main__":
    main()
