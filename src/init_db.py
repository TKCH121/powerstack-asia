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
