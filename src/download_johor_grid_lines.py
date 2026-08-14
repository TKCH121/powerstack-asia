import re

import truststore

# Use the Windows certificate store before network libraries are imported.
truststore.inject_into_ssl()

import geopandas as gpd
import osmnx as ox
import pandas as pd

from config import RAW_DIR, PROCESSED_DIR


ZONING_FILE = (
    PROCESSED_DIR / "johor_relevant_zoning.parquet"
)

RAW_OUTPUT = (
    RAW_DIR / "johor_osm_power_lines.parquet"
)

HV_OUTPUT = (
    PROCESSED_DIR / "johor_hv_power_lines.parquet"
)


def parse_max_voltage_v(value):
    """
    Convert an OpenStreetMap voltage field into the
    highest stated voltage in volts.

    Examples:
        "132000" -> 132000
        "275000;132000" -> 275000
        missing -> None

    We do NOT guess missing voltages.
    """

    if value is None:
        return None

    if value is pd.NA:
        return None

    # OSM fields can occasionally contain multiple values.
    text = str(value)

    # Extract digit groups.
    matches = re.findall(r"\d+", text)

    if not matches:
        return None

    voltages = [
        int(number)
        for number in matches
    ]

    return max(voltages)


def main():

    print("=" * 70)
    print("POWERSTACK — JOHOR GRID LINE DOWNLOAD")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Load our verified Johor zoning data
    # --------------------------------------------------

    if not ZONING_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {ZONING_FILE}"
        )

    zoning = gpd.read_parquet(
        ZONING_FILE
    )

    print()
    print(
        f"Loaded {len(zoning):,} zoning polygons"
    )

    print(
        f"Zoning CRS: {zoning.crs}"
    )

    # OSMnx expects latitude/longitude.
    if zoning.crs is None:
        raise RuntimeError(
            "Zoning dataset has no CRS."
        )

    if zoning.crs.to_epsg() != 4326:
        print(
            "Converting zoning to EPSG:4326..."
        )

        zoning = zoning.to_crs(
            "EPSG:4326"
        )

    # --------------------------------------------------
    # 2. Derive a Johor working bounding box
    # --------------------------------------------------

    minx, miny, maxx, maxy = (
        zoning.total_bounds
    )

    # Small buffer around the zoning extent.
    padding = 0.05

    left = minx - padding
    bottom = miny - padding
    right = maxx + padding
    top = maxy + padding

    bbox = (
        left,
        bottom,
        right,
        top,
    )

    print()
    print("Query bounding box:")
    print(f"Left:   {left:.6f}")
    print(f"Bottom: {bottom:.6f}")
    print(f"Right:  {right:.6f}")
    print(f"Top:    {top:.6f}")

    # --------------------------------------------------
    # 3. Configure OSMnx
    # --------------------------------------------------

    ox.settings.use_cache = True

    # Large regional requests can take time.
    ox.settings.requests_timeout = 300

    # --------------------------------------------------
    # 4. Download power lines and underground cables
    # --------------------------------------------------

    print()
    print("Downloading OSM power lines...")
    print(
        "This can take several minutes."
    )

    tags = {
        "power": [
            "line",
            "cable",
        ]
    }

    grid = ox.features.features_from_bbox(
        bbox,
        tags,
    )

    if grid.empty:
        raise RuntimeError(
            "OpenStreetMap returned no power-line features."
        )

    # Convert OSM's multi-index to ordinary columns.
    grid = grid.reset_index()

    print()
    print(
        f"Downloaded {len(grid):,} total power features"
    )

    # --------------------------------------------------
    # 5. Preserve the original voltage field
    # --------------------------------------------------

    if "voltage" not in grid.columns:
        grid["voltage"] = None

    grid["max_voltage_v"] = (
        grid["voltage"]
        .apply(parse_max_voltage_v)
    )

    grid["max_voltage_kv"] = (
        grid["max_voltage_v"] / 1000
    )

    # --------------------------------------------------
    # 6. Add PowerStack provenance
    # --------------------------------------------------

    grid["powerstack_source"] = (
        "OpenStreetMap via OSMnx"
    )

    grid["fact_type"] = "VERIFIED"

    grid["capacity_status"] = (
        "NOT_FOUND"
    )

    # --------------------------------------------------
    # 7. Save complete raw extraction
    # --------------------------------------------------

    grid.to_parquet(
        RAW_OUTPUT,
        index=False,
    )

    print()
    print(
        f"Saved raw power features to:"
    )
    print(RAW_OUTPUT)

    # --------------------------------------------------
    # 8. Create our high-voltage subset
    # --------------------------------------------------

    # Start at 100 kV so this captures the Malaysian
    # 132 / 275 / 500 kV transmission classes.
    #
    # This is a screening threshold, not a statement
    # that every >=100 kV asset is relevant to a DC.

    hv = grid[
        grid["max_voltage_v"] >= 100_000
    ].copy()

    hv.to_parquet(
        HV_OUTPUT,
        index=False,
    )

    # --------------------------------------------------
    # 9. Inspection output
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("HIGH-VOLTAGE SUMMARY")
    print("=" * 70)

    print()
    print(
        f"Total power features: "
        f"{len(grid):,}"
    )

    print(
        f">=100 kV features: "
        f"{len(hv):,}"
    )

    print()
    print("Voltage counts:")

    print(
        hv["max_voltage_kv"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("Geometry types:")

    print(
        hv.geometry
        .geom_type
        .value_counts()
        .to_string()
    )

    print()
    print(
        f"Saved processed HV layer to:"
    )

    print(HV_OUTPUT)

    print()
    print("=" * 70)
    print("GRID LINE DOWNLOAD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()