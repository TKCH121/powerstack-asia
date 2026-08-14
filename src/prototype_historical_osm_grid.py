"""Research prototype for reconstructing OSM grid topology at a past cutoff.

This is not part of the canonical current-state pipeline. It tests one project
(PDG JH1) and writes generated outputs only under ignored ``data/processed``.

Historical OSM presence means ``OSM_MAPPED_AS_OF_CUTOFF``. It is not proof
that an asset physically existed at the cutoff, and absence is not proof that
it did not exist.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
import truststore
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import unary_union

from config import PROCESSED_DIR, RAW_DIR
from powerstack_utils import (
    PROJECTED_CRS,
    extract_voltages_kv,
    geometry_hash,
    has_voltage,
    max_voltage_kv,
)


truststore.inject_into_ssl()


PROJECT_ID = "DC-JHR-004"
INFORMATION_CUTOFF_DATE = "2023-05-22"
SNAPSHOT_TIMESTAMP = "2023-05-22T23:59:59Z"
SITE_LATITUDE = 1.69142
SITE_LONGITUDE = 103.41441
SEARCH_RADIUS_M = 30_000

OHSOME_API_ROOT = "https://api.ohsome.org/v1"
OHSOME_FILTER = "power in (line, cable, substation)"
OSM_API_ROOT = "https://api.openstreetmap.org/api/0.6"
USER_AGENT = "PowerStack-Asia historical-grid-research/0.1"

REGIONAL_PBF = RAW_DIR / "malaysia-singapore-brunei-latest.osm.pbf"
CURRENT_LINES_FILE = PROCESSED_DIR / "johor_hv_power_lines.parquet"
CURRENT_SUBSTATIONS_FILE = (
    PROCESSED_DIR / "johor_hv_substations_clean.parquet"
)

OUTPUT_DIR = PROCESSED_DIR / "research" / "historical_osm_pdg"
OHSOME_RAW_FILE = OUTPUT_DIR / "ohsome_snapshot_bbox.geojson"
OSM_API_RAW_FILE = OUTPUT_DIR / "osm_api_exact_candidates.json"
HISTORICAL_BBOX_GEOJSON = OUTPUT_DIR / "historical_power_feature_bboxes.geojson"
HISTORICAL_EXACT_GEOJSON = (
    OUTPUT_DIR / "historical_distance_candidates.geojson"
)
CURRENT_BBOX_PBF = OUTPUT_DIR / "current_bbox.osm.pbf"
CURRENT_POWER_PBF = OUTPUT_DIR / "current_power_features.osm.pbf"
CURRENT_GEOJSON = OUTPUT_DIR / "current_power_features.geojson"
DISTANCE_CSV = OUTPUT_DIR / "pdg_historical_current_distances.csv"
CHANGE_CSV = OUTPUT_DIR / "historical_current_change_detection.csv"
SUMMARY_JSON = OUTPUT_DIR / "prototype_summary.json"

TAG_COLUMNS = (
    "power",
    "voltage",
    "name",
    "operator",
    "construction",
    "construction:power",
    "substation",
)
VOLTAGES_KV = (132, 275, 500)


def build_bbox():
    """Return a 30 km projected envelope as a WGS84 bbox string."""
    site = gpd.GeoSeries(
        [Point(SITE_LONGITUDE, SITE_LATITUDE)],
        crs="EPSG:4326",
    ).to_crs(PROJECTED_CRS)
    envelope = gpd.GeoSeries(
        [site.iloc[0].buffer(SEARCH_RADIUS_M).envelope],
        crs=PROJECTED_CRS,
    ).to_crs("EPSG:4326")
    return ",".join(f"{value:.8f}" for value in envelope.total_bounds)


def request_response(method, url, *, timeout, **kwargs):
    """Make one retry-bounded public-data request."""
    headers = dict(kwargs.pop("headers", {}))
    headers.setdefault("User-Agent", USER_AGENT)
    response = None
    for attempt in range(4):
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        if response.status_code not in {429, 502, 503, 504}:
            break
        if attempt < 3:
            time.sleep(2 ** (attempt + 1))
    response.raise_for_status()
    return response


def request_json(method, url, *, timeout, **kwargs):
    """Make one public-data request and return its parsed JSON response."""
    response = request_response(method, url, timeout=timeout, **kwargs)
    return response, json.loads(response.content)


def fetch_historical_snapshot(bbox):
    """Fetch ohsome metadata and historical object bounding boxes.

    The public ohsome geometry endpoint currently returns Apache 403. Its bbox
    endpoint remains usable and provides snapshot IDs, versions, tags, and
    last-edit timestamps. Exact geometries needed for nearest-distance
    calculations are reconstructed later from the corresponding versioned OSM
    object and the node versions valid at the cutoff.
    """
    metadata_response, metadata = request_json(
        "GET",
        f"{OHSOME_API_ROOT}/metadata",
        timeout=60,
    )

    params = {
        "bboxes": bbox,
        "time": SNAPSHOT_TIMESTAMP,
        "filter": OHSOME_FILTER,
        "properties": "tags,metadata",
        "clipGeometry": "false",
        "timeout": "600",
    }

    geometry_response = requests.get(
        f"{OHSOME_API_ROOT}/elements/geometry",
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )

    bbox_response, ohsome = request_json(
        "GET",
        f"{OHSOME_API_ROOT}/elements/bbox",
        params=params,
        timeout=650,
    )

    OHSOME_RAW_FILE.write_text(
        json.dumps(ohsome, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    request_provenance = {
        "ohsome_metadata_status": metadata_response.status_code,
        "ohsome_api_version": metadata.get("apiVersion"),
        "ohsome_temporal_extent": metadata.get("extractRegion", {}).get(
            "temporalExtent"
        ),
        "ohsome_geometry_status": geometry_response.status_code,
        "ohsome_geometry_content_type": geometry_response.headers.get(
            "content-type"
        ),
        "ohsome_bbox_status": bbox_response.status_code,
        "ohsome_bbox_request_url": bbox_response.url,
        "ohsome_filter": OHSOME_FILTER,
        "osm_api_root": OSM_API_ROOT,
        "osm_attribution": ohsome.get("attribution"),
    }
    return ohsome, request_provenance


def element_geometry(element):
    """Convert one Overpass element with ``out geom`` to Shapely."""
    if element["type"] == "node":
        return Point(element["lon"], element["lat"])

    if element["type"] == "way":
        coordinates = [
            (node["lon"], node["lat"])
            for node in element.get("geometry", [])
        ]
        if len(coordinates) < 2:
            return None
        if len(coordinates) >= 4 and coordinates[0] == coordinates[-1]:
            return Polygon(coordinates)
        return LineString(coordinates)

    member_lines = []
    for member in element.get("members", []):
        coordinates = [
            (node["lon"], node["lat"])
            for node in member.get("geometry", [])
        ]
        if len(coordinates) >= 2:
            member_lines.append(LineString(coordinates))
    return unary_union(member_lines) if member_lines else None


def feature_kind(tags):
    """Return the mapped or construction power feature type."""
    power = tags.get("power")
    if power in {"line", "cable", "substation"}:
        return power
    construction_power = tags.get("construction:power")
    if construction_power in {"line", "cable", "substation"}:
        return construction_power
    return None


def historical_bbox_geodataframe(ohsome):
    """Load ohsome snapshot IDs, tags, metadata, and geometry bounding boxes."""
    rows = []
    for feature in ohsome.get("features", []):
        properties = feature["properties"]
        tags = {
            key: value
            for key, value in properties.items()
            if not key.startswith("@")
        }
        row = {
            "osm_id": properties["@osmId"],
            "osm_type": properties["@osmType"],
            "osm_version": properties.get("@version"),
            "snapshot_timestamp": properties.get("@snapshotTimestamp"),
            "last_edit": properties.get("@lastEdit"),
            "feature_kind": feature_kind(tags),
            "tags_json": json.dumps(tags, sort_keys=True, ensure_ascii=False),
            "geometry": shape(feature["geometry"]),
        }
        for column in TAG_COLUMNS:
            row[column] = tags.get(column)
        rows.append(row)

    historical = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    historical["max_voltage_kv"] = historical["voltage"].apply(
        max_voltage_kv
    )
    historical["historical_topology_status"] = "OSM_MAPPED_AS_OF_CUTOFF"
    historical["fact_type"] = "DERIVED"
    historical.to_file(HISTORICAL_BBOX_GEOJSON, driver="GeoJSON")
    return historical


def parse_osm_timestamp(value):
    """Parse an OSM UTC timestamp."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_xml_response(response):
    """Parse one OSM API XML response."""
    return ET.fromstring(response.content)


def fetch_node_history_at_cutoff(node_id, request_log):
    """Return the latest visible node version at or before the cutoff."""
    url = f"{OSM_API_ROOT}/node/{node_id}/history"
    response = request_response("GET", url, timeout=60)
    request_log.append(
        {"request_type": "node_history", "url": response.url, "status": 200}
    )
    cutoff = parse_osm_timestamp(SNAPSHOT_TIMESTAMP)
    candidates = [
        node
        for node in parse_xml_response(response).findall("node")
        if parse_osm_timestamp(node.attrib["timestamp"]) <= cutoff
    ]
    if not candidates:
        raise RuntimeError(f"Node {node_id} has no version at the cutoff")
    node = max(
        candidates,
        key=lambda item: parse_osm_timestamp(item.attrib["timestamp"]),
    )
    if node.attrib.get("visible", "true") == "false":
        raise RuntimeError(f"Node {node_id} was not visible at the cutoff")
    return node


def fetch_way_nodes_at_cutoff(node_ids, request_log):
    """Resolve the cutoff-valid coordinates for an ordered set of way nodes."""
    current_nodes = {}
    for start in range(0, len(node_ids), 400):
        chunk = node_ids[start : start + 400]
        url = f"{OSM_API_ROOT}/nodes"
        try:
            response = request_response(
                "GET",
                url,
                params={"nodes": ",".join(chunk)},
                timeout=60,
            )
            nodes = parse_xml_response(response).findall("node")
            current_nodes.update({node.attrib["id"]: node for node in nodes})
            request_log.append(
                {
                    "request_type": "current_nodes_bulk",
                    "url": response.url,
                    "status": 200,
                    "node_count": len(nodes),
                }
            )
        except requests.RequestException as error:
            request_log.append(
                {
                    "request_type": "current_nodes_bulk",
                    "url": url,
                    "status": "FAILED",
                    "error": str(error),
                }
            )

    cutoff = parse_osm_timestamp(SNAPSHOT_TIMESTAMP)
    nodes_at_cutoff = {}
    for node_id in set(node_ids):
        current = current_nodes.get(node_id)
        if (
            current is not None
            and parse_osm_timestamp(current.attrib["timestamp"]) <= cutoff
        ):
            nodes_at_cutoff[node_id] = current
        else:
            nodes_at_cutoff[node_id] = fetch_node_history_at_cutoff(
                node_id,
                request_log,
            )
    return nodes_at_cutoff


def tags_from_xml(element):
    """Return an OSM XML element's tags."""
    return {
        tag.attrib["k"]: tag.attrib["v"]
        for tag in element.findall("tag")
    }


def fetch_exact_historical_element(feature, request_log):
    """Reconstruct one exact object version selected by the ohsome snapshot."""
    osm_type, numeric_id = feature["osm_id"].split("/", 1)
    version = int(feature["osm_version"])
    url = f"{OSM_API_ROOT}/{osm_type}/{numeric_id}/{version}"
    response = request_response("GET", url, timeout=60)
    root = parse_xml_response(response)
    xml_element = root.find(osm_type)
    if xml_element is None:
        raise RuntimeError(f"OSM API did not return {feature['osm_id']}")
    request_log.append(
        {
            "request_type": "versioned_object",
            "url": response.url,
            "status": 200,
            "osm_id": feature["osm_id"],
            "osm_version": version,
        }
    )

    result = {
        "type": osm_type,
        "id": int(numeric_id),
        "version": version,
        "timestamp": xml_element.attrib["timestamp"],
        "tags": tags_from_xml(xml_element),
    }
    if osm_type == "node":
        result["lat"] = float(xml_element.attrib["lat"])
        result["lon"] = float(xml_element.attrib["lon"])
        return result
    if osm_type != "way":
        raise RuntimeError(
            "The pilot exact-geometry resolver currently supports nodes and ways; "
            f"nearest candidate {feature['osm_id']} is a relation."
        )

    node_ids = [node.attrib["ref"] for node in xml_element.findall("nd")]
    nodes = fetch_way_nodes_at_cutoff(node_ids, request_log)
    result["geometry"] = [
        {
            "lat": float(nodes[node_id].attrib["lat"]),
            "lon": float(nodes[node_id].attrib["lon"]),
        }
        for node_id in node_ids
    ]
    return result


def fetch_exact_historical_elements(features, request_log):
    """Resolve a small set of ohsome-selected objects to exact geometry."""
    return {
        feature["osm_id"]: fetch_exact_historical_element(feature, request_log)
        for _, feature in features.iterrows()
    }


def nearest_exact_historical_distance(
    features,
    site,
    exact_cache,
    request_log,
):
    """Resolve only candidates whose bbox can still contain the nearest asset."""
    if features.empty:
        return None, None

    candidates = features.to_crs(PROJECTED_CRS).copy()
    candidates["bbox_lower_bound_m"] = candidates.geometry.distance(site)
    candidates = candidates.sort_values(["bbox_lower_bound_m", "osm_id"])
    best_distance_m = float("inf")
    best_id = None

    start = 0
    batch_size = 1
    while start < len(candidates):
        if float(candidates.iloc[start]["bbox_lower_bound_m"]) >= best_distance_m:
            break

        batch = candidates.iloc[start : start + batch_size]
        unresolved = [
            osm_id
            for osm_id in batch["osm_id"]
            if osm_id not in exact_cache
        ]
        if unresolved:
            exact_cache.update(
                fetch_exact_historical_elements(
                    batch[batch["osm_id"].isin(unresolved)],
                    request_log,
                )
            )

        for _, candidate in batch.iterrows():
            lower_bound_m = float(candidate["bbox_lower_bound_m"])
            if lower_bound_m >= best_distance_m:
                break
            osm_id = candidate["osm_id"]
            exact_geometry = element_geometry(exact_cache[osm_id])
            projected_geometry = gpd.GeoSeries(
                [exact_geometry],
                crs="EPSG:4326",
            ).to_crs(PROJECTED_CRS).iloc[0]
            exact_distance_m = float(projected_geometry.distance(site))
            if exact_distance_m < best_distance_m:
                best_distance_m = exact_distance_m
                best_id = osm_id
        start += batch_size

    if best_id is None:
        return None, None
    return best_distance_m / 1000, best_id


def historical_distance_metrics(historical, exact_cache, request_log):
    """Calculate historical distances using bbox lower bounds and exact geometry."""
    site = gpd.GeoSeries(
        [Point(SITE_LONGITUDE, SITE_LATITUDE)],
        crs="EPSG:4326",
    ).to_crs(PROJECTED_CRS).iloc[0]
    lines = historical[
        historical["feature_kind"].isin(["line", "cable"])
    ].copy()
    substations = historical[
        historical["feature_kind"].eq("substation")
        & historical["max_voltage_kv"].fillna(0).ge(100)
    ].copy()
    values = {}
    nearest_ids = {}

    for voltage_kv in VOLTAGES_KV:
        subset = lines[
            lines["voltage"].apply(
                lambda value: has_voltage(value, voltage_kv)
            )
        ]
        distance, osm_id = nearest_exact_historical_distance(
            subset,
            site,
            exact_cache,
            request_log,
        )
        key = f"distance_{voltage_kv}kv_line_osm_as_of_cutoff_km"
        values[key] = distance
        nearest_ids[key] = osm_id

    distance, osm_id = nearest_exact_historical_distance(
        substations,
        site,
        exact_cache,
        request_log,
    )
    key = "distance_hv_substation_osm_as_of_cutoff_km"
    values[key] = distance
    nearest_ids[key] = osm_id

    for voltage_kv in VOLTAGES_KV:
        subset = substations[
            substations["voltage"].apply(
                lambda value: has_voltage(value, voltage_kv)
            )
        ]
        distance, osm_id = nearest_exact_historical_distance(
            subset,
            site,
            exact_cache,
            request_log,
        )
        key = f"distance_{voltage_kv}kv_substation_osm_as_of_cutoff_km"
        values[key] = distance
        nearest_ids[key] = osm_id
    return values, nearest_ids


def save_exact_historical_candidates(exact_cache):
    """Save only exact geometries resolved for the nearest-distance proof."""
    rows = []
    for osm_id, element in exact_cache.items():
        tags = element.get("tags", {})
        row = {
            "osm_id": osm_id,
            "osm_type": element["type"],
            "osm_version": element.get("version"),
            "osm_timestamp": element.get("timestamp"),
            "feature_kind": feature_kind(tags),
            "tags_json": json.dumps(tags, sort_keys=True, ensure_ascii=False),
            "geometry": element_geometry(element),
        }
        for column in TAG_COLUMNS:
            row[column] = tags.get(column)
        rows.append(row)

    exact = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    exact.to_file(HISTORICAL_EXACT_GEOJSON, driver="GeoJSON")
    OSM_API_RAW_FILE.write_text(
        json.dumps(
            {
                "snapshot_timestamp": SNAPSHOT_TIMESTAMP,
                "source_api_root": OSM_API_ROOT,
                "versioned_object_urls": [
                    (
                        f"{OSM_API_ROOT}/{element['type']}/{element['id']}/"
                        f"{element['version']}"
                    )
                    for element in exact_cache.values()
                ],
                "elements": list(exact_cache.values()),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return exact


def load_exact_historical_cache():
    """Reuse an ignored exact-geometry artifact for repeat local validation."""
    if not OSM_API_RAW_FILE.exists():
        return {}
    payload = json.loads(OSM_API_RAW_FILE.read_text(encoding="utf-8"))
    if payload.get("snapshot_timestamp") != SNAPSHOT_TIMESTAMP:
        return {}
    return {
        f"{element['type']}/{element['id']}": element
        for element in payload.get("elements", [])
    }


def find_osmium():
    """Locate Osmium in PATH or next to the active Conda environment."""
    path = shutil.which("osmium")
    if path:
        return path

    environment_root = Path(sys.executable).resolve().parent
    candidate = environment_root / "Library" / "bin" / "osmium.exe"
    if candidate.exists():
        return str(candidate)
    raise RuntimeError("Osmium is required to inspect the current local PBF.")


def run(command):
    """Run one local Osmium command."""
    subprocess.run(command, check=True)


def build_current_bbox_extract(bbox):
    """Create an ID-preserving current subset without changing canonical data."""
    if not REGIONAL_PBF.exists():
        raise FileNotFoundError(REGIONAL_PBF)

    osmium = find_osmium()
    run(
        [
            osmium,
            "extract",
            "-s",
            "complete_ways",
            "-b",
            bbox,
            str(REGIONAL_PBF),
            "-o",
            str(CURRENT_BBOX_PBF),
            "-O",
        ]
    )
    run(
        [
            osmium,
            "tags-filter",
            str(CURRENT_BBOX_PBF),
            "w/power=line",
            "w/power=cable",
            "power=substation",
            "-o",
            str(CURRENT_POWER_PBF),
            "-O",
        ]
    )
    run(
        [
            osmium,
            "export",
            str(CURRENT_POWER_PBF),
            "-u",
            "type_id",
            "-a",
            "version,timestamp",
            "-o",
            str(CURRENT_GEOJSON),
            "-O",
        ]
    )

    file_info = subprocess.run(
        [osmium, "fileinfo", "-j", str(REGIONAL_PBF)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(file_info.stdout)


def current_geodataframe():
    """Load the generated current subset and normalize stable OSM IDs."""
    current = gpd.read_file(CURRENT_GEOJSON)
    id_column = "@id" if "@id" in current.columns else "id"
    if id_column not in current.columns:
        raise RuntimeError(
            f"Current export lacks an ID; columns={list(current.columns)}"
        )

    # Osmium's ``a...`` records are generated area representations of closed
    # OSM ways/relations, not stable primitives. Keep only n/w/r IDs so a
    # substation polygon is not counted twice in historical change detection.
    current = current[
        ~current[id_column].astype(str).str.startswith("a")
    ].copy()
    current = current.rename(columns={id_column: "osm_id"})
    current["osm_id"] = (
        current["osm_id"]
        .astype(str)
        .str.replace(r"^n", "node/", regex=True)
        .str.replace(r"^w", "way/", regex=True)
        .str.replace(r"^r", "relation/", regex=True)
    )
    current["feature_kind"] = current.apply(
        lambda row: feature_kind(row),
        axis=1,
    )
    current["max_voltage_kv"] = current["voltage"].apply(max_voltage_kv)
    return current


def nearest_distance_km(features, site):
    """Return metric point-to-feature distance, or ``None`` when empty."""
    if features.empty:
        return None
    projected = features.to_crs(PROJECTED_CRS)
    return float(projected.geometry.distance(site).min() / 1000)


def distance_metrics(lines, substations, suffix):
    """Calculate the requested voltage-specific distances."""
    site = gpd.GeoSeries(
        [Point(SITE_LONGITUDE, SITE_LATITUDE)],
        crs="EPSG:4326",
    ).to_crs(PROJECTED_CRS).iloc[0]
    values = {}

    for voltage_kv in VOLTAGES_KV:
        subset = lines[
            lines["voltage"].apply(
                lambda value: has_voltage(value, voltage_kv)
            )
        ]
        values[f"distance_{voltage_kv}kv_line_{suffix}_km"] = (
            nearest_distance_km(subset, site)
        )

    values[f"distance_hv_substation_{suffix}_km"] = nearest_distance_km(
        substations,
        site,
    )
    for voltage_kv in VOLTAGES_KV:
        subset = substations[
            substations["voltage"].apply(
                lambda value: has_voltage(value, voltage_kv)
            )
        ]
        values[f"distance_{voltage_kv}kv_substation_{suffix}_km"] = (
            nearest_distance_km(subset, site)
        )
    return values


def make_change_detection(historical, current):
    """Compare stable IDs for explicitly tagged >=100 kV features."""
    historical_hv = historical[
        historical["max_voltage_kv"].fillna(0).ge(100)
    ].copy()
    current_hv = current[current["max_voltage_kv"].fillna(0).ge(100)].copy()
    historical_by_id = historical_hv.set_index("osm_id", drop=False)
    current_by_id = current_hv.set_index("osm_id", drop=False)
    all_ids = sorted(set(historical_by_id.index) | set(current_by_id.index))
    rows = []

    for osm_id in all_ids:
        historical_row = (
            historical_by_id.loc[osm_id]
            if osm_id in historical_by_id.index
            else None
        )
        current_row = (
            current_by_id.loc[osm_id]
            if osm_id in current_by_id.index
            else None
        )
        if historical_row is not None and current_row is not None:
            status = "PRESENT_AT_CUTOFF_AND_CURRENT"
        elif current_row is not None:
            status = "NOT_MAPPED_IN_OSM_AT_CUTOFF"
        else:
            status = "MAPPED_AT_CUTOFF_NOT_IN_CURRENT_SNAPSHOT"

        rows.append(
            {
                "osm_id": osm_id,
                "topology_status": status,
                "historical_feature_kind": None
                if historical_row is None
                else historical_row["feature_kind"],
                "current_feature_kind": None
                if current_row is None
                else current_row["feature_kind"],
                "historical_voltage": None
                if historical_row is None
                else historical_row["voltage"],
                "current_voltage": None
                if current_row is None
                else current_row["voltage"],
                "historical_name": None
                if historical_row is None
                else historical_row["name"],
                "current_name": None
                if current_row is None
                else current_row["name"],
                "historical_bbox_hash": None
                if historical_row is None
                else geometry_hash(historical_row.geometry),
                "current_geometry_hash": None
                if current_row is None
                else geometry_hash(current_row.geometry),
            }
        )

    change = pd.DataFrame(rows)
    if not change.empty:
        change["voltage_tag_changed"] = (
            change["historical_voltage"].fillna("")
            != change["current_voltage"].fillna("")
        )
        change["name_tag_changed"] = (
            change["historical_name"].fillna("")
            != change["current_name"].fillna("")
        )
    change.to_csv(CHANGE_CSV, index=False)
    return change


def voltage_change_counts(historical, current):
    """Count ID presence separately for each explicit voltage class."""
    result = {}
    for voltage_kv in VOLTAGES_KV:
        historical_ids = set(
            historical.loc[
                historical["voltage"].apply(
                    lambda value: has_voltage(value, voltage_kv)
                ),
                "osm_id",
            ]
        )
        current_ids = set(
            current.loc[
                current["voltage"].apply(
                    lambda value: has_voltage(value, voltage_kv)
                ),
                "osm_id",
            ]
        )
        result[str(voltage_kv)] = {
            "present_at_cutoff_and_current": len(
                historical_ids & current_ids
            ),
            "not_mapped_at_cutoff_with_voltage": len(
                current_ids - historical_ids
            ),
            "mapped_at_cutoff_not_current_with_voltage": len(
                historical_ids - current_ids
            ),
        }
    return result


def named_sedenak(features):
    """Return mapped Sedenak-named records without forcing identity matches."""
    if "name" not in features.columns:
        return []
    matches = features[
        features["name"].fillna("").str.contains(
            "Sedenak",
            case=False,
            regex=False,
        )
    ]
    return [
        {
            "osm_id": row.get("osm_id"),
            "feature_kind": row.get("feature_kind"),
            "name": row.get("name"),
            "voltage": row.get("voltage"),
        }
        for _, row in matches.iterrows()
    ]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bbox = build_bbox()
    print(f"Historical cutoff: {SNAPSHOT_TIMESTAMP}")
    print(f"PDG 30 km envelope: {bbox}")

    ohsome, request_provenance = fetch_historical_snapshot(bbox)
    historical = historical_bbox_geodataframe(ohsome)

    current_file_info = build_current_bbox_extract(bbox)
    current = current_geodataframe()

    historical_lines = historical[
        historical["feature_kind"].isin(["line", "cable"])
    ].copy()
    historical_substations_all = historical[
        historical["feature_kind"].eq("substation")
    ].copy()
    historical_substations_hv = historical_substations_all[
        historical_substations_all["max_voltage_kv"].fillna(0).ge(100)
    ].copy()

    current_lines = gpd.read_parquet(CURRENT_LINES_FILE)
    current_substations = gpd.read_parquet(CURRENT_SUBSTATIONS_FILE)

    exact_cache = load_exact_historical_cache()
    osm_api_request_log = []
    historical_distances, historical_nearest_ids = (
        historical_distance_metrics(
            historical,
            exact_cache,
            osm_api_request_log,
        )
    )
    exact_candidates = save_exact_historical_candidates(exact_cache)
    request_provenance["osm_api_exact_geometry_requests"] = (
        osm_api_request_log
    )
    request_provenance["osm_api_exact_geometry_cache_reused"] = bool(
        exact_cache and not osm_api_request_log
    )
    request_provenance["osm_api_versioned_object_urls"] = [
        (
            f"{OSM_API_ROOT}/{element['type']}/{element['id']}/"
            f"{element['version']}"
        )
        for element in exact_cache.values()
    ]
    request_provenance["osm_api_exact_geometry_count"] = len(
        exact_candidates
    )
    current_distances = distance_metrics(
        current_lines,
        current_substations,
        "current_osm",
    )
    distance_row = {
        "project_id": PROJECT_ID,
        "information_cutoff_date": INFORMATION_CUTOFF_DATE,
        "snapshot_source": "ohsome snapshot IDs + versioned OSM API geometry",
        "snapshot_timestamp": SNAPSHOT_TIMESTAMP,
        "site_latitude": SITE_LATITUDE,
        "site_longitude": SITE_LONGITUDE,
        **historical_distances,
        **current_distances,
        "historical_topology_status": "OSM_MAPPED_AS_OF_CUTOFF",
        "fact_type": "DERIVED",
        "notes": (
            "Historical OSM presence is public-map evidence only, not "
            "physical pre-existence. Absence is not proof of physical absence."
        ),
    }
    pd.DataFrame([distance_row]).to_csv(DISTANCE_CSV, index=False)

    change = make_change_detection(historical, current)
    current_lines_raw = current[
        current["feature_kind"].isin(["line", "cable"])
    ].copy()
    current_substations_raw = current[
        current["feature_kind"].eq("substation")
    ].copy()

    summary = {
        "project_id": PROJECT_ID,
        "extraction_date": date.today().isoformat(),
        "site_latitude": SITE_LATITUDE,
        "site_longitude": SITE_LONGITUDE,
        "information_cutoff_date": INFORMATION_CUTOFF_DATE,
        "snapshot_timestamp": SNAPSHOT_TIMESTAMP,
        "search_radius_m": SEARCH_RADIUS_M,
        "bbox_wgs84": bbox,
        "projected_crs": PROJECTED_CRS,
        "request_provenance": request_provenance,
        "current_pbf_header": current_file_info.get("header"),
        "counts": {
            "historical_all_relevant_features": len(historical),
            "historical_lines_cables": len(historical_lines),
            "historical_lines_cables_explicit_ge_100kv": int(
                historical_lines["max_voltage_kv"].fillna(0).ge(100).sum()
            ),
            "historical_substations": len(historical_substations_all),
            "historical_substations_explicit_ge_100kv": len(
                historical_substations_hv
            ),
            "current_raw_lines_cables_in_bbox": len(current_lines_raw),
            "current_raw_substations_in_bbox": len(current_substations_raw),
        },
        "historical_distances_km": historical_distances,
        "historical_nearest_osm_ids": historical_nearest_ids,
        "current_distances_km": current_distances,
        "change_counts_explicit_ge_100kv": (
            change["topology_status"].value_counts().to_dict()
            if not change.empty
            else {}
        ),
        "change_counts_by_voltage": voltage_change_counts(
            historical,
            current,
        ),
        "historical_sedenak_named_features": named_sedenak(historical),
        "current_sedenak_named_features": named_sedenak(current),
        "interpretation": {
            "present_historically": "OSM_MAPPED_AS_OF_CUTOFF",
            "current_only": "NOT_MAPPED_IN_OSM_AT_CUTOFF",
            "historical_only": "MAPPED_AT_CUTOFF_NOT_IN_CURRENT_SNAPSHOT",
            "physical_timing": "NOT_FOUND without independent dated evidence",
        },
    }
    SUMMARY_JSON.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    print(f"Generated research outputs: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
