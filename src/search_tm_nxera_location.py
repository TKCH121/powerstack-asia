"""Diagnostic search for contextual OSM features near TM Nxera's known plot."""

import geopandas as gpd
import pandas as pd

from config import RAW_DIR


INPUT_FILE = (
    RAW_DIR /
    "johor_named_features.geojson"
)


SEARCH_TERMS = [
    "Eco Botanic",
    "Eco Galleria",
    "University of Reading Malaysia",
    "University of Reading",
    "Dataran MBIP",
    "Dataran Iskandar Puteri",
    "EduCity",
    "Jalan Kampung Lalang",
    "Kampung Lalang",
]


def main():

    print("=" * 70)
    print("POWERSTACK — TM NXERA LOCATION SEARCH")
    print("=" * 70)

    features = gpd.read_file(
        INPUT_FILE
    )

    print()
    print(
        f"Named OSM features loaded: "
        f"{len(features):,}"
    )

    search_columns = [
        column
        for column in [
            "name",
            "name:en",
            "name:ms",
            "alt_name",
            "short_name",
            "operator",
            "brand",
            "description",
        ]
        if column in features.columns
    ]

    features[
        "_search_text"
    ] = (
        features[
            search_columns
        ]
        .fillna("")
        .astype(str)
        .agg(
            " | ".join,
            axis=1,
        )
    )

    representative = (
        features
        .geometry
        .representative_point()
    )

    features[
        "candidate_lat"
    ] = representative.y

    features[
        "candidate_lon"
    ] = representative.x

    features[
        "geometry_type"
    ] = (
        features
        .geometry
        .geom_type
    )

    for term in SEARCH_TERMS:

        print()
        print("=" * 70)
        print(term)
        print("=" * 70)

        mask = (
            features[
                "_search_text"
            ]
            .str.contains(
                term,
                case=False,
                regex=False,
                na=False,
            )
        )

        matches = (
            features[
                mask
            ]
            .copy()
        )

        if matches.empty:

            print(
                "NOT FOUND"
            )

            continue

        display_columns = [
            column
            for column in [
                "name",
                "alt_name",
                "operator",
                "geometry_type",
                "@type",
                "@id",
                "candidate_lat",
                "candidate_lon",
            ]
            if column in matches.columns
        ]

        print(
            matches[
                display_columns
            ]
            .head(30)
            .to_string(
                index=False
            )
        )

    print()
    print("=" * 70)
    print("TM NXERA SEARCH COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
