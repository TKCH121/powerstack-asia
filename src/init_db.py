import duckdb

from config import DB_PATH


POWER_PATHWAY_SCHEMAS = {
    "power_pathways": {
        "columns": [
            "pathway_id",
            "project_id",
            "prediction_date",
            "prediction_date_precision",
            "information_cutoff_date",
            "information_cutoff_date_precision",
            "assessment_scope",
            "prediction_context",
            "target_power_mw",
            "target_power_measure_type",
            "target_power_mw_qualifier",
            "ultimate_power_mw",
            "ultimate_power_measure_type",
            "ultimate_power_mw_qualifier",
            "pathway_type",
            "connection_voltage_kv",
            "fact_type",
            "source_url",
            "source_date",
            "notes",
        ],
        "create_sql": """
            CREATE TABLE power_pathways (
                pathway_id VARCHAR PRIMARY KEY,
                project_id VARCHAR NOT NULL,
                prediction_date VARCHAR NOT NULL,
                prediction_date_precision VARCHAR NOT NULL,
                information_cutoff_date VARCHAR,
                information_cutoff_date_precision VARCHAR,
                assessment_scope VARCHAR NOT NULL,
                prediction_context VARCHAR,
                target_power_mw DOUBLE,
                target_power_measure_type VARCHAR NOT NULL,
                target_power_mw_qualifier VARCHAR NOT NULL,
                ultimate_power_mw DOUBLE,
                ultimate_power_measure_type VARCHAR NOT NULL,
                ultimate_power_mw_qualifier VARCHAR NOT NULL,
                pathway_type VARCHAR,
                connection_voltage_kv DOUBLE,
                fact_type VARCHAR NOT NULL,
                source_url VARCHAR,
                source_date VARCHAR,
                notes VARCHAR
            )
        """,
    },
    "power_pathway_components": {
        "columns": [
            "component_id",
            "pathway_id",
            "component_type",
            "requirement_status",
            "infrastructure_timing",
            "asset_name",
            "voltage_kv",
            "capacity_value",
            "capacity_unit",
            "target_completion_date",
            "target_date_precision",
            "actual_completion_date",
            "actual_date_precision",
            "delivery_party",
            "handover_status",
            "connection_event_id",
            "grid_asset_event_id",
            "fact_type",
            "source_url",
            "source_date",
            "notes",
        ],
        "create_sql": """
            CREATE TABLE power_pathway_components (
                component_id VARCHAR PRIMARY KEY,
                pathway_id VARCHAR NOT NULL,
                component_type VARCHAR NOT NULL,
                requirement_status VARCHAR NOT NULL,
                infrastructure_timing VARCHAR NOT NULL,
                asset_name VARCHAR,
                voltage_kv DOUBLE,
                capacity_value DOUBLE,
                capacity_unit VARCHAR,
                target_completion_date VARCHAR,
                target_date_precision VARCHAR,
                actual_completion_date VARCHAR,
                actual_date_precision VARCHAR,
                delivery_party VARCHAR,
                handover_status VARCHAR,
                connection_event_id VARCHAR,
                grid_asset_event_id VARCHAR,
                fact_type VARCHAR NOT NULL,
                source_url VARCHAR,
                source_date VARCHAR,
                notes VARCHAR
            )
        """,
    },
    "power_pathway_milestones": {
        "columns": [
            "milestone_id",
            "pathway_id",
            "milestone_type",
            "milestone_status",
            "milestone_date",
            "date_precision",
            "power_mw",
            "power_measure_type",
            "power_mw_qualifier",
            "delivery_party",
            "connection_event_id",
            "fact_type",
            "source_url",
            "source_date",
            "notes",
        ],
        "create_sql": """
            CREATE TABLE power_pathway_milestones (
                milestone_id VARCHAR PRIMARY KEY,
                pathway_id VARCHAR NOT NULL,
                milestone_type VARCHAR NOT NULL,
                milestone_status VARCHAR NOT NULL,
                milestone_date VARCHAR,
                date_precision VARCHAR,
                power_mw DOUBLE,
                power_measure_type VARCHAR NOT NULL,
                power_mw_qualifier VARCHAR NOT NULL,
                delivery_party VARCHAR,
                connection_event_id VARCHAR,
                fact_type VARCHAR NOT NULL,
                source_url VARCHAR,
                source_date VARCHAR,
                notes VARCHAR
            )
        """,
    },
}


LEGACY_POWER_PATHWAY_COLUMNS = {
    "pathway_id",
    "project_id",
    "prediction_date",
    "prediction_date_precision",
    "assessment_scope",
    "prediction_context",
    "target_supply_mw",
    "target_supply_mw_qualifier",
    "ultimate_supply_mw",
    "ultimate_supply_mw_qualifier",
    "pathway_type",
    "connection_voltage_kv",
    "fact_type",
    "source_url",
    "source_date",
    "notes",
}

LEGACY_POWER_PATHWAY_COMPONENT_COLUMNS = {
    "component_id",
    "pathway_id",
    "component_type",
    "requirement_status",
    "infrastructure_timing",
    "asset_name",
    "voltage_kv",
    "capacity_mw",
    "target_completion_date",
    "target_date_precision",
    "actual_completion_date",
    "actual_date_precision",
    "delivery_party",
    "handover_status",
    "connection_event_id",
    "grid_asset_event_id",
    "fact_type",
    "source_url",
    "source_date",
    "notes",
}

LEGACY_POWER_PATHWAY_MILESTONE_COLUMNS = {
    "milestone_id",
    "pathway_id",
    "milestone_type",
    "milestone_status",
    "milestone_date",
    "date_precision",
    "supply_mw",
    "delivery_party",
    "connection_event_id",
    "fact_type",
    "source_url",
    "source_date",
    "notes",
}


def table_exists(con, table_name):
    return con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = ?
        """,
        [table_name],
    ).fetchone()[0] == 1


def migrate_populated_power_pathways(con):
    """Atomically copy the populated legacy table into the refined schema."""
    if not table_exists(con, "power_pathways"):
        return

    current_columns = {
        row[0]
        for row in con.execute("DESCRIBE power_pathways").fetchall()
    }

    if current_columns != LEGACY_POWER_PATHWAY_COLUMNS:
        return

    legacy_records = con.execute(
        """
        SELECT pathway_id, project_id, prediction_date,
               prediction_date_precision, assessment_scope,
               prediction_context, target_supply_mw,
               target_supply_mw_qualifier, ultimate_supply_mw,
               ultimate_supply_mw_qualifier, pathway_type,
               connection_voltage_kv, fact_type, source_url,
               source_date, notes
        FROM power_pathways
        ORDER BY pathway_id
        """
    ).fetchall()

    if not legacy_records:
        return

    expected_baseline = [
        ("PP-JHR-001", 85.5),
        ("PP-JHR-002", None),
        ("PP-JHR-003", 280.0),
    ]
    actual_baseline = [(row[0], row[6]) for row in legacy_records]

    if actual_baseline != expected_baseline:
        raise RuntimeError(
            "Refusing automatic power_pathways migration because the "
            "populated legacy rows do not match the approved unit-test baseline."
        )

    migration_table = "power_pathways_schema_migration"
    if table_exists(con, migration_table):
        raise RuntimeError(
            f"Refusing migration because temporary table {migration_table!r} "
            "already exists."
        )

    measure_types = {
        "PP-JHR-001": "MAXIMUM_DEMAND",
        "PP-JHR-002": "NOT_FOUND",
        "PP-JHR-003": "ELECTRICAL_SUPPLY",
    }
    expected_migrated_records = [
        row[:4]
        + (None, None)
        + row[4:6]
        + (
            row[6],
            measure_types[row[0]],
            row[7],
            row[8],
            "NOT_FOUND",
            row[9],
        )
        + row[10:]
        for row in legacy_records
    ]

    con.execute("BEGIN TRANSACTION")

    try:
        migration_sql = POWER_PATHWAY_SCHEMAS["power_pathways"][
            "create_sql"
        ].replace(
            "CREATE TABLE power_pathways",
            f"CREATE TABLE {migration_table}",
            1,
        )
        con.execute(migration_sql)
        con.execute(
            f"""
            INSERT INTO {migration_table} (
                pathway_id,
                project_id,
                prediction_date,
                prediction_date_precision,
                information_cutoff_date,
                information_cutoff_date_precision,
                assessment_scope,
                prediction_context,
                target_power_mw,
                target_power_measure_type,
                target_power_mw_qualifier,
                ultimate_power_mw,
                ultimate_power_measure_type,
                ultimate_power_mw_qualifier,
                pathway_type,
                connection_voltage_kv,
                fact_type,
                source_url,
                source_date,
                notes
            )
            SELECT
                pathway_id,
                project_id,
                prediction_date,
                prediction_date_precision,
                NULL,
                NULL,
                assessment_scope,
                prediction_context,
                target_supply_mw,
                CASE pathway_id
                    WHEN 'PP-JHR-001' THEN 'MAXIMUM_DEMAND'
                    WHEN 'PP-JHR-002' THEN 'NOT_FOUND'
                    WHEN 'PP-JHR-003' THEN 'ELECTRICAL_SUPPLY'
                END,
                target_supply_mw_qualifier,
                ultimate_supply_mw,
                'NOT_FOUND',
                ultimate_supply_mw_qualifier,
                pathway_type,
                connection_voltage_kv,
                fact_type,
                source_url,
                source_date,
                notes
            FROM power_pathways
            ORDER BY pathway_id
            """
        )

        migrated_records = con.execute(
            f"""
            SELECT pathway_id, project_id, prediction_date,
                   prediction_date_precision, information_cutoff_date,
                   information_cutoff_date_precision, assessment_scope,
                   prediction_context, target_power_mw,
                   target_power_measure_type, target_power_mw_qualifier,
                   ultimate_power_mw, ultimate_power_measure_type,
                   ultimate_power_mw_qualifier, pathway_type,
                   connection_voltage_kv, fact_type, source_url,
                   source_date, notes
            FROM {migration_table}
            ORDER BY pathway_id
            """
        ).fetchall()

        if migrated_records != expected_migrated_records:
            raise RuntimeError(
                "Power-pathway migration verification failed; rolling back."
            )

        con.execute(
            "ALTER TABLE power_pathways "
            "RENAME TO power_pathways_legacy_backup"
        )
        con.execute(
            f"ALTER TABLE {migration_table} RENAME TO power_pathways"
        )
        con.execute("DROP TABLE power_pathways_legacy_backup")

    except Exception:
        con.execute("ROLLBACK")
        raise

    con.execute("COMMIT")
    print("Migrated 3 populated power_pathways rows without data loss.")


def migrate_populated_pathway_evidence_tables(con):
    """Atomically migrate populated component and milestone evidence tables."""
    component_table = "power_pathway_components"
    milestone_table = "power_pathway_milestones"

    component_records = []
    if table_exists(con, component_table):
        component_columns = {
            row[0]
            for row in con.execute(f"DESCRIBE {component_table}").fetchall()
        }
        if component_columns == LEGACY_POWER_PATHWAY_COMPONENT_COLUMNS:
            component_records = con.execute(
                """
                SELECT component_id, pathway_id, component_type,
                       requirement_status, infrastructure_timing, asset_name,
                       voltage_kv, capacity_mw, target_completion_date,
                       target_date_precision, actual_completion_date,
                       actual_date_precision, delivery_party, handover_status,
                       connection_event_id, grid_asset_event_id, fact_type,
                       source_url, source_date, notes
                FROM power_pathway_components
                ORDER BY component_id
                """
            ).fetchall()

    if any(row[7] is not None for row in component_records):
        raise RuntimeError(
            "Refusing automatic component migration because a legacy "
            "capacity_mw value has no source unit."
        )

    milestone_records = []
    if table_exists(con, milestone_table):
        milestone_columns = {
            row[0]
            for row in con.execute(f"DESCRIBE {milestone_table}").fetchall()
        }
        if milestone_columns == LEGACY_POWER_PATHWAY_MILESTONE_COLUMNS:
            milestone_records = con.execute(
                """
                SELECT milestone_id, pathway_id, milestone_type,
                       milestone_status, milestone_date, date_precision,
                       supply_mw, delivery_party, connection_event_id,
                       fact_type, source_url, source_date, notes
                FROM power_pathway_milestones
                ORDER BY milestone_id
                """
            ).fetchall()

    milestone_power_semantics = {
        "PPM-JHR-001-001": (None, "NOT_FOUND", "NOT_FOUND"),
        "PPM-JHR-001-002": (16.0, "ELECTRICAL_SUPPLY", "EXACT"),
        "PPM-JHR-001-003": (85.5, "MAXIMUM_DEMAND", "EXACT"),
        "PPM-JHR-002-001": (None, "NOT_FOUND", "NOT_FOUND"),
        "PPM-JHR-002-002": (None, "NOT_FOUND", "NOT_FOUND"),
        "PPM-JHR-003-001": (280.0, "ELECTRICAL_SUPPLY", "EXACT"),
    }
    actual_milestone_baseline = [
        (row[0], row[6]) for row in milestone_records
    ]
    expected_milestone_baseline = [
        (milestone_id, semantics[0])
        for milestone_id, semantics in milestone_power_semantics.items()
    ]

    if (
        milestone_records
        and actual_milestone_baseline != expected_milestone_baseline
    ):
        raise RuntimeError(
            "Refusing automatic milestone migration because the populated "
            "legacy rows do not match the approved six-row baseline."
        )

    migrations = []
    if component_records:
        migrations.append(component_table)
    if milestone_records:
        migrations.append(milestone_table)
    if not migrations:
        return

    for table_name in migrations:
        for suffix in ["schema_migration", "legacy_backup"]:
            temporary_name = f"{table_name}_{suffix}"
            if table_exists(con, temporary_name):
                raise RuntimeError(
                    f"Refusing migration because temporary table "
                    f"{temporary_name!r} already exists."
                )

    con.execute("BEGIN TRANSACTION")

    try:
        if component_records:
            migration_table = f"{component_table}_schema_migration"
            migration_sql = POWER_PATHWAY_SCHEMAS[component_table][
                "create_sql"
            ].replace(
                f"CREATE TABLE {component_table}",
                f"CREATE TABLE {migration_table}",
                1,
            )
            con.execute(migration_sql)
            con.execute(
                f"""
                INSERT INTO {migration_table} (
                    component_id, pathway_id, component_type,
                    requirement_status, infrastructure_timing, asset_name,
                    voltage_kv, capacity_value, capacity_unit,
                    target_completion_date, target_date_precision,
                    actual_completion_date, actual_date_precision,
                    delivery_party, handover_status, connection_event_id,
                    grid_asset_event_id, fact_type, source_url, source_date,
                    notes
                )
                SELECT component_id, pathway_id, component_type,
                       requirement_status, infrastructure_timing, asset_name,
                       voltage_kv, capacity_mw, NULL,
                       target_completion_date, target_date_precision,
                       actual_completion_date, actual_date_precision,
                       delivery_party, handover_status, connection_event_id,
                       grid_asset_event_id, fact_type, source_url, source_date,
                       notes
                FROM {component_table}
                ORDER BY component_id
                """
            )
            migrated_components = con.execute(
                f"""
                SELECT component_id, pathway_id, component_type,
                       requirement_status, infrastructure_timing, asset_name,
                       voltage_kv, capacity_value, capacity_unit,
                       target_completion_date, target_date_precision,
                       actual_completion_date, actual_date_precision,
                       delivery_party, handover_status, connection_event_id,
                       grid_asset_event_id, fact_type, source_url, source_date,
                       notes
                FROM {migration_table}
                ORDER BY component_id
                """
            ).fetchall()
            expected_components = [
                row[:8] + (None,) + row[8:] for row in component_records
            ]
            if migrated_components != expected_components:
                raise RuntimeError(
                    "Component migration verification failed; rolling back."
                )

        if milestone_records:
            migration_table = f"{milestone_table}_schema_migration"
            migration_sql = POWER_PATHWAY_SCHEMAS[milestone_table][
                "create_sql"
            ].replace(
                f"CREATE TABLE {milestone_table}",
                f"CREATE TABLE {migration_table}",
                1,
            )
            con.execute(migration_sql)
            con.execute(
                f"""
                INSERT INTO {migration_table} (
                    milestone_id, pathway_id, milestone_type,
                    milestone_status, milestone_date, date_precision,
                    power_mw, power_measure_type, power_mw_qualifier,
                    delivery_party, connection_event_id, fact_type,
                    source_url, source_date, notes
                )
                SELECT milestone_id, pathway_id, milestone_type,
                       milestone_status, milestone_date, date_precision,
                       supply_mw,
                       CASE milestone_id
                           WHEN 'PPM-JHR-001-002' THEN 'ELECTRICAL_SUPPLY'
                           WHEN 'PPM-JHR-001-003' THEN 'MAXIMUM_DEMAND'
                           WHEN 'PPM-JHR-003-001' THEN 'ELECTRICAL_SUPPLY'
                           ELSE 'NOT_FOUND'
                       END,
                       CASE WHEN supply_mw IS NULL
                           THEN 'NOT_FOUND'
                           ELSE 'EXACT'
                       END,
                       delivery_party, connection_event_id, fact_type,
                       source_url, source_date, notes
                FROM {milestone_table}
                ORDER BY milestone_id
                """
            )
            migrated_milestones = con.execute(
                f"""
                SELECT milestone_id, pathway_id, milestone_type,
                       milestone_status, milestone_date, date_precision,
                       power_mw, power_measure_type, power_mw_qualifier,
                       delivery_party, connection_event_id, fact_type,
                       source_url, source_date, notes
                FROM {migration_table}
                ORDER BY milestone_id
                """
            ).fetchall()
            expected_milestones = [
                row[:6] + milestone_power_semantics[row[0]] + row[7:]
                for row in milestone_records
            ]
            if migrated_milestones != expected_milestones:
                raise RuntimeError(
                    "Milestone migration verification failed; rolling back."
                )

        for table_name in migrations:
            migration_table = f"{table_name}_schema_migration"
            backup_table = f"{table_name}_legacy_backup"
            con.execute(
                f"ALTER TABLE {table_name} RENAME TO {backup_table}"
            )
            con.execute(
                f"ALTER TABLE {migration_table} RENAME TO {table_name}"
            )
            con.execute(f"DROP TABLE {backup_table}")

    except Exception:
        con.execute("ROLLBACK")
        raise

    con.execute("COMMIT")
    for table_name, records in [
        (component_table, component_records),
        (milestone_table, milestone_records),
    ]:
        if records:
            print(
                f"Migrated {len(records)} populated {table_name} rows "
                "without data loss."
            )


def migrate_power_pathway_schema(con):
    """Create the approved schema without discarding populated pathway data."""
    migrate_populated_power_pathways(con)
    migrate_populated_pathway_evidence_tables(con)

    tables_to_replace = []

    for table_name, definition in POWER_PATHWAY_SCHEMAS.items():
        if not table_exists(con, table_name):
            continue

        current_columns = [
            row[0]
            for row in con.execute(f"DESCRIBE {table_name}").fetchall()
        ]

        if (
            len(current_columns) == len(definition["columns"])
            and set(current_columns) == set(definition["columns"])
        ):
            continue

        row_count = con.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        if row_count:
            raise RuntimeError(
                f"Refusing to replace populated table {table_name!r}; "
                f"found {row_count:,} rows."
            )

        tables_to_replace.append(table_name)

    for table_name in reversed(list(POWER_PATHWAY_SCHEMAS)):
        if table_name in tables_to_replace:
            con.execute(f"DROP TABLE {table_name}")
            print(f"Replaced empty legacy table: {table_name}")

    for table_name, definition in POWER_PATHWAY_SCHEMAS.items():
        if not table_exists(con, table_name):
            con.execute(definition["create_sql"])
            print(f"Created table: {table_name}")


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
    # TABLES 6-8 — POWER-PATHWAY EVIDENCE
    # ==================================================
    # Empty until source-backed pathway records are curated.

    migrate_power_pathway_schema(con)

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
