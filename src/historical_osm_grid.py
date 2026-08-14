"""Reusable, conservative historical OSM grid-feature extraction.

Historical OSM presence describes public map state at a cutoff. It does not
prove that infrastructure was physically present, commissioned, or available.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import requests
import truststore
from shapely.geometry import LineString, Point, Polygon, shape

from config import PROCESSED_DIR, RAW_DIR
from powerstack_utils import (
    PROJECTED_CRS,
    geometry_hash,
    has_voltage,
    max_voltage_kv,
)


truststore.inject_into_ssl()


OHSOME_API_ROOT = "https://api.ohsome.org/v1"
OSM_API_ROOT = "https://api.openstreetmap.org/api/0.6"
OHSOME_FILTER = (
    "power in (line, cable, substation) or "
    "(power = construction and "
    "construction:power in (line, cable, substation))"
)
USER_AGENT = "PowerStack-Asia historical-grid-research/0.2"

REGIONAL_PBF = RAW_DIR / "malaysia-singapore-brunei-latest.osm.pbf"
CURRENT_LINES_FILE = PROCESSED_DIR / "johor_hv_power_lines.parquet"
CURRENT_SUBSTATIONS_FILE = PROCESSED_DIR / "johor_hv_substations_clean.parquet"
DEFAULT_CACHE_ROOT = RAW_DIR / "research" / "historical_osm_cache_v1"
DEFAULT_OUTPUT_ROOT = PROCESSED_DIR / "research" / "historical_osm"

TAG_COLUMNS = (
    "power",
    "voltage",
    "name",
    "operator",
    "construction",
    "construction:power",
    "proposed",
    "proposed:power",
    "disused",
    "disused:power",
    "abandoned",
    "abandoned:power",
    "start_date",
    "end_date",
    "status",
    "substation",
)
LIFECYCLE_TAG_COLUMNS = (
    "power",
    "construction",
    "construction:power",
    "proposed",
    "proposed:power",
    "disused",
    "disused:power",
    "abandoned",
    "abandoned:power",
    "start_date",
    "end_date",
    "status",
)
VOLTAGES_KV = (132, 275, 500)
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}
MAX_REQUEST_ATTEMPTS = 4


class HistoricalOsmError(RuntimeError):
    """Base error for a failed historical OSM extraction."""


class GeometryResolutionError(HistoricalOsmError):
    """An exact historical geometry could not be safely reconstructed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ExtractionConfig:
    """Inputs for one project-level historical spatial observation."""

    project_id: str
    information_cutoff_date: str
    snapshot_timestamp: str
    latitude: float
    longitude: float
    site_geometry_source: str
    site_geometry_quality: str
    search_radius_m: int = 30_000
    cache_root: Path = DEFAULT_CACHE_ROOT
    output_root: Path = DEFAULT_OUTPUT_ROOT

    @property
    def snapshot_key(self) -> str:
        return self.snapshot_timestamp.replace(":", "").replace("-", "")

    @property
    def output_dir(self) -> Path:
        return self.output_root / self.project_id / self.snapshot_key


@dataclass
class RequestStats:
    """Network and cache accounting for one extraction run."""

    network_requests: int = 0
    successful_network_responses: int = 0
    cache_hits: int = 0
    retries: int = 0
    failed_requests: int = 0


@dataclass
class ExtractionResult:
    """Important artifacts and run statistics returned to the runner."""

    feature_file: Path
    summary_file: Path
    comparison_file: Path
    failures_file: Path
    feature_record: dict[str, Any]
    summary: dict[str, Any]
    request_stats: RequestStats


def stable_key(payload: Any) -> str:
    """Return a deterministic short cache key for JSON-compatible inputs."""
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


def parse_osm_timestamp(value: str) -> datetime:
    """Parse an OSM UTC timestamp."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_bbox(config: ExtractionConfig) -> str:
    """Return the WGS84 envelope of a metric buffer around the site."""
    site = gpd.GeoSeries(
        [Point(config.longitude, config.latitude)],
        crs="EPSG:4326",
    ).to_crs(PROJECTED_CRS)
    envelope = gpd.GeoSeries(
        [site.iloc[0].buffer(config.search_radius_m).envelope],
        crs=PROJECTED_CRS,
    ).to_crs("EPSG:4326")
    return ",".join(f"{value:.8f}" for value in envelope.total_bounds)


class ResponseCache:
    """Sequential HTTP client with deterministic file caches and bounded retry."""

    def __init__(self, root: Path, stats: RequestStats):
        self.root = root
        self.stats = stats
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch(
        self,
        *,
        cache_file: Path,
        url: str,
        timeout: int,
        params: dict[str, str] | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        """Return cached bytes or make one conservatively retried GET request."""
        metadata_file = cache_file.with_suffix(cache_file.suffix + ".meta.json")
        if cache_file.exists():
            self.stats.cache_hits += 1
            metadata = (
                json.loads(metadata_file.read_text(encoding="utf-8"))
                if metadata_file.exists()
                else {"cache_file": str(cache_file), "metadata_missing": True}
            )
            return cache_file.read_bytes(), metadata

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        last_error: Exception | None = None
        for attempt in range(MAX_REQUEST_ATTEMPTS):
            self.stats.network_requests += 1
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code in RETRYABLE_STATUS_CODES:
                    raise requests.HTTPError(
                        f"HTTP {response.status_code} from {response.url}",
                        response=response,
                    )
                response.raise_for_status()
            except requests.RequestException as error:
                last_error = error
                retryable = (
                    error.response is None
                    or error.response.status_code in RETRYABLE_STATUS_CODES
                )
                if not retryable or attempt == MAX_REQUEST_ATTEMPTS - 1:
                    self.stats.failed_requests += 1
                    break
                self.stats.retries += 1
                time.sleep(2 ** (attempt + 1))
                continue

            self.stats.successful_network_responses += 1
            cache_file.write_bytes(response.content)
            metadata = {
                "request_url": response.url,
                "status_code": response.status_code,
                "fetched_at": datetime.now().astimezone().isoformat(),
                "cache_file": str(cache_file),
            }
            metadata_file.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return response.content, metadata

        raise HistoricalOsmError(
            f"Request failed after {MAX_REQUEST_ATTEMPTS} attempts: "
            f"{url}: {last_error}"
        )


def feature_kind(tags: dict[str, Any] | pd.Series) -> str | None:
    """Return the mapped line, cable, or substation type without inference."""
    power = tags.get("power")
    if power in {"line", "cable", "substation"}:
        return power
    if power == "construction":
        construction_power = tags.get("construction:power")
        if construction_power in {"line", "cable", "substation"}:
            return construction_power
    return None


def lifecycle_status(tags: dict[str, Any] | pd.Series) -> str:
    """Classify only the lifecycle tagging visible in OSM."""
    if tags.get("power") == "construction" and tags.get(
        "construction:power"
    ) in {"line", "cable", "substation"}:
        return "MAPPED_CONSTRUCTION_TAG"
    if tags.get("power") in {"line", "cable", "substation"}:
        return "MAPPED_STANDARD_TAG"
    return "LIFECYCLE_STATUS_NOT_FOUND"


def fetch_historical_inventory(
    config: ExtractionConfig,
    bbox: str,
    cache: ResponseCache,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch and cache the ohsome snapshot inventory and API metadata."""
    metadata_content, metadata_request = cache.fetch(
        cache_file=config.cache_root / "ohsome" / "metadata.json",
        url=f"{OHSOME_API_ROOT}/metadata",
        timeout=60,
    )
    metadata = json.loads(metadata_content)

    params = {
        "bboxes": bbox,
        "time": config.snapshot_timestamp,
        "filter": OHSOME_FILTER,
        "properties": "tags,metadata",
        "clipGeometry": "false",
        "timeout": "600",
    }
    query_key = stable_key(
        {
            "endpoint": "elements/bbox",
            "timestamp": config.snapshot_timestamp,
            "bbox": bbox,
            "filter": OHSOME_FILTER,
            "properties": "tags,metadata",
            "clip_geometry": False,
        }
    )
    inventory_content, inventory_request = cache.fetch(
        cache_file=(
            config.cache_root / "ohsome" / "inventory" / f"{query_key}.json"
        ),
        url=f"{OHSOME_API_ROOT}/elements/bbox",
        params=params,
        timeout=650,
    )
    inventory = json.loads(inventory_content)
    provenance = {
        "ohsome_api_version": metadata.get("apiVersion"),
        "ohsome_temporal_extent": metadata.get("extractRegion", {}).get(
            "temporalExtent"
        ),
        "ohsome_metadata_request": metadata_request,
        "ohsome_inventory_request": inventory_request,
        "ohsome_filter": OHSOME_FILTER,
        "bbox_wgs84": bbox,
        "snapshot_timestamp": config.snapshot_timestamp,
        "osm_attribution": inventory.get("attribution"),
    }
    return inventory, provenance


def inventory_geodataframe(inventory: dict[str, Any]) -> gpd.GeoDataFrame:
    """Normalize the ohsome inventory while preserving raw relevant tags."""
    rows = []
    for feature in inventory.get("features", []):
        properties = feature["properties"]
        tags = {
            key: value
            for key, value in properties.items()
            if not key.startswith("@")
        }
        kind = feature_kind(tags)
        if kind is None:
            continue
        row = {
            "osm_id": properties["@osmId"],
            "osm_type": properties["@osmType"],
            "osm_version": properties.get("@version"),
            "snapshot_timestamp": properties.get("@snapshotTimestamp"),
            "last_edit": properties.get("@lastEdit"),
            "feature_kind": kind,
            "lifecycle_status": lifecycle_status(tags),
            "tags_json": json.dumps(tags, sort_keys=True, ensure_ascii=False),
            "geometry": shape(feature["geometry"]),
        }
        for column in TAG_COLUMNS:
            row[column] = tags.get(column)
        rows.append(row)

    result = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    result["max_voltage_kv"] = result["voltage"].apply(max_voltage_kv)
    result["historical_topology_status"] = "OSM_MAPPED_AS_OF_CUTOFF"
    result["fact_type"] = "DERIVED"
    return result


def parse_xml(content: bytes) -> ET.Element:
    """Parse one cached or downloaded OSM XML response."""
    return ET.fromstring(content)


def tags_from_xml(element: ET.Element) -> dict[str, str]:
    """Return tags from an OSM XML primitive."""
    return {
        tag.attrib["k"]: tag.attrib["v"]
        for tag in element.findall("tag")
    }


def fetch_node_history_at_cutoff(
    config: ExtractionConfig,
    node_id: str,
    cache: ResponseCache,
) -> ET.Element:
    """Return the latest visible node version at or before the cutoff."""
    content, _ = cache.fetch(
        cache_file=(
            config.cache_root
            / "osm_api"
            / "node_histories"
            / config.snapshot_key
            / f"node_{node_id}.xml"
        ),
        url=f"{OSM_API_ROOT}/node/{node_id}/history",
        timeout=60,
    )
    cutoff = parse_osm_timestamp(config.snapshot_timestamp)
    candidates = [
        node
        for node in parse_xml(content).findall("node")
        if parse_osm_timestamp(node.attrib["timestamp"]) <= cutoff
    ]
    if not candidates:
        raise GeometryResolutionError(
            "NODE_VERSION_NOT_FOUND",
            f"Node {node_id} has no version at {config.snapshot_timestamp}",
        )
    node = max(
        candidates,
        key=lambda item: parse_osm_timestamp(item.attrib["timestamp"]),
    )
    if node.attrib.get("visible", "true") == "false":
        raise GeometryResolutionError(
            "NODE_NOT_VISIBLE_AT_CUTOFF",
            f"Node {node_id} was not visible at {config.snapshot_timestamp}",
        )
    return node


def fetch_way_nodes_at_cutoff(
    config: ExtractionConfig,
    node_ids: list[str],
    cache: ResponseCache,
) -> dict[str, ET.Element]:
    """Resolve the cutoff-valid coordinates for an ordered set of way nodes."""
    current_nodes: dict[str, ET.Element] = {}
    unique_ids = sorted(set(node_ids), key=int)
    for start in range(0, len(unique_ids), 400):
        chunk = unique_ids[start : start + 400]
        chunk_key = stable_key(
            {"endpoint": "nodes", "node_ids": chunk}
        )
        content, _ = cache.fetch(
            cache_file=(
                config.cache_root
                / "osm_api"
                / "current_node_batches"
                / f"{chunk_key}.xml"
            ),
            url=f"{OSM_API_ROOT}/nodes",
            params={"nodes": ",".join(chunk)},
            timeout=60,
        )
        current_nodes.update(
            {
                node.attrib["id"]: node
                for node in parse_xml(content).findall("node")
            }
        )

    cutoff = parse_osm_timestamp(config.snapshot_timestamp)
    nodes_at_cutoff = {}
    for node_id in unique_ids:
        current = current_nodes.get(node_id)
        if (
            current is not None
            and parse_osm_timestamp(current.attrib["timestamp"]) <= cutoff
        ):
            nodes_at_cutoff[node_id] = current
        else:
            nodes_at_cutoff[node_id] = fetch_node_history_at_cutoff(
                config,
                node_id,
                cache,
            )
    return nodes_at_cutoff


def fetch_exact_historical_element(
    config: ExtractionConfig,
    feature: pd.Series,
    cache: ResponseCache,
) -> dict[str, Any]:
    """Reconstruct one exact node or way version selected by ohsome."""
    osm_type, numeric_id = feature["osm_id"].split("/", 1)
    version = int(feature["osm_version"])
    if osm_type == "relation":
        raise GeometryResolutionError(
            "UNSUPPORTED_RELATION_GEOMETRY",
            (
                f"Historical relation {feature['osm_id']} could be nearest, "
                "but safe member-version reconstruction is not implemented."
            ),
        )
    if osm_type not in {"node", "way"}:
        raise GeometryResolutionError(
            "UNSUPPORTED_OSM_TYPE",
            f"Unsupported OSM primitive type: {osm_type}",
        )

    content, _ = cache.fetch(
        cache_file=(
            config.cache_root
            / "osm_api"
            / "objects"
            / f"{osm_type}_{numeric_id}_v{version}.xml"
        ),
        url=f"{OSM_API_ROOT}/{osm_type}/{numeric_id}/{version}",
        timeout=60,
    )
    xml_element = parse_xml(content).find(osm_type)
    if xml_element is None:
        raise GeometryResolutionError(
            "VERSIONED_OBJECT_NOT_FOUND",
            f"OSM API did not return {feature['osm_id']} version {version}",
        )

    result: dict[str, Any] = {
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

    node_ids = [node.attrib["ref"] for node in xml_element.findall("nd")]
    if len(node_ids) < 2:
        raise GeometryResolutionError(
            "WAY_GEOMETRY_NOT_FOUND",
            f"Historical way {feature['osm_id']} has fewer than two nodes",
        )
    nodes = fetch_way_nodes_at_cutoff(config, node_ids, cache)
    result["geometry"] = [
        {
            "lat": float(nodes[node_id].attrib["lat"]),
            "lon": float(nodes[node_id].attrib["lon"]),
        }
        for node_id in node_ids
    ]
    return result


def element_geometry(element: dict[str, Any]):
    """Convert a reconstructed OSM node or way to Shapely geometry."""
    if element["type"] == "node":
        return Point(element["lon"], element["lat"])
    coordinates = [
        (node["lon"], node["lat"])
        for node in element.get("geometry", [])
    ]
    if len(coordinates) < 2:
        return None
    if len(coordinates) >= 4 and coordinates[0] == coordinates[-1]:
        return Polygon(coordinates)
    return LineString(coordinates)


def exact_candidate_geodataframe(
    exact_cache: dict[str, dict[str, Any]],
) -> gpd.GeoDataFrame:
    """Normalize exact geometries resolved while proving nearest distances."""
    rows = []
    for osm_id, element in exact_cache.items():
        tags = element.get("tags", {})
        row = {
            "osm_id": osm_id,
            "osm_type": element["type"],
            "osm_version": element.get("version"),
            "osm_timestamp": element.get("timestamp"),
            "feature_kind": feature_kind(tags),
            "lifecycle_status": lifecycle_status(tags),
            "tags_json": json.dumps(tags, sort_keys=True, ensure_ascii=False),
            "geometry": element_geometry(element),
        }
        for column in TAG_COLUMNS:
            row[column] = tags.get(column)
        rows.append(row)
    if not rows:
        return gpd.GeoDataFrame(
            columns=["osm_id", "osm_type", "geometry"],
            geometry="geometry",
            crs="EPSG:4326",
        )
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def nearest_exact_historical_distance(
    *,
    metric_name: str,
    features: gpd.GeoDataFrame,
    site,
    config: ExtractionConfig,
    cache: ResponseCache,
    exact_cache: dict[str, dict[str, Any]],
    failures: list[dict[str, Any]],
) -> tuple[float | None, str | None, str]:
    """Resolve only objects whose bbox can still contain the nearest feature."""
    if features.empty:
        return None, None, "NOT_FOUND"

    candidates = features.to_crs(PROJECTED_CRS).copy()
    candidates["bbox_lower_bound_m"] = candidates.geometry.distance(site)
    candidates = candidates.sort_values(["bbox_lower_bound_m", "osm_id"])
    best_distance_m = float("inf")
    best_id = None

    for _, candidate in candidates.iterrows():
        lower_bound_m = float(candidate["bbox_lower_bound_m"])
        if lower_bound_m >= best_distance_m:
            break
        osm_id = candidate["osm_id"]
        try:
            if osm_id not in exact_cache:
                exact_cache[osm_id] = fetch_exact_historical_element(
                    config,
                    candidate,
                    cache,
                )
            geometry = element_geometry(exact_cache[osm_id])
            if geometry is None:
                raise GeometryResolutionError(
                    "GEOMETRY_NOT_FOUND",
                    f"No exact geometry was reconstructed for {osm_id}",
                )
        except (HistoricalOsmError, requests.RequestException) as error:
            code = getattr(error, "code", "GEOMETRY_RESOLUTION_FAILED")
            failures.append(
                {
                    "metric": metric_name,
                    "osm_id": osm_id,
                    "failure_code": code,
                    "message": str(error),
                    "bbox_lower_bound_km": lower_bound_m / 1000,
                }
            )
            return None, None, code

        projected = gpd.GeoSeries(
            [geometry], crs="EPSG:4326"
        ).to_crs(PROJECTED_CRS).iloc[0]
        exact_distance_m = float(projected.distance(site))
        if exact_distance_m < best_distance_m:
            best_distance_m = exact_distance_m
            best_id = osm_id

    if best_id is None:
        return None, None, "NOT_FOUND"
    return best_distance_m / 1000, best_id, "DERIVED"


def historical_distance_metrics(
    inventory: gpd.GeoDataFrame,
    config: ExtractionConfig,
    cache: ResponseCache,
    exact_cache: dict[str, dict[str, Any]],
    failures: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """Calculate historical voltage-specific distances and nearest IDs."""
    site = gpd.GeoSeries(
        [Point(config.longitude, config.latitude)],
        crs="EPSG:4326",
    ).to_crs(PROJECTED_CRS).iloc[0]
    lines = inventory[inventory["feature_kind"].isin(["line", "cable"])]
    substations = inventory[
        inventory["feature_kind"].eq("substation")
        & inventory["max_voltage_kv"].fillna(0).ge(100)
    ]

    subsets: dict[str, gpd.GeoDataFrame] = {}
    for voltage_kv in VOLTAGES_KV:
        subsets[f"{voltage_kv}kv_line"] = lines[
            lines["voltage"].apply(
                lambda value, voltage=voltage_kv: has_voltage(value, voltage)
            )
        ]
    subsets["hv_substation"] = substations
    for voltage_kv in VOLTAGES_KV:
        subsets[f"{voltage_kv}kv_substation"] = substations[
            substations["voltage"].apply(
                lambda value, voltage=voltage_kv: has_voltage(value, voltage)
            )
        ]

    distances = {}
    nearest_ids = {}
    statuses = {}
    for metric_name, features in subsets.items():
        distance, osm_id, status = nearest_exact_historical_distance(
            metric_name=metric_name,
            features=features,
            site=site,
            config=config,
            cache=cache,
            exact_cache=exact_cache,
            failures=failures,
        )
        distances[f"distance_{metric_name}_osm_as_of_cutoff_km"] = distance
        nearest_ids[f"nearest_{metric_name}_osm_id"] = osm_id
        statuses[f"distance_{metric_name}_status"] = status
    return distances, nearest_ids, statuses


def find_osmium() -> str:
    """Locate Osmium in PATH or next to the active Conda environment."""
    path = shutil.which("osmium")
    if path:
        return path
    candidate = Path(sys.executable).resolve().parent / "Library" / "bin" / "osmium.exe"
    if candidate.exists():
        return str(candidate)
    raise HistoricalOsmError("Osmium is required for the current comparison.")


def run_command(command: list[str]) -> None:
    """Run one local command and surface its failure."""
    subprocess.run(command, check=True)


def build_current_extract(config: ExtractionConfig, bbox: str) -> dict[str, Any]:
    """Build a disposable current PBF subset without changing canonical files."""
    if not REGIONAL_PBF.exists():
        raise FileNotFoundError(REGIONAL_PBF)
    output_dir = config.output_dir
    current_bbox = output_dir / "current_bbox.osm.pbf"
    current_power = output_dir / "current_power_features.osm.pbf"
    current_geojson = output_dir / "current_power_features.geojson"
    osmium = find_osmium()
    run_command(
        [
            osmium,
            "extract",
            "-s",
            "complete_ways",
            "-b",
            bbox,
            str(REGIONAL_PBF),
            "-o",
            str(current_bbox),
            "-O",
        ]
    )
    run_command(
        [
            osmium,
            "tags-filter",
            str(current_bbox),
            "w/power=line",
            "w/power=cable",
            "power=substation",
            "power=construction",
            "-o",
            str(current_power),
            "-O",
        ]
    )
    run_command(
        [
            osmium,
            "export",
            str(current_power),
            "-u",
            "type_id",
            "-a",
            "version,timestamp",
            "-o",
            str(current_geojson),
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


def current_geodataframe(config: ExtractionConfig) -> gpd.GeoDataFrame:
    """Load the current subset and keep stable OSM primitive IDs only."""
    path = config.output_dir / "current_power_features.geojson"
    current = gpd.read_file(path)
    id_column = "@id" if "@id" in current.columns else "id"
    if id_column not in current.columns:
        raise HistoricalOsmError(
            f"Current Osmium export lacks an ID; columns={list(current.columns)}"
        )
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
    current["feature_kind"] = current.apply(feature_kind, axis=1)
    current = current[current["feature_kind"].notna()].copy()
    current["lifecycle_status"] = current.apply(lifecycle_status, axis=1)
    current["max_voltage_kv"] = current["voltage"].apply(max_voltage_kv)
    return current


def nearest_distance_km(features: gpd.GeoDataFrame, site) -> float | None:
    """Return one metric point-to-feature distance."""
    if features.empty:
        return None
    projected = features.to_crs(PROJECTED_CRS)
    return float(projected.geometry.distance(site).min() / 1000)


def current_distance_metrics(config: ExtractionConfig) -> dict[str, float | None]:
    """Calculate comparison distances from canonical current Parquets."""
    lines = gpd.read_parquet(CURRENT_LINES_FILE)
    substations = gpd.read_parquet(CURRENT_SUBSTATIONS_FILE)
    site = gpd.GeoSeries(
        [Point(config.longitude, config.latitude)],
        crs="EPSG:4326",
    ).to_crs(PROJECTED_CRS).iloc[0]
    result = {}
    for voltage_kv in VOLTAGES_KV:
        subset = lines[
            lines["voltage"].apply(
                lambda value, voltage=voltage_kv: has_voltage(value, voltage)
            )
        ]
        result[f"distance_{voltage_kv}kv_line_current_osm_km"] = (
            nearest_distance_km(subset, site)
        )
    result["distance_hv_substation_current_osm_km"] = nearest_distance_km(
        substations,
        site,
    )
    for voltage_kv in VOLTAGES_KV:
        subset = substations[
            substations["voltage"].apply(
                lambda value, voltage=voltage_kv: has_voltage(value, voltage)
            )
        ]
        result[f"distance_{voltage_kv}kv_substation_current_osm_km"] = (
            nearest_distance_km(subset, site)
        )
    return result


def make_change_detection(
    historical: gpd.GeoDataFrame,
    current: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """Compare stable explicit-HV primitive IDs and relevant tags."""
    historical_hv = historical[
        historical["max_voltage_kv"].fillna(0).ge(100)
    ].copy()
    current_hv = current[current["max_voltage_kv"].fillna(0).ge(100)].copy()
    historical_by_id = historical_hv.set_index("osm_id", drop=False)
    current_by_id = current_hv.set_index("osm_id", drop=False)
    all_ids = sorted(set(historical_by_id.index) | set(current_by_id.index))
    rows = []

    for osm_id in all_ids:
        old = historical_by_id.loc[osm_id] if osm_id in historical_by_id.index else None
        new = current_by_id.loc[osm_id] if osm_id in current_by_id.index else None
        if old is not None and new is not None:
            topology_status = "PRESENT_AT_CUTOFF_AND_CURRENT"
        elif new is not None:
            topology_status = "NOT_MAPPED_IN_OSM_AT_CUTOFF"
        else:
            topology_status = "MAPPED_AT_CUTOFF_NOT_IN_CURRENT_SNAPSHOT"

        row = {"osm_id": osm_id, "topology_status": topology_status}
        for prefix, feature in (("historical", old), ("current", new)):
            row[f"{prefix}_feature_kind"] = (
                None if feature is None else feature.get("feature_kind")
            )
            row[f"{prefix}_voltage"] = (
                None if feature is None else feature.get("voltage")
            )
            row[f"{prefix}_name"] = (
                None if feature is None else feature.get("name")
            )
            row[f"{prefix}_lifecycle_status"] = (
                None if feature is None else feature.get("lifecycle_status")
            )
            row[f"{prefix}_lifecycle_tags"] = (
                None
                if feature is None
                else json.dumps(
                    {
                        column: feature.get(column)
                        for column in LIFECYCLE_TAG_COLUMNS
                        if pd.notna(feature.get(column))
                    },
                    sort_keys=True,
                )
            )
        row["historical_bbox_hash"] = (
            None if old is None else geometry_hash(old.geometry)
        )
        row["current_geometry_hash"] = (
            None if new is None else geometry_hash(new.geometry)
        )
        rows.append(row)

    change = pd.DataFrame(rows)
    if not change.empty:
        for field in ("voltage", "name", "lifecycle_status", "lifecycle_tags"):
            change[f"{field}_changed"] = (
                change[f"historical_{field}"].fillna("")
                != change[f"current_{field}"].fillna("")
            )
        change["relevant_tag_changed"] = change[
            [
                "voltage_changed",
                "name_changed",
                "lifecycle_status_changed",
                "lifecycle_tags_changed",
            ]
        ].any(axis=1)
    return change


def inventory_counts(inventory: gpd.GeoDataFrame) -> dict[str, int]:
    """Return transparent inventory and lifecycle counts."""
    lines = inventory[inventory["feature_kind"].eq("line")]
    cables = inventory[inventory["feature_kind"].eq("cable")]
    substations = inventory[inventory["feature_kind"].eq("substation")]
    return {
        "historical_feature_count": len(inventory),
        "historical_line_count": len(lines),
        "historical_cable_count": len(cables),
        "historical_hv_line_count": int(
            lines["max_voltage_kv"].fillna(0).ge(100).sum()
        ),
        "historical_hv_cable_count": int(
            cables["max_voltage_kv"].fillna(0).ge(100).sum()
        ),
        "historical_substation_count": len(substations),
        "historical_hv_substation_count": int(
            substations["max_voltage_kv"].fillna(0).ge(100).sum()
        ),
        "mapped_standard_tag_count": int(
            inventory["lifecycle_status"].eq("MAPPED_STANDARD_TAG").sum()
        ),
        "mapped_construction_tag_count": int(
            inventory["lifecycle_status"].eq("MAPPED_CONSTRUCTION_TAG").sum()
        ),
        "lifecycle_status_not_found_count": int(
            inventory["lifecycle_status"]
            .eq("LIFECYCLE_STATUS_NOT_FOUND")
            .sum()
        ),
        "historical_relation_count": int(inventory["osm_type"].eq("relation").sum()),
    }


def save_outputs(
    *,
    config: ExtractionConfig,
    inventory: gpd.GeoDataFrame,
    exact_cache: dict[str, dict[str, Any]],
    feature_record: dict[str, Any],
    change: pd.DataFrame,
    failures: list[dict[str, Any]],
    summary: dict[str, Any],
) -> ExtractionResult:
    """Write ignored derived outputs and return their paths."""
    output_dir = config.output_dir
    inventory_file = output_dir / "historical_inventory.geojson"
    exact_file = output_dir / "historical_exact_candidates.geojson"
    feature_file = output_dir / "historical_project_features.csv"
    comparison_file = output_dir / "historical_current_comparison.csv"
    failures_file = output_dir / "geometry_resolution_failures.csv"
    summary_file = output_dir / "extraction_summary.json"

    inventory.to_file(inventory_file, driver="GeoJSON")
    exact = exact_candidate_geodataframe(exact_cache)
    if not exact.empty:
        exact.to_file(exact_file, driver="GeoJSON")
    pd.DataFrame([feature_record]).to_csv(feature_file, index=False)
    change.to_csv(comparison_file, index=False)
    pd.DataFrame(
        failures,
        columns=[
            "metric",
            "osm_id",
            "failure_code",
            "message",
            "bbox_lower_bound_km",
        ],
    ).to_csv(failures_file, index=False)
    summary_file.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return ExtractionResult(
        feature_file=feature_file,
        summary_file=summary_file,
        comparison_file=comparison_file,
        failures_file=failures_file,
        feature_record=feature_record,
        summary=summary,
        request_stats=RequestStats(**summary["request_stats"]),
    )


def run_historical_osm_extraction(config: ExtractionConfig) -> ExtractionResult:
    """Run one complete historical extraction and current comparison."""
    config.output_dir.mkdir(parents=True, exist_ok=True)
    stats = RequestStats()
    cache = ResponseCache(config.cache_root, stats)
    bbox = build_bbox(config)
    raw_inventory, provenance = fetch_historical_inventory(config, bbox, cache)
    inventory = inventory_geodataframe(raw_inventory)
    counts = inventory_counts(inventory)

    current_pbf_info = build_current_extract(config, bbox)
    current = current_geodataframe(config)
    exact_cache: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    historical_distances, nearest_ids, distance_statuses = (
        historical_distance_metrics(
            inventory,
            config,
            cache,
            exact_cache,
            failures,
        )
    )
    current_distances = current_distance_metrics(config)
    change = make_change_detection(inventory, current)

    feature_record = {
        "project_id": config.project_id,
        "information_cutoff_date": config.information_cutoff_date,
        "snapshot_timestamp": config.snapshot_timestamp,
        "snapshot_source": "ohsome snapshot IDs + versioned OSM API geometry",
        "site_latitude": config.latitude,
        "site_longitude": config.longitude,
        "site_geometry_source": config.site_geometry_source,
        "site_geometry_quality": config.site_geometry_quality,
        **historical_distances,
        **nearest_ids,
        **distance_statuses,
        "historical_line_count": counts["historical_line_count"],
        "historical_cable_count": counts["historical_cable_count"],
        "historical_hv_line_count": counts["historical_hv_line_count"],
        "historical_hv_cable_count": counts["historical_hv_cable_count"],
        "historical_substation_count": counts["historical_substation_count"],
        "historical_hv_substation_count": counts[
            "historical_hv_substation_count"
        ],
        "historical_topology_status": "OSM_MAPPED_AS_OF_CUTOFF",
        "historical_topology_fact_type": "DERIVED",
        "notes": (
            "OSM_MAPPED_AS_OF_CUTOFF is public map-state evidence and does "
            "not imply PHYSICALLY_VERIFIED_PRE_EXISTING, commissioning, or "
            "available grid capacity."
        ),
    }
    change_counts = (
        change["topology_status"].value_counts().to_dict()
        if not change.empty
        else {}
    )
    changed_tags = int(
        (
            change["topology_status"].eq("PRESENT_AT_CUTOFF_AND_CURRENT")
            & change["relevant_tag_changed"]
        ).sum()
    ) if not change.empty else 0
    summary = {
        "project": asdict(config),
        "extraction_date": date.today().isoformat(),
        "projected_crs": PROJECTED_CRS,
        "provenance": provenance,
        "request_stats": asdict(stats),
        "inventory_counts": counts,
        "exact_geometry_count": len(exact_cache),
        "historical_distances_km": historical_distances,
        "historical_nearest_osm_ids": nearest_ids,
        "distance_statuses": distance_statuses,
        "current_distances_km": current_distances,
        "current_pbf_header": current_pbf_info.get("header"),
        "change_counts_explicit_ge_100kv": change_counts,
        "surviving_objects_with_relevant_tag_changes": changed_tags,
        "geometry_resolution_failures": failures,
        "interpretation": {
            "historical_presence": "OSM_MAPPED_AS_OF_CUTOFF",
            "current_only": "NOT_MAPPED_IN_OSM_AT_CUTOFF",
            "historical_only": "MAPPED_AT_CUTOFF_NOT_IN_CURRENT_SNAPSHOT",
            "physical_timing": "NOT_FOUND without independent dated evidence",
            "standard_osm_tag": (
                "MAPPED_STANDARD_TAG does not prove operational status"
            ),
            "construction_osm_tag": (
                "MAPPED_CONSTRUCTION_TAG does not prove construction timing"
            ),
        },
    }
    return save_outputs(
        config=config,
        inventory=inventory,
        exact_cache=exact_cache,
        feature_record=feature_record,
        change=change,
        failures=failures,
        summary=summary,
    )
