"""Validate curated project-polygon evidence and its source manifest."""

from __future__ import annotations

import json
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

from powerstack_utils import (
    EVIDENCE_FACT_TYPES,
    PROJECTED_CRS,
    geometry_hash,
)


ROOT = Path(__file__).resolve().parents[1]
MANUAL_DIR = ROOT / "data" / "manual"
GEOMETRY_PATH = MANUAL_DIR / "dc_project_geometries_seed.geojson"
SOURCE_PATH = MANUAL_DIR / "dc_project_geometry_sources_seed.csv"
LOCATION_PATH = MANUAL_DIR / "dc_project_locations_seed.csv"

REQUIRED_GEOMETRY_COLUMNS = {
    "geometry_id",
    "project_id",
    "geometry_classification",
    "source_authority",
    "source_service",
    "source_layer",
    "source_feature_id",
    "source_global_id",
    "ptd",
    "title_reference",
    "candidate_lot",
    "upi",
    "title_succession_status",
    "original_crs",
    "stored_crs",
    "calculated_area_crs",
    "source_area_m2",
    "calculated_area_m2",
    "title_area_m2",
    "area_difference_pct",
    "calculated_area_difference_pct",
    "effective_date",
    "effective_date_precision",
    "effective_date_status",
    "retrieval_date",
    "fact_type",
    "source_url",
    "geometry_hash",
    "notes",
    "geometry",
}

REQUIRED_SOURCE_COLUMNS = {
    "geometry_source_id",
    "geometry_id",
    "source_role",
    "source_authority",
    "source_name",
    "source_url",
    "source_date",
    "retrieval_date",
    "fact_type",
    "notes",
}

EXPECTED = {
    "GEO-JHR-003-001": {
        "project_id": "DC-JHR-003",
        "classification": "BOUNDED_PARCEL",
        "ptd": "213429",
        "source_feature_id": "377272",
        "geometry_hash": (
            "20a28fb23bb96e42f36d3690e48e848d7796d808873e3ebdd"
            "403800b703a9769"
        ),
        "source_area_difference_pct": -10.922188229522655,
    },
    "GEO-JHR-006-001": {
        "project_id": "DC-JHR-006",
        "classification": "AUTHORITATIVE_PROJECT_POLYGON",
        "ptd": "227197",
        "source_feature_id": "344541",
        "geometry_hash": (
            "42c7e295cf2688143250f557111d644faa6757a4d886f37b8"
            "e5c5d3e46d10e35"
        ),
        "source_area_difference_pct": -0.3385852579710136,
    },
}


def require(condition: bool, message: str) -> None:
    """Raise a compact validation error when a contract is violated."""
    if not condition:
        raise ValueError(message)


def main() -> None:
    with GEOMETRY_PATH.open(encoding="utf-8") as stream:
        geojson = json.load(stream)

    require(
        geojson.get("type") == "FeatureCollection",
        "Project geometry file is not a GeoJSON FeatureCollection.",
    )
    geometry_rows = []
    for feature in geojson.get("features", []):
        properties = dict(feature.get("properties") or {})
        require(
            feature.get("id") == properties.get("geometry_id"),
            "GeoJSON feature id must equal geometry_id.",
        )
        properties["geometry"] = shape(feature.get("geometry"))
        geometry_rows.append(properties)

    geometries = gpd.GeoDataFrame(
        geometry_rows,
        geometry="geometry",
        crs="EPSG:4326",
    )
    sources = pd.read_csv(SOURCE_PATH, dtype=str)
    locations = pd.read_csv(LOCATION_PATH, dtype=str)

    require(
        REQUIRED_GEOMETRY_COLUMNS <= set(geometries.columns),
        "Project geometry GeoJSON is missing required properties.",
    )
    require(
        REQUIRED_SOURCE_COLUMNS <= set(sources.columns),
        "Project geometry source manifest is missing required columns.",
    )
    require(len(geometries) == len(EXPECTED), "Unexpected geometry row count.")
    require(geometries.crs is not None, "Project geometry CRS is missing.")
    require(
        geometries.crs.to_epsg() == 4326,
        f"Expected stored EPSG:4326, found {geometries.crs}.",
    )
    require(geometries["geometry_id"].is_unique, "Duplicate geometry_id.")
    require(
        sources["geometry_source_id"].is_unique,
        "Duplicate geometry_source_id.",
    )
    require(
        set(geometries["fact_type"]) <= EVIDENCE_FACT_TYPES,
        "Geometry contains an invalid fact_type.",
    )
    require(
        set(sources["fact_type"]) <= EVIDENCE_FACT_TYPES,
        "Geometry source manifest contains an invalid fact_type.",
    )

    location_projects = set(locations["project_id"])
    source_geometry_ids = set(sources["geometry_id"])
    require(
        set(geometries["project_id"]) <= location_projects,
        "A project geometry does not join to dc_project_locations.",
    )
    require(
        source_geometry_ids == set(geometries["geometry_id"]),
        "Geometry/source manifest IDs do not match.",
    )

    calculated_areas = geometries.to_crs(PROJECTED_CRS).geometry.area

    for index, row in geometries.iterrows():
        geometry_id = row["geometry_id"]
        require(geometry_id in EXPECTED, f"Unexpected geometry {geometry_id}.")
        expected = EXPECTED[geometry_id]

        require(row.geometry.geom_type == "Polygon", f"{geometry_id} is not a Polygon.")
        require(not row.geometry.is_empty, f"{geometry_id} geometry is empty.")
        require(row.geometry.is_valid, f"{geometry_id} geometry is invalid.")
        require(row["project_id"] == expected["project_id"], f"{geometry_id} project mismatch.")
        require(
            row["geometry_classification"] == expected["classification"],
            f"{geometry_id} classification mismatch.",
        )
        require(str(row["ptd"]) == expected["ptd"], f"{geometry_id} PTD mismatch.")
        require(
            str(row["source_feature_id"]) == expected["source_feature_id"],
            f"{geometry_id} source feature mismatch.",
        )
        require(row["stored_crs"] == "EPSG:4326", f"{geometry_id} stored CRS mismatch.")
        require(row["calculated_area_crs"] == PROJECTED_CRS, f"{geometry_id} area CRS mismatch.")
        require(
            row["title_succession_status"] == "NOT_FOUND",
            f"{geometry_id} must not claim a title successor.",
        )
        require(
            row["effective_date_status"] == "NOT_FOUND"
            and pd.isna(row["effective_date"])
            and pd.isna(row["effective_date_precision"]),
            f"{geometry_id} must preserve the unknown effective date.",
        )

        actual_hash = geometry_hash(row.geometry)
        require(actual_hash == row["geometry_hash"], f"{geometry_id} stored hash is stale.")
        require(actual_hash == expected["geometry_hash"], f"{geometry_id} geometry changed.")

        calculated_area = float(calculated_areas.iloc[index])
        require(
            math.isclose(
                calculated_area,
                float(row["calculated_area_m2"]),
                rel_tol=0,
                abs_tol=0.01,
            ),
            f"{geometry_id} calculated area does not reproduce.",
        )

        source_difference = (
            float(row["source_area_m2"]) / float(row["title_area_m2"])
            - 1
        ) * 100
        calculated_difference = (
            calculated_area / float(row["title_area_m2"]) - 1
        ) * 100
        require(
            math.isclose(
                source_difference,
                float(row["area_difference_pct"]),
                rel_tol=0,
                abs_tol=1e-9,
            ),
            f"{geometry_id} source/title area comparison is stale.",
        )
        require(
            math.isclose(
                calculated_difference,
                float(row["calculated_area_difference_pct"]),
                rel_tol=0,
                abs_tol=1e-9,
            ),
            f"{geometry_id} calculated/title area comparison is stale.",
        )
        require(
            math.isclose(
                source_difference,
                expected["source_area_difference_pct"],
                rel_tol=0,
                abs_tol=1e-9,
            ),
            f"{geometry_id} baseline area discrepancy changed.",
        )

        primary_sources = sources[
            (sources["geometry_id"] == geometry_id)
            & (sources["source_role"] == "PRIMARY_GEOMETRY")
        ]
        require(
            len(primary_sources) == 1,
            f"{geometry_id} requires exactly one primary geometry source.",
        )

        print(
            f"PASS {geometry_id}: {row['geometry_classification']}; "
            f"valid Polygon; hash {actual_hash}; "
            f"area {calculated_area:.2f} m2"
        )

    print(
        f"Validated {len(geometries)} project geometries and "
        f"{len(sources)} source records."
    )


if __name__ == "__main__":
    main()
