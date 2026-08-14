import duckdb

from config import DB_PATH


def main():

    print("=" * 70)
    print("POWERSTACK — DATABASE INITIALISATION")
    print("=" * 70)

    print()
    print(f"Database: {DB_PATH}")

    # --------------------------------------------------
    # Connect to DuckDB
    # --------------------------------------------------

    con = duckdb.connect(
        str(DB_PATH)
    )

    # ==================================================
    # TABLE 1 — DATA CENTRE PROJECTS
    # ==================================================

    con.execute("""
    CREATE TABLE IF NOT EXISTS dc_projects (

        project_id VARCHAR,

        operator_at_event VARCHAR,

        current_operator VARCHAR,

        project_name VARCHAR,

        location_text VARCHAR,

        state VARCHAR,

        country VARCHAR,

        announced_it_mw DOUBLE,

        secured_supply_mw DOUBLE,

        location_precision VARCHAR,

        status VARCHAR,

        source_url VARCHAR,

        source_date VARCHAR,

        fact_type VARCHAR,

        notes VARCHAR
    )
    """)

    # ==================================================
    # TABLE 2 — GRID / CONNECTION EVENTS
    # ==================================================

    con.execute("""
    CREATE TABLE IF NOT EXISTS connection_events (

        event_id VARCHAR,

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
    )
    """)

    # ==================================================
    # TABLE 3 — SOURCE REGISTER
    # ==================================================
    #
    # This remains deliberately simple.
    # We can expand it later when PowerStack begins
    # ingesting many more source types.
    # ==================================================

    con.execute("""
    CREATE TABLE IF NOT EXISTS source_registry (

        source_id VARCHAR,

        source_name VARCHAR,

        source_url VARCHAR,

        source_type VARCHAR,

        geography VARCHAR,

        authority_level VARCHAR,

        access_type VARCHAR,

        fact_type VARCHAR,

        notes VARCHAR
    )
    """)

    # ==================================================
    # TABLE 4 — PROJECT LOCATION EVIDENCE
    # ==================================================

    con.execute("""
    CREATE TABLE IF NOT EXISTS dc_project_locations (

        project_id VARCHAR,
        latitude DOUBLE,
        longitude DOUBLE,
        location_precision VARCHAR,
        location_reference VARCHAR,
        title_reference VARCHAR,
        location_source VARCHAR,
        fact_type VARCHAR,
        notes VARCHAR
    )
    """)

    # ==================================================
    # TABLE 5 — TIME-AWARE GRID-ASSET EVENTS
    # ==================================================

    con.execute("""
    CREATE TABLE IF NOT EXISTS grid_asset_events (

        asset_event_id VARCHAR,
        project_id VARCHAR,
        asset_name VARCHAR,
        asset_type VARCHAR,
        voltage_kv DOUBLE,
        event_date VARCHAR,
        date_precision VARCHAR,
        event_type VARCHAR,
        status_relative_to_project_decision VARCHAR,
        source_url VARCHAR,
        fact_type VARCHAR,
        notes VARCHAR
    )
    """)

    # ==================================================
    # TABLE 6 — FUTURE POWER-PATHWAY EVIDENCE
    # ==================================================
    # Empty until source-backed pathway records are curated.

    con.execute("""
    CREATE TABLE IF NOT EXISTS power_pathways (

        project_id VARCHAR,
        prediction_date VARCHAR,
        target_mw DOUBLE,
        ultimate_demand_mw DOUBLE,
        pathway_type VARCHAR,
        connection_voltage_kv DOUBLE,
        preexisting_grid VARCHAR,
        new_consumer_landing_station VARCHAR,
        new_ssu VARCHAR,
        new_pmu VARCHAR,
        new_line_or_cable VARCHAR,
        major_upstream_reinforcement VARCHAR,
        interim_supply_mw DOUBLE,
        interim_supply_date VARCHAR,
        permanent_supply_mw DOUBLE,
        target_energisation_date VARCHAR,
        right_of_way_required VARCHAR,
        delivery_party VARCHAR,
        handover_to_tnb VARCHAR,
        tnb_study_status VARCHAR,
        esa_status VARCHAR,
        planning_status VARCHAR,
        fact_type VARCHAR,
        source_url VARCHAR,
        notes VARCHAR
    )
    """)

    # --------------------------------------------------
    # Show tables created
    # --------------------------------------------------

    tables = con.execute("""
        SHOW TABLES
    """).fetchall()

    print()
    print("Tables available:")

    for table in tables:
        print(
            f"  - {table[0]}"
        )

    # --------------------------------------------------
    # Show dc_projects schema
    # --------------------------------------------------

    print()
    print("dc_projects schema:")

    dc_schema = con.execute("""
        DESCRIBE dc_projects
    """).fetchall()

    for row in dc_schema:
        print(
            f"  {row[0]:30} {row[1]}"
        )

    # --------------------------------------------------
    # Show connection_events schema
    # --------------------------------------------------

    print()
    print("connection_events schema:")

    event_schema = con.execute("""
        DESCRIBE connection_events
    """).fetchall()

    for row in event_schema:
        print(
            f"  {row[0]:30} {row[1]}"
        )

    # --------------------------------------------------
    # Close database
    # --------------------------------------------------

    con.close()

    print()
    print("=" * 70)
    print("DATABASE INITIALISATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
