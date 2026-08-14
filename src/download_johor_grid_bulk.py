from pathlib import Path
import re
import shutil
import subprocess

import truststore
truststore.inject_into_ssl()

import geopandas as gpd
import pandas as pd
import requests

from config import RAW_DIR, PROCESSED_DIR


# --------------------------------------------------
# Files
# --------------------------------------------------

REGIONAL_PBF = (
    RAW_DIR /
    "malaysia-singapore-brunei-latest.osm.pbf"
)

JOHOR_PBF = (
    RAW_DIR /
    "johor_bbox.osm.pbf"
)

POWER_PBF = (
    RAW_DIR /
    "johor_power_lines.osm.pbf"
)

POWER_GEOJSON = (
    RAW_DIR /
    "johor_power_lines.geojson"
)

OUTPUT_PARQUET = (
    PROCESSED_DIR /
    "johor_hv_power_lines.parquet"
)


# Official Geofabrik regional OSM extract
DOWNLOAD_URL = (
    "https://download.geofabrik.de/asia/"
    "malaysia-singapore-brunei-latest.osm.pbf"
)


# Bounding box derived from our Johor zoning dataset,
# including the small padding used previously.
#
# left,bottom,right,top
JOHOR_BBOX = (
    "102.471970,"
    "1.227300,"
    "104.330946,"
    "2.706822"
)


def run_command(command):
    """
    Run a command and stop immediately if it fails.
    """

    print()
    print("Running:")
    print(" ".join(command))
    print()

    subprocess.run(
        command,
        check=True,
    )


def download_file():

    if REGIONAL_PBF.exists():

        size_mb = (
            REGIONAL_PBF.stat().st_size
            / 1024
            / 1024
        )

        print(
            f"Regional OSM file already exists "
            f"({size_mb:.1f} MB)."
        )

        print(
            "Skipping download."
        )

        return

    print()
    print("Downloading regional OpenStreetMap extract...")
    print(
        "This file is roughly 240 MB, "
        "so this is the slowest part."
    )

    with requests.get(
        DOWNLOAD_URL,
        stream=True,
        timeout=300,
    ) as response:

        response.raise_for_status()

        total = int(
            response.headers.get(
                "content-length",
                0,
            )
        )

        downloaded = 0

        with open(
            REGIONAL_PBF,
            "wb",
        ) as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if not chunk:
                    continue

                file.write(chunk)

                downloaded += len(chunk)

                if total:

                    percent = (
                        downloaded
                        / total
                        * 100
                    )

                    print(
                        f"\rDownloaded "
                        f"{percent:5.1f}%",
                        end="",
                    )

    print()
    print(
        f"Saved to: {REGIONAL_PBF}"
    )


def parse_max_voltage(value):
    """
    Extract the highest stated voltage.

    Examples:

    132000
        -> 132 kV

    275000;132000
        -> 275 kV

    Missing
        -> None

    Missing voltage is NEVER guessed.
    """

    if value is None:
        return None

    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):
        pass

    values = re.findall(
        r"\d+",
        str(value),
    )

    if not values:
        return None

    volts = [
        int(v)
        for v in values
    ]

    return max(volts) / 1000


def main():

    print("=" * 70)
    print(
        "POWERSTACK — JOHOR BULK GRID EXTRACTION"
    )
    print("=" * 70)

    # --------------------------------------------------
    # 1. Confirm Osmium exists
    # --------------------------------------------------

    osmium_path = shutil.which(
        "osmium"
    )

    if osmium_path is None:

        raise RuntimeError(
            "Osmium was not found. "
            "Run: conda install -c conda-forge "
            "osmium-tool -y"
        )

    print()
    print(
        f"Using Osmium: {osmium_path}"
    )

    # --------------------------------------------------
    # 2. Download regional OSM data
    # --------------------------------------------------

    download_file()

    # --------------------------------------------------
    # 3. Crop regional file to Johor working area
    # --------------------------------------------------

    print()
    print("Extracting Johor region...")

    run_command(
        [
            "osmium",
            "extract",
            "-b",
            JOHOR_BBOX,
            str(REGIONAL_PBF),
            "-o",
            str(JOHOR_PBF),
            "-O",
        ]
    )

    # --------------------------------------------------
    # 4. Keep only relevant power infrastructure
    # --------------------------------------------------

    print()
    print(
        "Filtering power lines and cables..."
    )

    run_command(
        [
            "osmium",
            "tags-filter",
            str(JOHOR_PBF),

            # Existing overhead transmission lines
            "w/power=line",

            # Existing underground power cables
            "w/power=cable",

            # Lines currently under construction
            "w/construction:power=line",

            # Cables currently under construction
            "w/construction:power=cable",

            "-o",
            str(POWER_PBF),
            "-O",
        ]
    )

    # --------------------------------------------------
    # 5. Convert OSM objects to normal GIS geometry
    # --------------------------------------------------

    print()
    print(
        "Converting power data to GeoJSON..."
    )

    run_command(
        [
            "osmium",
            "export",
            str(POWER_PBF),
            "-o",
            str(POWER_GEOJSON),
            "-O",
        ]
    )

    # --------------------------------------------------
    # 6. Read into GeoPandas
    # --------------------------------------------------

    print()
    print(
        "Loading power lines into GeoPandas..."
    )

    grid = gpd.read_file(
        POWER_GEOJSON
    )

    print(
        f"Power features loaded: "
        f"{len(grid):,}"
    )

    print(
        f"CRS: {grid.crs}"
    )

    # --------------------------------------------------
    # 7. Inspect available OSM fields
    # --------------------------------------------------

    print()
    print("Available columns:")

    for column in grid.columns:
        print(
            f"  - {column}"
        )

    # --------------------------------------------------
    # 8. Voltage processing
    # --------------------------------------------------

    if "voltage" not in grid.columns:

        grid["voltage"] = None

    grid[
        "max_voltage_kv"
    ] = (
        grid["voltage"]
        .apply(
            parse_max_voltage
        )
    )

    # --------------------------------------------------
    # 9. Determine operating / construction status
    # --------------------------------------------------

    grid[
        "powerstack_status"
    ] = "OPERATING_OR_MAPPED"

    if "construction:power" in grid.columns:

        construction_mask = (
            grid[
                "construction:power"
            ]
            .notna()
        )

        grid.loc[
            construction_mask,
            "powerstack_status"
        ] = "UNDER_CONSTRUCTION"

    # --------------------------------------------------
    # 10. Add provenance
    # --------------------------------------------------

    grid[
        "powerstack_source"
    ] = (
        "OpenStreetMap / "
        "Geofabrik regional extract"
    )

    grid[
        "fact_type"
    ] = "VERIFIED_PUBLIC_MAP"

    grid[
        "available_capacity_mw"
    ] = None

    grid[
        "capacity_status"
    ] = "NOT_FOUND"

    # --------------------------------------------------
    # 11. High-voltage subset
    # --------------------------------------------------

    hv = grid[
        grid[
            "max_voltage_kv"
        ] >= 100
    ].copy()

    # --------------------------------------------------
    # 12. Save processed dataset
    # --------------------------------------------------

    hv.to_parquet(
        OUTPUT_PARQUET,
        index=False,
    )

    # --------------------------------------------------
    # 13. Summary
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("HIGH-VOLTAGE SUMMARY")
    print("=" * 70)

    print()
    print(
        f"All mapped power lines/cables: "
        f"{len(grid):,}"
    )

    print(
        f"Mapped >=100 kV lines/cables: "
        f"{len(hv):,}"
    )

    print()
    print("Voltage distribution:")

    if len(hv):

        print(
            hv[
                "max_voltage_kv"
            ]
            .value_counts()
            .sort_index()
            .to_string()
        )

    else:

        print(
            "NO >=100 kV LINES FOUND"
        )

    print()
    print("Status distribution:")

    print(
        grid[
            "powerstack_status"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        f"Saved processed grid to:"
    )

    print(
        OUTPUT_PARQUET
    )

    print()
    print("=" * 70)
    print(
        "BULK GRID EXTRACTION COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()