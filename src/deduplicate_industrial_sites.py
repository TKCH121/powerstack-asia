import geopandas as gpd
import pandas as pd

from config import PROCESSED_DIR
from powerstack_utils import geometry_hash


INPUT_FILE = (
    PROCESSED_DIR /
    "johor_industrial_grid_features.parquet"
)

OUTPUT_PARQUET = (
    PROCESSED_DIR /
    "johor_industrial_grid_features_clean.parquet"
)

OUTPUT_CSV = (
    PROCESSED_DIR /
    "johor_industrial_grid_features_clean.csv"
)

CONFLICT_FILE = (
    PROCESSED_DIR /
    "industrial_duplicate_conflicts.csv"
)


SOURCE_METADATA_COLUMNS = [
    "gunatanah1",
    "kod_gtn",
    "tahun_data",
    "lot_upi",
    "luas_hekta",
    "nama_ranca",
    "negeri_nam",
    "daerah_nam",
    "mukim_name",
    "seksyen_na",
    "pbt_name",
]


def normalized_value(value):
    """
    Normalize metadata for duplicate comparison.

    Empty strings and missing values are treated consistently.
    """

    if pd.isna(value):
        return "<MISSING>"

    if isinstance(value, str):
        value = value.strip()

        if value == "":
            return "<MISSING>"

    return str(value)


def main():

    print("=" * 70)
    print("POWERSTACK — INDUSTRIAL SITE DEDUPLICATION")
    print("=" * 70)

    sites = gpd.read_parquet(
        INPUT_FILE
    )

    print()
    print(
        f"Input candidate rows: "
        f"{len(sites):,}"
    )

    # --------------------------------------------------
    # 1. Geometry fingerprint
    # --------------------------------------------------

    sites[
        "geometry_hash"
    ] = (
        sites.geometry
        .apply(
            geometry_hash
        )
    )

    sites[
        "source_duplicate_count"
    ] = (
        sites.groupby(
            "geometry_hash"
        )[
            "geometry_hash"
        ]
        .transform("size")
    )

    duplicate_rows = (
        sites[
            sites[
                "source_duplicate_count"
            ] > 1
        ]
        .copy()
    )

    print(
        f"Rows involved in duplicate groups: "
        f"{len(duplicate_rows):,}"
    )

    print(
        f"Duplicate geometry groups: "
        f"{duplicate_rows['geometry_hash'].nunique():,}"
    )

    # --------------------------------------------------
    # 2. Check duplicate metadata consistency
    # --------------------------------------------------

    metadata_columns = [
        column
        for column in SOURCE_METADATA_COLUMNS
        if column in sites.columns
    ]

    conflict_hashes = []

    for geometry_id, group in (
        duplicate_rows
        .groupby("geometry_hash")
    ):

        group_has_conflict = False

        for column in metadata_columns:

            unique_values = {
                normalized_value(value)
                for value in group[column]
            }

            if len(unique_values) > 1:

                group_has_conflict = True

                break

        if group_has_conflict:

            conflict_hashes.append(
                geometry_id
            )

    print()
    print(
        f"Duplicate groups with conflicting "
        f"source metadata: "
        f"{len(conflict_hashes):,}"
    )

    # --------------------------------------------------
    # 3. Stop if any conflicts exist
    # --------------------------------------------------

    if conflict_hashes:

        conflicts = (
            duplicate_rows[
                duplicate_rows[
                    "geometry_hash"
                ]
                .isin(
                    conflict_hashes
                )
            ]
            .copy()
        )

        conflict_columns = [
            column
            for column in (
                [
                    "site_id",
                    "OBJECTID",
                    "geometry_hash",
                ]
                +
                metadata_columns
                +
                [
                    "calculated_area_ha",
                    "distance_275kv_km",
                ]
            )
            if column in conflicts.columns
        ]

        conflicts[
            conflict_columns
        ].to_csv(
            CONFLICT_FILE,
            index=False,
        )

        print()
        print(
            "STOPPING: some identical geometries "
            "have different source metadata."
        )

        print(
            f"Inspect: {CONFLICT_FILE}"
        )

        raise RuntimeError(
            "Duplicate metadata conflicts found. "
            "No deduplicated dataset was created."
        )

    # --------------------------------------------------
    # 4. Preserve duplicate site IDs for provenance
    # --------------------------------------------------

    duplicate_id_map = (
        sites.groupby(
            "geometry_hash"
        )[
            "site_id"
        ]
        .apply(
            lambda values:
            "|".join(
                sorted(
                    values.astype(str)
                )
            )
        )
        .to_dict()
    )

    sites[
        "source_site_ids"
    ] = (
        sites[
            "geometry_hash"
        ]
        .map(
            duplicate_id_map
        )
    )

    # --------------------------------------------------
    # 5. Choose one canonical record per geometry
    # --------------------------------------------------

    # OBJECTID itself is not treated as meaningful
    # planning metadata here. It merely provides a
    # deterministic record to retain.

    if "OBJECTID" in sites.columns:

        sites[
            "_sort_objectid"
        ] = pd.to_numeric(
            sites[
                "OBJECTID"
            ],
            errors="coerce",
        )

        sites = (
            sites.sort_values(
                [
                    "geometry_hash",
                    "_sort_objectid",
                ],
                na_position="last",
            )
        )

    else:

        sites = (
            sites.sort_values(
                "geometry_hash"
            )
        )

    clean = (
        sites
        .drop_duplicates(
            subset="geometry_hash",
            keep="first",
        )
        .copy()
    )

    # --------------------------------------------------
    # 6. Add explicit PowerStack provenance
    # --------------------------------------------------

    clean[
        "dedupe_status"
    ] = "CANONICAL"

    clean[
        "dedupe_method"
    ] = (
        "exact_geometry_hash_"
        "matching_source_metadata"
    )

    clean[
        "dedupe_fact_type"
    ] = "DERIVED"

    if "_sort_objectid" in clean.columns:

        clean = clean.drop(
            columns=[
                "_sort_objectid"
            ]
        )

    # --------------------------------------------------
    # 7. Save clean canonical dataset
    # --------------------------------------------------

    clean.to_parquet(
        OUTPUT_PARQUET,
        index=False,
    )

    csv_columns = [
        column
        for column in clean.columns
        if column != "geometry"
    ]

    clean[
        csv_columns
    ].to_csv(
        OUTPUT_CSV,
        index=False,
    )

    # --------------------------------------------------
    # 8. Summary
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("DEDUPLICATION SUMMARY")
    print("=" * 70)

    print()
    print(
        f"Original candidate rows: "
        f"{len(sites):,}"
    )

    print(
        f"Canonical unique sites: "
        f"{len(clean):,}"
    )

    print(
        f"Duplicate rows removed: "
        f"{len(sites) - len(clean):,}"
    )

    print()

    print(
        "Source duplicate count distribution:"
    )

    print(
        clean[
            "source_duplicate_count"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()

    if "daerah_nam" in duplicate_rows.columns:

        print(
            "Duplicate rows by district:"
        )

        print(
            duplicate_rows[
                "daerah_nam"
            ]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

    print()
    print(
        f"Saved canonical GeoParquet:"
    )
    print(
        OUTPUT_PARQUET
    )

    print()
    print(
        f"Saved canonical CSV:"
    )
    print(
        OUTPUT_CSV
    )

    print()
    print("=" * 70)
    print("DEDUPLICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
