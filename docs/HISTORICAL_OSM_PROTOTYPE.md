# Historical OSM Feature Extraction

## Purpose and evidence boundary

The hardened extractor builds conservative, project-level OSM grid features at
a historical information cutoff. Historical presence means
`OSM_MAPPED_AS_OF_CUTOFF`: the object was represented in the public map. It
does not prove `PHYSICALLY_VERIFIED_PRE_EXISTING`, commissioning, ownership, or
available capacity. Absence from the snapshot does not prove physical absence.
Calculated distances and counts are `DERIVED`.

The Step 38 prototype command remains as a compatibility wrapper. Normal use is:

```powershell
python src/build_historical_osm_features.py
```

With no arguments this runs the PDG JH1 regression case. A different project
must supply all evidence-backed inputs explicitly; run `--help` for the flags.
The script processes one project at a time and does not read or modify the Power
Pathway schema.

## Code structure

- `build_historical_osm_features.py`: short command-line entry point and PDG
  regression defaults.
- `historical_osm_grid.py`: inventory, cache, exact geometry, distance,
  lifecycle, comparison, and output functions.
- `prototype_historical_osm_grid.py`: compatibility wrapper for the old command.

The reusable module continues to use `powerstack_utils.py` for CRS, explicit
voltage parsing, voltage matching, and geometry hashing.

## Historical query and exact geometry

For PDG, the extractor creates an approximately 30 km envelope in `EPSG:3375`
and submits:

```text
GET https://api.ohsome.org/v1/elements/bbox
bboxes=103.14454647,1.41989581,103.68418662,1.96292189
time=2023-05-22T23:59:59Z
filter=power in (line, cable, substation) or
       (power = construction and
        construction:power in (line, cable, substation))
properties=tags,metadata
clipGeometry=false
timeout=600
```

ohsome supplies the cutoff-valid object ID, object version, tags, metadata, and
geometry bounding box. For each possible nearest feature, the extractor obtains
the immutable versioned OSM object and reconstructs its geometry from node
versions valid at the cutoff. Bounding-box lower bounds stop the search only
when no unresolved object can be closer. Missing voltage is never inferred.

The resolver safely supports historical nodes and ways. Historical relations
require member versions and potentially nested multipolygon assembly. Rather
than substitute current members or approximate geometry, a relation that could
be nearest produces `UNSUPPORTED_RELATION_GEOMETRY` in the failure output and
leaves that metric unresolved.

## Raw-response caching and failures

All historical HTTP responses are cached below ignored
`data/raw/research/historical_osm_cache_v1/`:

- ohsome metadata and inventory responses;
- immutable versioned OSM node/way responses;
- bulk current-node responses used as a safe shortcut where their edit date is
  before the cutoff;
- node histories needed when a node changed after the cutoff.

Inventory keys hash the timestamp, bounding box, filter, and response options.
OSM object keys contain primitive type, ID, and version; node-history paths also
contain the cutoff timestamp. Requests are sequential, have explicit timeouts,
and use at most four attempts with bounded exponential backoff. A geometry
failure is recorded in `geometry_resolution_failures.csv`; it is never silently
dropped or treated as `NOT_FOUND`.

The fresh PDG validation used 53 network requests. Its identical second run used
zero network requests and 53 cache hits, and produced the same feature-file
SHA-256 hash.

## Lifecycle interpretation

The inventory preserves raw construction, proposed, disused, abandoned,
start/end date, status, name, operator, voltage, and other OSM tags where
available. Derived tag-form classifications are:

- `MAPPED_STANDARD_TAG`
- `MAPPED_CONSTRUCTION_TAG`
- `LIFECYCLE_STATUS_NOT_FOUND`

These describe OSM tagging only. A standard `power=line` or `power=substation`
tag is not proof that an asset was operational. A construction tag is not proof
of its physical construction date.

## Derived outputs

Each run writes ignored artifacts below
`data/processed/research/historical_osm/<project_id>/<timestamp>/`:

- `historical_project_features.csv`: project inputs, historical distances,
  nearest IDs, inventory counts, metric statuses, fact type, and warning notes;
- `historical_inventory.geojson`: normalized historical inventory and raw tags;
- `historical_exact_candidates.geojson`: exact geometries used to prove nearest
  distances;
- `historical_current_comparison.csv`: stable-ID presence and relevant tag
  changes;
- `geometry_resolution_failures.csv`: explicit unresolved-object evidence;
- `extraction_summary.json`: query provenance, cache/request statistics, counts,
  current comparison, and interpretation;
- disposable current PBF/GeoJSON subsets for stable-ID comparison.

The comparison uses the canonical current line and substation Parquets for
distances and a disposable local Geofabrik/Osmium subset for stable primitive
IDs. Synthetic Osmium `area/...` records are excluded. Canonical files are never
written.

## Historical-training geometry contract

Strict historical training recognizes two potential geometry tiers. Tier B is
methodology only and is not implemented by the current extractor.

### Tier A — exact project geometry

Accepted evidence is:

- `AUTHORITATIVE_PROJECT_POLYGON`
- `AUTHORITATIVE_PROJECT_POINT`
- `REPRODUCIBLY_DERIVED_PROJECT_GEOMETRY`

A reproducibly derived geometry must start from an authoritative project or
cadastral artifact, document its CRS and transformation, retain an error or
residual measure, and be independently repeatable. A park point, geocoded
address, Google Maps pin, parent-parcel centroid, or current infrastructure
location is not project geometry.

Tier A may support geometry-to-asset distances, nearest historical primitive
IDs, voltage/lifecycle-specific inventory counts, fixed-radius counts, and
intersections. Geometry type remains part of the feature definition; a project
polygon and an authoritative site point are not silently treated as the same
measurement.

### Tier B — bounded containing parcel

Tier B requires an authoritative parcel polygon, verified project containment,
and evidence that the parcel boundary was valid at the historical cutoff. The
exact project footprint remains unknown. Do not substitute the parcel centroid.

Permitted future outputs are intervals and bounds, including:

- `distance_min` and `distance_max`
- `possible_within_radius`
- `guaranteed_within_radius`
- minimum and maximum possible inventory counts

An interval is not collapsed to a midpoint. It is unusable when the parcel
spans materially different grid environments or the bounds cannot preserve a
meaningful proximity classification. Radius sets and any interval-width rule
must be fixed before outcome analysis. Tier B feature engineering is deferred;
do not pass a containing parcel to the current point extractor.

## Existing-project spatial eligibility

This classification uses only `dc_project_locations_seed.csv`:

| Project | Classification | Reason |
|---|---|---|
| DC-JHR-001 GDS | `PROXY_ONLY` | Stored Nusajaya Tech Park representative point, not the parcel. |
| DC-JHR-002 Yondr / Vantage | `PROXY_ONLY` | Stored STeP East park-section representative point, not the campus. |
| DC-JHR-003 TM Nxera | `LOCATION_NOT_SUFFICIENT` | Exact plot identifier but no authoritative geometry. |
| DC-JHR-004 PDG JH1 | `READY_FOR_HISTORICAL_SPATIAL_EXTRACTION` | Official site coordinate stored. |
| DC-JHR-005 Bridge MY07 | `LOCATION_NOT_SUFFICIENT` | Ulu Tiram locality only. |
| DC-JHR-006 Digital Halo / Nanda | `LOCATION_NOT_SUFFICIENT` | Exact title but no stored polygon or coordinate. |
| DC-JHR-007 YTL | `LOCATION_NOT_SUFFICIENT` | Campus locality only. |
| DC-JHR-008 STT | `LOCATION_NOT_SUFFICIENT` | Industrial park only; no stored project coordinate. |

Do not manufacture centroids for the six projects without sufficient site
geometry. Proxy runs, if later approved, must remain clearly labelled.

## Remaining limitations

OSM edit time is not physical construction time. Object appearance,
disappearance, and tag changes may be mapping activity. Public APIs remain
unsuitable for parallel request storms, so this pipeline is intended for a small
sequential project batch with caching. Relation geometry remains explicitly
unsupported. Reconsider an operated OSHDB service or local history extract only
if measured project volume justifies it; this pipeline does not require a
full-history planet download.

Sources: [ohsome elements extraction](https://docs.ohsome.org/ohsome-api/v1/endpoints.html),
[ohsome filter syntax](https://docs.ohsome.org/ohsome-api/v1/filter.html),
[ohsome time parameter](https://docs.ohsome.org/ohsome-api/development/time.html),
[OSM API v0.6](https://wiki.openstreetmap.org/wiki/API_v0.6), and
[OpenStreetMap attribution](https://www.openstreetmap.org/copyright).
