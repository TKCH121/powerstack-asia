"""Small shared helpers for PowerStack's evidence-first GIS pipeline."""

import hashlib
import re
import subprocess

import pandas as pd


PROJECTED_CRS = "EPSG:3375"
EVIDENCE_FACT_TYPES = frozenset({
    "VERIFIED",
    "DERIVED",
    "INFERRED",
    "NOT_FOUND",
})
PUBLIC_MAP_SOURCE_TYPE = "PUBLIC_MAP"


def extract_voltages_kv(value):
    """Return every explicitly stated voltage from an OSM value, in kV."""
    if value is None:
        return set()

    try:
        if pd.isna(value):
            return set()
    except (TypeError, ValueError):
        pass

    return {
        int(number) / 1000
        for number in re.findall(r"\d+", str(value))
    }


def max_voltage_kv(value):
    """Return the highest explicitly stated voltage, or ``None`` if absent."""
    voltages = extract_voltages_kv(value)
    return max(voltages) if voltages else None


def has_voltage(value, target_kv):
    """Return whether an OSM value explicitly includes ``target_kv``."""
    return target_kv in extract_voltages_kv(value)


def geometry_hash(geometry):
    """Return a stable SHA-256 fingerprint for an exact geometry."""
    if geometry is None:
        return None

    return hashlib.sha256(geometry.normalize().wkb).hexdigest()


def run_command(command):
    """Run an external command and stop immediately if it fails."""
    print()
    print("Running:")
    print(" ".join(command))
    print()
    subprocess.run(command, check=True)


def nearest_feature_join(
    candidates,
    targets,
    *,
    candidate_id,
    distance_column,
    tie_break_columns=(),
):
    """Return one deterministic nearest target row for every candidate."""
    import geopandas as gpd

    joined = gpd.sjoin_nearest(
        candidates[[candidate_id, "geometry"]],
        targets,
        how="left",
        distance_col=distance_column,
    )

    sort_columns = [candidate_id, distance_column, *tie_break_columns]
    sort_columns = [
        column for column in sort_columns if column in joined.columns
    ]

    return (
        joined
        .sort_values(sort_columns)
        .drop_duplicates(subset=candidate_id, keep="first")
    )
