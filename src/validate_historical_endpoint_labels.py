"""Run lightweight regressions for historical endpoint methodology v1."""

from __future__ import annotations

from datetime import date

import duckdb
import pandas as pd

from build_historical_endpoint_labels import (
    ENDPOINTS,
    build_labels,
    classify_timing,
    evaluate_endpoint,
    parse_interval,
    reaches_100mw,
)
from config import DB_PATH


EVALUATION_DATE = date.fromisoformat("2026-08-14")
ENDPOINT_NAME = "POWER_AGREEMENT_100MW_WITHIN_48M"
AUDITED_PROJECTS = {
    "DC-JHR-001": "RIGHT_CENSORED",
    "DC-JHR-002": "RIGHT_CENSORED",
    "DC-JHR-003": "OBSERVED_POSITIVE",
    "DC-JHR-006": "OBSERVED_POSITIVE",
    "DC-JHR-007": "UNLABELABLE",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def endpoint_definition():
    return next(endpoint for endpoint in ENDPOINTS if endpoint[0] == ENDPOINT_NAME)


def validate_interval_rules():
    same_month = parse_interval("2024-12", "MONTH")
    require(
        classify_timing(same_month, same_month, 48) == "AMBIGUOUS",
        "same-month prediction and agreement must remain ambiguous",
    )

    digital_boundary = parse_interval("2024-07-12", "DAY")
    digital_agreement = parse_interval("2025-08", "MONTH")
    require(
        classify_timing(digital_boundary, digital_agreement, 48) == "WITHIN",
        "Digital Halo agreement month must be confidently within 48 months",
    )

    straddling_agreement = parse_interval("2028-07", "MONTH")
    july_boundary = parse_interval("2024-07", "MONTH")
    require(
        classify_timing(july_boundary, straddling_agreement, 48)
        == "AMBIGUOUS",
        "an outcome interval crossing the conservative horizon must be ambiguous",
    )


def load_endpoint_inputs():
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        pathways = connection.execute(
            "SELECT * FROM power_pathways ORDER BY project_id"
        ).fetchdf()
        milestones = connection.execute(
            "SELECT * FROM power_pathway_milestones"
        ).fetchdf()
        events = connection.execute("SELECT * FROM connection_events").fetchdf()
        locations = connection.execute(
            "SELECT * FROM dc_project_locations"
        ).fetchdf()
    finally:
        connection.close()
    return pathways, milestones, events, locations


def validate_tm_curated_records(pathways, milestones, events, locations):
    tm_pathways = pathways[pathways["project_id"] == "DC-JHR-003"]
    require(len(tm_pathways) == 1, "expected one TM Nxera pathway row")
    pathway = tm_pathways.iloc[0]
    require(
        pathway["prediction_date"] == "2024-06-15"
        and pathway["prediction_date_precision"] == "DAY"
        and pathway["prediction_context"] == "POST_SITE_COMMITMENT",
        "TM Nxera must use the verified binding-site-commitment boundary",
    )
    require(
        pathway["information_cutoff_date"] == "2024-06-15"
        and pathway["information_cutoff_date_precision"] == "DAY",
        "TM Nxera must use the 15 June 2024 information cutoff",
    )
    require(
        pd.isna(pathway["target_power_mw"])
        and pathway["target_power_measure_type"] == "NOT_FOUND"
        and pathway["target_power_mw_qualifier"] == "NOT_FOUND"
        and pd.isna(pathway["ultimate_power_mw"])
        and pathway["ultimate_power_measure_type"] == "NOT_FOUND"
        and pathway["ultimate_power_mw_qualifier"] == "NOT_FOUND"
        and pathway["pathway_type"] == "NOT_FOUND",
        "TM Nxera must not retain post-cutoff power or pathway features",
    )

    spa_events = events[events["event_id"] == "EVT-JHR-025"]
    require(len(spa_events) == 1, "expected one TM Nxera SPA event")
    spa_event = spa_events.iloc[0]
    require(
        spa_event["project_id"] == "DC-JHR-003"
        and spa_event["event_type"] == "LAND_ACQUISITION_SPA"
        and spa_event["event_date"] == "2024-06-15"
        and spa_event["date_precision"] == "DAY"
        and spa_event["fact_type"] == "VERIFIED"
        and pd.isna(spa_event["supply_mw"]),
        "TM Nxera SPA event semantics must remain source-backed and power-free",
    )

    spa_milestones = milestones[
        milestones["milestone_id"] == "PPM-JHR-003-002"
    ]
    require(len(spa_milestones) == 1, "expected one TM Nxera SPA milestone")
    spa_milestone = spa_milestones.iloc[0]
    require(
        spa_milestone["pathway_id"] == "PP-JHR-003"
        and spa_milestone["milestone_type"] == "LAND_ACQUISITION_SPA"
        and spa_milestone["milestone_status"] == "SIGNED"
        and spa_milestone["milestone_date"] == "2024-06-15"
        and spa_milestone["date_precision"] == "DAY"
        and spa_milestone["connection_event_id"] == "EVT-JHR-025"
        and spa_milestone["fact_type"] == "VERIFIED"
        and pd.isna(spa_milestone["power_mw"])
        and spa_milestone["power_measure_type"] == "NOT_FOUND"
        and spa_milestone["power_mw_qualifier"] == "NOT_FOUND",
        "TM Nxera SPA milestone semantics must remain source-backed and power-free",
    )

    tm_locations = locations[locations["project_id"] == "DC-JHR-003"]
    require(len(tm_locations) == 1, "expected one TM Nxera location row")
    location = tm_locations.iloc[0]
    require(
        location["location_precision"] == "EXACT_PLOT_ID_NO_GEOMETRY"
        and pd.isna(location["latitude"])
        and pd.isna(location["longitude"]),
        "TM Nxera must retain the exact-title-without-geometry classification",
    )


def validate_audited_projects(labels, milestones):
    endpoint_rows = labels[labels["endpoint_name"] == ENDPOINT_NAME]
    audited = endpoint_rows[
        endpoint_rows["project_id"].isin(AUDITED_PROJECTS)
    ].set_index("project_id")

    require(len(labels) == 40, "expected 40 project/endpoint rows")
    require(len(audited) == 5, "expected all five audited projects")
    for project_id, expected_state in AUDITED_PROJECTS.items():
        actual_state = audited.loc[project_id, "label_state"]
        require(
            actual_state == expected_state,
            f"{project_id} expected {expected_state}, found {actual_state}",
        )

    positives = set(
        audited[audited["label_state"] == "OBSERVED_POSITIVE"].index
    )
    require(
        positives == {"DC-JHR-003", "DC-JHR-006"},
        "TM Nxera and Digital Halo must be the strict audited positives",
    )
    require(
        audited.loc["DC-JHR-003", "qualifying_record_id"]
        == "PPM-JHR-003-001",
        "TM Nxera must qualify through its typed 280 MW agreement milestone",
    )
    require(
        audited.loc["DC-JHR-003", "prediction_date"] == "2024-06-15"
        and audited.loc["DC-JHR-003", "prediction_date_precision"] == "DAY",
        "TM Nxera must use the verified 15 June 2024 site-commitment boundary",
    )
    require(
        not bool(audited.loc["DC-JHR-003", "electrical_target_known"]),
        "TM Nxera must not retain the later 280 MW as a prediction-time target",
    )
    require(
        audited.loc["DC-JHR-003", "training_eligibility"]
        == "CALIBRATION_ONLY",
        "TM Nxera must remain calibration-only without usable geometry/spatial features",
    )
    require(
        audited.loc["DC-JHR-006", "qualifying_record_id"]
        == "PPM-JHR-006-003",
        "Digital Halo must qualify through its typed 150 MW ESA milestone",
    )
    require(
        audited.loc["DC-JHR-006", "training_eligibility"]
        == "CALIBRATION_ONLY",
        "Digital Halo must remain calibration-only pending cohort/geometry closure",
    )
    require(
        audited.loc["DC-JHR-001", "label_state"] != "OBSERVED_NEGATIVE",
        "GDS must not become an invented negative",
    )

    digital_milestone = milestones[
        milestones["milestone_id"] == "PPM-JHR-006-003"
    ].iloc[0]
    require(
        digital_milestone["fact_type"] == "VERIFIED"
        and digital_milestone["milestone_type"] == "ESA"
        and digital_milestone["milestone_status"] == "SIGNED"
        and reaches_100mw(
            digital_milestone["power_mw"],
            digital_milestone["power_measure_type"],
            digital_milestone["power_mw_qualifier"],
        ),
        "Digital Halo positive must carry agreement-attributed typed >=100 MW",
    )
    return audited.reset_index()


def validate_no_pathway_mw_fallback(pathways, milestones, events, locations):
    """Model the YTL ambiguity without adding or changing manual evidence."""
    ytl_pathway = next(
        row
        for row in pathways.itertuples(index=False)
        if row.project_id == "DC-JHR-007"
    )._replace(
        target_power_mw=300.0,
        target_power_measure_type="MAXIMUM_DEMAND",
        target_power_mw_qualifier="EXACT",
    )

    synthetic_row = {column: None for column in milestones.columns}
    synthetic_row.update(
        {
            "milestone_id": "REGRESSION-YTL-ESA",
            "pathway_id": "PP-JHR-007",
            "milestone_type": "ESA",
            "milestone_status": "SIGNED",
            "milestone_date": "2023-08-08",
            "date_precision": "DAY",
            "power_mw": None,
            "power_measure_type": "NOT_FOUND",
            "power_mw_qualifier": "NOT_FOUND",
            "delivery_party": "TNB",
            "fact_type": "VERIFIED",
            "notes": (
                "In-memory methodology regression only: the separate 300 MW "
                "pathway value is not attributed to this ESA."
            ),
        }
    )
    synthetic_milestones = pd.concat(
        [milestones, pd.DataFrame([synthetic_row])],
        ignore_index=True,
    )
    ytl_location = next(
        row
        for row in locations.itertuples(index=False)
        if row.project_id == "DC-JHR-007"
    )
    result = evaluate_endpoint(
        ytl_pathway,
        endpoint_definition(),
        synthetic_milestones,
        events,
        ytl_location,
        EVALUATION_DATE,
    )
    require(
        result["label_state"] == "UNLABELABLE",
        "a separate 300 MW pathway value must not promote an untyped ESA",
    )
    require(
        result["qualifying_record_id"] is None,
        "an agreement without attributable MW must not be selected",
    )
    require(
        "pathway values cannot substitute" in result["notes"],
        "the strict-attribution failure must be explicit in output notes",
    )


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Run init_db.py and "
            "load_seed_data.py first."
        )

    validate_interval_rules()
    pathways, milestones, events, locations = load_endpoint_inputs()
    validate_tm_curated_records(pathways, milestones, events, locations)
    labels = build_labels(EVALUATION_DATE)
    audited = validate_audited_projects(labels, milestones)
    validate_no_pathway_mw_fallback(
        pathways,
        milestones,
        events,
        locations,
    )

    print("Historical endpoint methodology v1 regressions:")
    print(
        audited[
            [
                "project_id",
                "label_state",
                "qualifying_record_id",
                "training_eligibility",
            ]
        ].to_string(index=False)
    )
    print("\nAll historical endpoint methodology v1 assertions passed.")


if __name__ == "__main__":
    main()
