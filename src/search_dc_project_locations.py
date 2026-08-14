import shutil
import subprocess

import geopandas as gpd
import pandas as pd

from config import RAW_DIR, PROCESSED_DIR


# ============================================================
# FILES
# ============================================================

JOHOR_PBF = (
    RAW_DIR /
    "johor_bbox.osm.pbf"
)

NAMED_PBF = (
    RAW_DIR /
    "johor_named_features.osm.pbf"
)

NAMED_GEOJSON = (
    RAW_DIR /
    "johor_named_features.geojson"
)

OUTPUT_CSV = (
    PROCESSED_DIR /
    "dc_project_location_candidates.csv"
)


# ============================================================
# PROJECT SEARCH TERMS
# ============================================================

PROJECT_SEARCHES = {

    "DC-JHR-001": {
        "project_name":
            "GDS Nusajaya Tech Park Campus",

        "terms": [
            "Nusajaya Tech Park",
            "Nusajaya",
            "GDS",
        ],
    },

    "DC-JHR-002": {
        "project_name":
            "Vantage / former Yondr Sedenak Campus",

        "terms": [
            "Sedenak Tech Park",
            "Sedenak",
            "Yondr",
            "Vantage",
        ],
    },

    "DC-JHR-003": {
        "project_name":
            "TM Nxera Iskandar Puteri Campus",

        "terms": [
            "TM Nxera",
            "Nxera",
            "Iskandar Puteri",
        ],
    },
}


# ============================================================
# HELPERS
# ============================================================

def run_command(command):

    print()
    print("Running:")
    print(" ".join(command))
    print()

    subprocess.run(
        command,
        check=True,
    )


def safe_text(value):

    if pd.isna(value):
        return ""

    return str(value)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "POWERSTACK — DC PROJECT LOCATION SEARCH"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Check input
    # --------------------------------------------------------

    if not JOHOR_PBF.exists():

        raise FileNotFoundError(
            f"Missing Johor OSM file: "
            f"{JOHOR_PBF}"
        )

    if shutil.which("osmium") is None:

        raise RuntimeError(
            "Osmium not found."
        )

    # --------------------------------------------------------
    # 2. Extract named / identifiable OSM objects
    # --------------------------------------------------------

    if not NAMED_PBF.exists():

        print()
        print(
            "Extracting named Johor OSM features..."
        )

        run_command(
            [
                "osmium",
                "tags-filter",
                str(JOHOR_PBF),

                # Match objects containing any
                # of these useful descriptive keys.
                "name",
                "alt_name",
                "short_name",
                "operator",
                "brand",

                "-o",
                str(NAMED_PBF),
                "-O",
            ]
        )

    else:

        print()
        print(
            "Named-feature PBF already exists."
        )

        print(
            "Skipping extraction."
        )

    # --------------------------------------------------------
    # 3. Export to GeoJSON
    # --------------------------------------------------------

    if not NAMED_GEOJSON.exists():

        print()
        print(
            "Converting named features to GeoJSON..."
        )

        run_command(
            [
                "osmium",
                "export",
                str(NAMED_PBF),

                # Preserve useful original OSM attributes.
                "--attributes=type,id",

                # Give each exported geometry a unique ID.
                "--add-unique-id=type_id",

                "-o",
                str(NAMED_GEOJSON),
                "-O",
            ]
        )

    else:

        print()
        print(
            "Named-feature GeoJSON already exists."
        )

        print(
            "Skipping export."
        )

    # --------------------------------------------------------
    # 4. Read data
    # --------------------------------------------------------

    print()
    print(
        "Loading named Johor features..."
    )

    features = gpd.read_file(
        NAMED_GEOJSON
    )

    print(
        f"Named features loaded: "
        f"{len(features):,}"
    )

    print(
        f"CRS: {features.crs}"
    )

    # --------------------------------------------------------
    # 5. Determine searchable columns
    # --------------------------------------------------------

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

    print()
    print(
        "Searchable fields:"
    )

    for column in search_columns:

        print(
            f"  - {column}"
        )

    # Combine them into one searchable text field.
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

    # --------------------------------------------------------
    # 6. Representative coordinates
    # --------------------------------------------------------

    # We are NOT claiming this is always the site's
    # exact entrance or building coordinate.
    #
    # For a park polygon it represents a point safely
    # inside the mapped geometry.

    representative = (
        features.geometry
        .representative_point()
    )

    features[
        "candidate_lon"
    ] = representative.x

    features[
        "candidate_lat"
    ] = representative.y

    features[
        "geometry_type"
    ] = (
        features.geometry
        .geom_type
    )

    # --------------------------------------------------------
    # 7. Search for each validation project
    # --------------------------------------------------------

    results = []

    for (
        project_id,
        project_config,
    ) in PROJECT_SEARCHES.items():

        print()
        print("=" * 70)

        print(
            f"{project_id} — "
            f"{project_config['project_name']}"
        )

        print("=" * 70)

        project_matches = []

        for term in (
            project_config[
                "terms"
            ]
        ):

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

                continue

            matches[
                "project_id"
            ] = project_id

            matches[
                "project_name_search"
            ] = (
                project_config[
                    "project_name"
                ]
            )

            matches[
                "matched_term"
            ] = term

            project_matches.append(
                matches
            )

        if not project_matches:

            print()
            print(
                "NO OSM MATCHES FOUND"
            )

            continue

        project_result = (
            pd.concat(
                project_matches,
                ignore_index=True,
            )
        )

        # The same feature can match several terms.
        # Remove duplicate search results.
        dedupe_columns = [
            "candidate_lon",
            "candidate_lat",
            "geometry_type",
        ]

        if "name" in project_result.columns:

            dedupe_columns.append(
                "name"
            )

        project_result = (
            project_result
            .drop_duplicates(
                subset=dedupe_columns,
                keep="first",
            )
        )

        # ----------------------------------------------------
        # Display useful columns
        # ----------------------------------------------------

        display_columns = [
            column
            for column in [
                "project_id",
                "matched_term",
                "name",
                "alt_name",
                "operator",
                "brand",
                "geometry_type",
                "@type",
                "@id",
                "candidate_lat",
                "candidate_lon",
            ]
            if column in project_result.columns
        ]

        print()
        print(
            project_result[
                display_columns
            ]
            .head(30)
            .to_string(
                index=False
            )
        )

        results.append(
            project_result
        )

    # --------------------------------------------------------
    # 8. Save combined candidate results
    # --------------------------------------------------------

    if not results:

        raise RuntimeError(
            "No project location candidates found."
        )

    all_results = (
        pd.concat(
            results,
            ignore_index=True,
        )
    )

    output_columns = [
        column
        for column in [
            "project_id",
            "project_name_search",
            "matched_term",
            "name",
            "name:en",
            "name:ms",
            "alt_name",
            "short_name",
            "operator",
            "brand",
            "@type",
            "@id",
            "geometry_type",
            "candidate_lat",
            "candidate_lon",
        ]
        if column in all_results.columns
    ]

    all_results[
        output_columns
    ].to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print()
    print("=" * 70)

    print(
        "LOCATION SEARCH COMPLETE"
    )

    print("=" * 70)

    print()
    print(
        f"Candidate table saved to:"
    )

    print(
        OUTPUT_CSV
    )


if __name__ == "__main__":
    main()