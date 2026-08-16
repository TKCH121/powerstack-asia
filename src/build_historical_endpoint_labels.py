"""Derive conservative historical endpoint labels from the local DuckDB."""

from __future__ import annotations

import argparse
import calendar
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from config import DB_PATH, PROCESSED_DIR


DEFAULT_EVALUATION_DATE = "2026-08-14"
DEFAULT_OUTPUT_FILE = (
    PROCESSED_DIR / "research" / "historical_endpoint_labels.csv"
)
HISTORICAL_OSM_ROOT = PROCESSED_DIR / "research" / "historical_osm"

ENDPOINTS = (
    ("ESA_WITHIN_12M", 12, "ESA"),
    ("ESA_WITHIN_24M", 24, "ESA"),
    ("UTILITY_COMMISSIONING_WITHIN_24M", 24, "UTILITY"),
    ("FIRST_PHASE_OPERATION_WITHIN_24M", 24, "OPERATION"),
    ("POWER_AGREEMENT_100MW_WITHIN_48M", 48, "POWER_AGREEMENT_100MW"),
)
MILESTONE_MAPPINGS = {
    "ESA": {
        ("ESA", "SIGNED"),
        ("ELECTRICITY_SUPPLY_AGREEMENT", "AGREED"),
        ("ELECTRICITY_SUPPLY_AGREEMENT", "SIGNED"),
    },
    "UTILITY": {("UTILITY_SUPPLY_COMMISSIONING", "COMMISSIONED")},
    "OPERATION": {
        ("PHASE_ONE_OPERATION", "OPERATING"),
        ("PHASE_ONE_DELIVERY", "DELIVERED"),
    },
}
EVENT_MAPPINGS = {
    "ESA": {"ESA_SIGNED", "ELECTRICITY_SUPPLY_AGREEMENT"},
    "UTILITY": {"UTILITY_SUPPLY_COMMISSIONED"},
    "OPERATION": {
        "PHASE_ONE_OPERATION_STARTED",
        "PHASE_ONE_DELIVERED",
    },
}
ALLOWED_POWER_MEASURES = {
    "ELECTRICAL_SUPPLY",
    "MAXIMUM_DEMAND",
    "CONTRACTED_CAPACITY",
    "CONNECTION_CAPACITY",
}
KNOWN_QUALIFIERS = {
    "EXACT",
    "APPROXIMATE",
    "GREATER_THAN",
    "LESS_THAN",
}
THRESHOLD_QUALIFIERS = {"EXACT", "GREATER_THAN"}
LABEL_STATES = {
    "OBSERVED_POSITIVE",
    "OBSERVED_NEGATIVE",
    "RIGHT_CENSORED",
    "UNLABELABLE",
}


@dataclass(frozen=True)
class DateInterval:
    raw: str
    precision: str
    start: date
    end: date


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build derived historical endpoint labels."
    )
    parser.add_argument("--evaluation-date", default=DEFAULT_EVALUATION_DATE)
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
    )
    return parser.parse_args()


def parse_interval(raw_value, precision) -> DateInterval:
    """Parse a source date without inventing day precision."""
    if pd.isna(raw_value) or pd.isna(precision):
        raise ValueError("date and precision must both be present")
    raw = str(raw_value).strip()
    precision = str(precision).strip().upper()
    if precision == "DAY":
        parsed = date.fromisoformat(raw)
        return DateInterval(raw, precision, parsed, parsed)
    if precision == "MONTH":
        parts = raw.split("-")
        if len(parts) != 2:
            raise ValueError(f"invalid MONTH value: {raw}")
        year, month = map(int, parts)
        last_day = calendar.monthrange(year, month)[1]
        return DateInterval(
            raw,
            precision,
            date(year, month, 1),
            date(year, month, last_day),
        )
    if precision == "YEAR":
        year = int(raw)
        return DateInterval(raw, precision, date(year, 1, 1), date(year, 12, 31))
    raise ValueError(f"unsupported date precision: {precision}")


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def classify_timing(prediction, event, horizon_months):
    """Classify timing without resolving interval dates to assumed days."""
    if event.end < prediction.start:
        return "BEFORE"
    if event.start <= prediction.end:
        return "AMBIGUOUS"
    earliest_end = add_months(prediction.start, horizon_months)
    latest_end = add_months(prediction.end, horizon_months)
    if event.end <= earliest_end:
        return "WITHIN"
    if event.start > latest_end:
        return "OUTSIDE"
    return "AMBIGUOUS"


def elapsed_text(prediction, event):
    if prediction.raw == event.raw and prediction.precision == event.precision:
        if prediction.precision == "DAY":
            return "0 days"
        return f"0 months (same recorded {prediction.precision.lower()})"
    minimum = (event.start - prediction.end).days
    maximum = (event.end - prediction.start).days
    return f"{minimum} days" if minimum == maximum else f"{minimum}-{maximum} days"


def optional_float(value):
    return None if pd.isna(value) else float(value)


def collect_candidates(milestones, events, pathway_id, project_id, kind):
    """Prefer typed milestones and use connection events only as fallback."""
    mapping_kind = "ESA" if kind == "POWER_AGREEMENT_100MW" else kind
    project_milestones = milestones[
        (milestones["pathway_id"] == pathway_id)
        & (milestones["fact_type"] == "VERIFIED")
    ]
    candidates = []
    for row in project_milestones.itertuples(index=False):
        if (row.milestone_type, row.milestone_status) not in MILESTONE_MAPPINGS[
            mapping_kind
        ]:
            continue
        candidates.append(
            {
                "id": row.milestone_id,
                "table": "power_pathway_milestones",
                "type": row.milestone_type,
                "status": row.milestone_status,
                "date": parse_interval(row.milestone_date, row.date_precision),
                "power_mw": optional_float(row.power_mw),
                "measure_type": row.power_measure_type,
                "qualifier": row.power_mw_qualifier,
            }
        )
    if candidates:
        return sorted(candidates, key=lambda item: (item["date"].start, item["id"]))

    project_events = events[
        (events["project_id"] == project_id)
        & (events["fact_type"] == "VERIFIED")
    ]
    for row in project_events.itertuples(index=False):
        if row.event_type not in EVENT_MAPPINGS[mapping_kind]:
            continue
        candidates.append(
            {
                "id": row.event_id,
                "table": "connection_events",
                "type": row.event_type,
                "status": "",
                "date": parse_interval(row.event_date, row.date_precision),
                # connection_events lacks measure semantics, so its MW is
                # deliberately unavailable to the 100 MW threshold logic.
                "power_mw": None,
                "measure_type": None,
                "qualifier": None,
            }
        )
    return sorted(candidates, key=lambda item: (item["date"].start, item["id"]))


def power_known(value, measure_type, qualifier):
    return (
        value is not None
        and not pd.isna(value)
        and measure_type in ALLOWED_POWER_MEASURES
        and qualifier in KNOWN_QUALIFIERS
    )


def reaches_100mw(value, measure_type, qualifier):
    return (
        power_known(value, measure_type, qualifier)
        and qualifier in THRESHOLD_QUALIFIERS
        and float(value) >= 100.0
    )


def pathway_power_values(pathway):
    return (
        (
            optional_float(pathway.target_power_mw),
            pathway.target_power_measure_type,
            pathway.target_power_mw_qualifier,
        ),
        (
            optional_float(pathway.ultimate_power_mw),
            pathway.ultimate_power_measure_type,
            pathway.ultimate_power_mw_qualifier,
        ),
    )


def boundary_usable(pathway, evaluation_date):
    try:
        prediction = parse_interval(
            pathway.prediction_date,
            pathway.prediction_date_precision,
        )
        if pathway.assessment_scope != "EX_ANTE" or prediction.start > evaluation_date:
            return False
        if not pd.isna(pathway.information_cutoff_date):
            cutoff = parse_interval(
                pathway.information_cutoff_date,
                pathway.information_cutoff_date_precision,
            )
            if cutoff.end > prediction.end:
                return False
        return True
    except (TypeError, ValueError):
        return False


def site_usable(location):
    return bool(
        location
        and location.fact_type == "VERIFIED"
        and location.location_precision == "SITE_COORDINATE"
        and not pd.isna(location.latitude)
        and not pd.isna(location.longitude)
    )


def spatial_features_available(pathway):
    if pd.isna(pathway.information_cutoff_date):
        return False
    project_root = HISTORICAL_OSM_ROOT / pathway.project_id
    for feature_file in project_root.glob(
        "*/historical_project_features.csv"
    ):
        try:
            features = pd.read_csv(feature_file, dtype=str)
        except (OSError, pd.errors.ParserError):
            continue
        required = {
            "project_id",
            "information_cutoff_date",
            "historical_topology_status",
        }
        if features.empty or not required.issubset(features.columns):
            continue
        matches = features[
            (features["project_id"] == pathway.project_id)
            & (
                features["information_cutoff_date"]
                == str(pathway.information_cutoff_date)
            )
            & (features["historical_topology_status"] == "OSM_MAPPED_AS_OF_CUTOFF")
        ]
        if not matches.empty:
            return True
    return False


def excluded_evidence_note(milestones, events, pathway_id, project_id, kind):
    milestone_types = set(
        milestones.loc[
            (milestones["pathway_id"] == pathway_id)
            & (milestones["fact_type"] == "VERIFIED"),
            "milestone_type",
        ]
    )
    event_types = set(
        events.loc[
            (events["project_id"] == project_id)
            & (events["fact_type"] == "VERIFIED"),
            "event_type",
        ]
    )
    notes = []
    if kind in {"ESA", "POWER_AGREEMENT_100MW"} and (
        "POWER_PARTNERSHIP" in milestone_types
        or "ESA_OR_POWER_PARTNERSHIP" in event_types
    ):
        notes.append("POWER_PARTNERSHIP is not automatically mapped to ESA")
    if kind == "UTILITY" and (
        "SUBSTATION_ENERGISATION" in milestone_types
        or "SUBSTATION_ENERGISED" in event_types
    ):
        notes.append(
            "substation energisation does not prove utility supply commissioning"
        )
    if kind == "OPERATION" and "FIRST_IT_HANDOVER" in event_types:
        notes.append("IT handover alone is not mapped to first-phase operation")
    return "; ".join(notes)


def explicit_negative_candidate(kind, candidates, timings):
    """Recognize explicit first-operation timing after the horizon."""
    if kind != "OPERATION":
        return None
    for candidate in candidates:
        explicit_first_operation = (
            candidate["type"] == "PHASE_ONE_OPERATION"
            and candidate["status"] == "OPERATING"
        ) or candidate["type"] == "PHASE_ONE_OPERATION_STARTED"
        if explicit_first_operation and timings[candidate["id"]] == "OUTSIDE":
            return candidate
    return None


def training_eligibility(
    label_state,
    prediction_ok,
    location_ok,
    spatial_ok,
):
    """Assess eligibility using labels and prediction-time features only."""
    # The fixed 100 MW threshold belongs to the outcome definition. A future
    # project-specific-target model would add an ex-ante requested-power gate.
    if label_state not in {"OBSERVED_POSITIVE", "OBSERVED_NEGATIVE"}:
        return "NOT_READY"
    if not prediction_ok:
        return "NOT_READY"
    if location_ok and spatial_ok:
        return "TRAINING_READY_FOR_ENDPOINT"
    return "CALIBRATION_ONLY"


def evaluate_endpoint(
    pathway,
    endpoint,
    milestones,
    events,
    location,
    evaluation_date,
):
    endpoint_name, horizon_months, kind = endpoint
    prediction = parse_interval(
        pathway.prediction_date,
        pathway.prediction_date_precision,
    )
    prediction_ok = boundary_usable(pathway, evaluation_date)
    location_ok = site_usable(location)
    spatial_ok = spatial_features_available(pathway)
    pathway_values = pathway_power_values(pathway)
    electrical_target_known = any(power_known(*value) for value in pathway_values)
    candidates = collect_candidates(
        milestones,
        events,
        pathway.pathway_id,
        pathway.project_id,
        kind,
    )
    agreement_threshold_note = ""

    if kind == "POWER_AGREEMENT_100MW":
        threshold_candidates = [
            candidate
            for candidate in candidates
            if reaches_100mw(
                candidate["power_mw"],
                candidate["measure_type"],
                candidate["qualifier"],
            )
        ]
        candidates = threshold_candidates
        if not threshold_candidates:
            if electrical_target_known:
                agreement_threshold_note = (
                    "A separate pathway-level electrical value exists, but "
                    "no qualifying agreement record explicitly attributes "
                    ">=100 MW to that agreement; pathway values cannot "
                    "substitute for agreement quantity."
                )
            else:
                agreement_threshold_note = (
                    "No qualifying agreement record explicitly attributes a "
                    "typed, project-specific >=100 MW electrical quantity; "
                    "IT capacity and untyped event MW cannot qualify."
                )

    timings = {
        candidate["id"]: classify_timing(
            prediction,
            candidate["date"],
            horizon_months,
        )
        for candidate in candidates
    }
    within = [candidate for candidate in candidates if timings[candidate["id"]] == "WITHIN"]
    ambiguous = [
        candidate
        for candidate in candidates
        if timings[candidate["id"]] in {"AMBIGUOUS", "BEFORE"}
    ]
    selected = None
    elapsed = None

    if within:
        selected = within[0]
        label_state = "OBSERVED_POSITIVE"
        elapsed = elapsed_text(prediction, selected["date"])
        reason = (
            f"Verified {selected['type']} outcome falls confidently within "
            f"the {horizon_months}-month horizon."
        )
        notes = "The source date precision is retained; no day was invented."
    elif ambiguous:
        selected = ambiguous[0]
        label_state = "UNLABELABLE"
        elapsed = elapsed_text(prediction, selected["date"])
        reason = (
            "Date precision prevents confident placement of the qualifying "
            "outcome relative to time zero or the horizon."
        )
        notes = "The ambiguity is retained rather than resolved by an assumed day."
    else:
        latest_horizon_end = add_months(prediction.end, horizon_months)
        negative = explicit_negative_candidate(kind, candidates, timings)
        if negative and evaluation_date >= latest_horizon_end:
            selected = negative
            label_state = "OBSERVED_NEGATIVE"
            elapsed = elapsed_text(prediction, selected["date"])
            reason = (
                "Verified first-phase operation commenced after the complete "
                f"{horizon_months}-month horizon."
            )
            notes = (
                "Explicit commencement timing supports non-occurrence within "
                "the earlier horizon."
            )
        elif evaluation_date < latest_horizon_end:
            label_state = "RIGHT_CENSORED"
            reason = (
                "No qualifying positive is observed and the full horizon has "
                f"not elapsed by {evaluation_date.isoformat()}."
            )
            notes = f"Latest possible horizon end is {latest_horizon_end.isoformat()}."
        else:
            outside = [
                candidate
                for candidate in candidates
                if timings[candidate["id"]] == "OUTSIDE"
            ]
            selected = outside[0] if outside else None
            if selected:
                elapsed = elapsed_text(prediction, selected["date"])
            label_state = "UNLABELABLE"
            reason = (
                "The horizon elapsed, but current repository evidence does "
                "not explicitly establish non-occurrence within it."
            )
            notes = "Missing milestone is not treated as a negative outcome."

    excluded = excluded_evidence_note(
        milestones,
        events,
        pathway.pathway_id,
        pathway.project_id,
        kind,
    )
    if excluded:
        notes = f"{notes} {excluded}."
    if agreement_threshold_note:
        notes = f"{notes} {agreement_threshold_note}"
    return result_row(
        pathway,
        endpoint,
        evaluation_date,
        label_state,
        selected,
        elapsed,
        prediction_ok,
        location_ok,
        spatial_ok,
        electrical_target_known,
        reason,
        notes,
    )


def result_row(
    pathway,
    endpoint,
    evaluation_date,
    label_state,
    candidate,
    elapsed,
    prediction_ok,
    location_ok,
    spatial_ok,
    electrical_target_known,
    reason,
    notes,
):
    endpoint_name, horizon_months, kind = endpoint
    label_usable = label_state in {"OBSERVED_POSITIVE", "OBSERVED_NEGATIVE"}
    if label_state not in LABEL_STATES:
        raise RuntimeError(f"invalid label state: {label_state}")
    return {
        "project_id": pathway.project_id,
        "endpoint_name": endpoint_name,
        "prediction_date": pathway.prediction_date,
        "prediction_date_precision": pathway.prediction_date_precision,
        "horizon_months": horizon_months,
        "evaluation_date": evaluation_date.isoformat(),
        "label_state": label_state,
        "event_date": candidate["date"].raw if candidate else None,
        "event_date_precision": candidate["date"].precision if candidate else None,
        "qualifying_record_id": candidate["id"] if candidate else None,
        "qualifying_source_table": candidate["table"] if candidate else None,
        "elapsed_days_or_months": elapsed,
        "label_fact_type": "DERIVED",
        "prediction_boundary_usable": prediction_ok,
        "location_usable": location_ok,
        "historical_spatial_features_available": spatial_ok,
        "electrical_target_known": electrical_target_known,
        "endpoint_label_usable": label_usable,
        "training_eligibility": training_eligibility(
            label_state,
            prediction_ok,
            location_ok,
            spatial_ok,
        ),
        "reason": reason,
        "notes": notes,
    }


def build_labels(evaluation_date):
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Run init_db.py and load_seed_data.py."
        )
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

    if pathways["project_id"].duplicated().any():
        raise RuntimeError("each project must have exactly one pathway row")
    location_lookup = {
        row.project_id: row for row in locations.itertuples(index=False)
    }
    rows = []
    for pathway in pathways.itertuples(index=False):
        for endpoint in ENDPOINTS:
            rows.append(
                evaluate_endpoint(
                    pathway,
                    endpoint,
                    milestones,
                    events,
                    location_lookup.get(pathway.project_id),
                    evaluation_date,
                )
            )
    labels = pd.DataFrame(rows)
    if len(labels) != len(pathways) * len(ENDPOINTS):
        raise RuntimeError("one label is required for every project/endpoint pair")
    if labels.duplicated(["project_id", "endpoint_name"]).any():
        raise RuntimeError("duplicate project/endpoint label rows")
    return labels


def print_report(labels, output_file):
    print("\nEndpoint results:")
    print(
        labels[
            [
                "project_id",
                "endpoint_name",
                "label_state",
                "event_date",
                "training_eligibility",
                "reason",
            ]
        ].to_string(index=False)
    )
    print("\nCounts by endpoint and label state:")
    counts = (
        labels.groupby(["endpoint_name", "label_state"])
        .size()
        .rename("row_count")
        .reset_index()
    )
    print(counts.to_string(index=False))
    print("\nTraining-ready counts by endpoint:")
    ready = (
        labels[
            labels["training_eligibility"] == "TRAINING_READY_FOR_ENDPOINT"
        ]
        .groupby("endpoint_name")
        .size()
        .reindex([endpoint[0] for endpoint in ENDPOINTS], fill_value=0)
        .rename("training_ready_count")
        .reset_index()
    )
    print(ready.to_string(index=False))
    print(f"\nWrote {len(labels)} derived labels to {output_file}")


def main():
    args = parse_args()
    evaluation_date = date.fromisoformat(args.evaluation_date)
    labels = build_labels(evaluation_date)
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    labels.to_csv(args.output_file, index=False)
    print_report(labels, args.output_file)


if __name__ == "__main__":
    main()
