# PowerStack Market Intelligence Model

**Status:** Design authority; not yet implemented

**Baseline date:** 17 August 2026

## Purpose

This document defines the shared Intelligence Spine used by Site Diligence,
Origination Intelligence, Market Intelligence, and Historical Calibration. It
is a target information architecture, not a description of tables that already
exist. Implemented fields and vocabularies remain governed by
[DATA_DICTIONARY.md](DATA_DICTIONARY.md).

The model generalizes the existing Johor historical evidence without replacing
the Power Pathway model. It should support approximately 30–50 material Johor
data-centre projects or campuses first, while remaining extensible to grid,
generation, renewable procurement, land, planning, contractors, and capital.

## Architectural guardrail: one source of truth

The Intelligence Spine must not become an independent duplicate source of truth
beside existing historical evidence.

Existing source-backed facts should be:

1. referenced by stable record ID;
2. crosswalked to the common entity or event;
3. normalized through views, links, or controlled transformations;
4. copied only when an explicit canonical migration is approved.

For example, one real-world ESA can be represented by a linked
`connection_events` row and `power_pathway_milestones` row. Those rows must not
produce two unrelated intelligence events. Similarly, a `grid_asset_events`
record and a pathway component referring to the same substation work must share
canonical identity or an explicit relationship.

Before historical facts are loaded into a new event table, implementation must
define:

- the real-world event's canonical ID;
- which current record is authoritative for each assertion;
- how linked current records are retained;
- how multiple sources attach to the event;
- how conflicts and later corrections are handled;
- how duplicate event generation is prevented.

Step 58 should first unit-test this rule against the existing eight projects.

## Design principles

### Stable internal identity

Internal IDs are immutable and must not depend solely on an entity name or
mutable status. Suggested namespaces include `ORG`, `PROJECT`, `SITE`, `PARCEL`,
`ASSET`, `AGREEMENT`, `CAPACITY`, `EVENT`, and `SOURCE`.

Existing IDs such as `DC-JHR-001`, `PP-JHR-001`, and source-backed event IDs are
preserved. External identifiers—company registration number, ticker, official
planning reference, OSM primitive ID, title number, UPI, ArcGIS feature ID, or
filing ID—are stored separately.

### Minimal normalized core

The initial physical model should use a small number of general entities and
facts rather than one table for every market concept:

- `ORGANIZATION`
- `PROJECT`
- `SITE`
- `LAND_PARCEL`
- `INFRASTRUCTURE_ASSET`
- `AGREEMENT`
- `CAPACITY_OBSERVATION`
- `INTELLIGENCE_EVENT`
- `ENTITY_RELATIONSHIP`
- `SOURCE`
- `EVIDENCE_LINK`

Power agreements and renewable procurement are agreement types. Grid and
generation projects are project types. Contractors are organizations in roles.
Transactions, financings, planning actions, construction events, and
operational milestones use the common event model unless real records later
demonstrate the need for a specialized table.

### Event time and knowledge time

Every material fact distinguishes:

- event or effective date;
- date precision;
- source publication date;
- retrieval date;
- information cutoff where relevant;
- valid-from and valid-to for changing relationships or states.

A later source may verify an earlier event. Its event date does not make the
source available at that earlier date. Historical feature construction uses the
knowledge cutoff as well as the event chronology.

### Evidence linkage

Entity master rows combine facts from multiple sources. One row-level URL is
therefore insufficient at scale. `EVIDENCE_LINK` should connect a source to a
specific record or field assertion and retain:

- record type and ID;
- field or assertion;
- source ID;
- evidence role such as primary, corroborating, geometry, title, or conflict;
- page, section, table, or source span where useful;
- fact type;
- analyst review state;
- notes.

Machine-extracted candidate evidence belongs in staging and is not an accepted
evidence link until validated.

## Core entities

### `ORGANIZATION`

Represents a legal entity, operating brand, utility, authority, developer,
investor, fund, contractor, consultant, lender, or other institution.

Key attributes:

- stable organization ID;
- canonical and legal name;
- organization type;
- jurisdiction;
- registration number, ticker, LEI, or other external ID where verified;
- current-status snapshot;
- source and evidence links.

Developer, operator, owner, contractor, investor, lender, applicant, utility,
and counterparty are roles through `ENTITY_RELATIONSHIP`, not permanent company
types. Former names and aliases must resolve to the same organization without
destroying their dates.

### `PROJECT`

Represents a separately identifiable development. Types may include data-centre
campus, data-centre phase, grid project, generation project, renewable project,
industrial infrastructure, or another approved class.

Key attributes:

- stable project ID;
- canonical project name;
- project type;
- parent project ID;
- campus/phase/facility scope;
- current status and as-of date;
- country, state, and principal geography;
- project vehicle where verified;
- source and evidence links.

Milestones are events rather than a growing collection of date columns. The
current `dc_projects` table remains the data-centre historical specialization
until a migration is explicitly designed.

### Campus and phase hierarchy

Capacity and status must be scoped to the correct level:

- portfolio;
- market or regional pipeline;
- campus;
- facility/building;
- phase;
- expansion.

A phase is linked to its parent campus. Campus capacity is not added to phase
capacity unless the source explicitly establishes non-overlapping scope.
Renaming or ownership transfer does not create a new project unless the
underlying development is genuinely distinct.

### `SITE`

Represents the physical development location independently of the project or
owner. Multiple phases or successive projects may use one site.

Key attributes:

- site ID and name;
- country, state, district, mukim, locality, and planning authority;
- geometry classification;
- canonical geometry reference;
- source-stated and calculated area;
- geometry effective-date status;
- source and evidence links.

The current location CSV and curated geometry GeoJSON are preserved. Future
site integration should link them rather than replacing stronger geometry with
a lower-quality point or proxy.

### `LAND_PARCEL`

Represents a cadastral or title unit independently of project use.

Key attributes:

- parcel ID;
- state, district, mukim, and section;
- PTD, lot, H.S.(D), GRN, UPI, and other identifiers where supported;
- title area and unit;
- owner relationship;
- geometry reference and authority;
- title-succession and effective-date status;
- source and evidence links.

PTD, provisional title, final lot, and ownership succession must not be assumed
equivalent. A project may occupy all, part, or several parcels. Site-to-parcel
relationships therefore carry occupancy scope and valid dates.

### `INFRASTRUCTURE_ASSET`

Represents a physical grid, generation, or supporting infrastructure asset.

Key attributes:

- asset ID and type;
- asset name and external source IDs;
- geometry;
- voltage;
- operator/owner relationships;
- source-stated capacity value and unit where applicable;
- current lifecycle/map status;
- linked delivery project;
- source and evidence links.

Current OSM objects retain their OSM type, ID, version, timestamp, tags, and
attribution. An OSM asset is mapped topology, not automatically a utility-
verified physical asset. Dated independent evidence is required for
`PRE_EXISTING_VERIFIED`, commissioning, energisation, or available capacity.

### `AGREEMENT`

Represents a legally or commercially meaningful arrangement such as an
electricity-supply agreement, connection agreement, works agreement, PPA,
CRESS/BESC arrangement, land agreement, JV agreement, transaction agreement,
or financing agreement.

Key attributes:

- agreement ID and type;
- linked project, site, parcel, or asset;
- parties and roles;
- signed, effective, expiry, and termination dates with precision;
- agreement status;
- linked capacity observations;
- source and evidence links.

An agreement does not inherit a project-level MW merely because both relate to
the same project. Agreement-attributed quantities require an evidence link that
supports agreement, identity, measure, value, qualifier, and scope.

### `CAPACITY_OBSERVATION`

Represents one source-stated or derived capacity value at a defined scope and
date. Long-form observations preserve changing disclosures without overwriting
history.

Required semantics include:

- observation ID;
- subject type and ID: project, phase, agreement, asset, or other approved
  subject;
- value and unit;
- measure type;
- qualifier;
- scope and phase;
- observation/effective date and precision;
- source and evidence classification.

Measure types include:

- `IT_CAPACITY`
- `ELECTRICAL_SUPPLY`
- `MAXIMUM_DEMAND`
- `CONTRACTED_CAPACITY`
- `CONNECTION_CAPACITY`
- `GENERATION_CAPACITY`

Units such as `MW`, `MWac`, `MWp`, `MVA`, and `MWh` remain distinct. Storage
power and energy require different observations. Different measure types are
not automatically additive or successive stages of one waterfall.

### `INTELLIGENCE_EVENT`

Represents one real-world occurrence that changes or evidences the state of an
entity or relationship.

Key attributes:

- canonical event ID;
- event type;
- subject project/site/asset/agreement/organization;
- event date and precision;
- status or result;
- linked organizations and roles;
- linked current historical record IDs;
- source and evidence links;
- analyst review state.

Event specializations initially include:

- project announcement;
- land or site commitment;
- planning application and decision;
- agreement signing or effectiveness;
- contractor award;
- construction commencement or progress;
- commissioning and energisation;
- operational milestone;
- transaction announcement, signing, or completion;
- financing commitment or close;
- policy issue or effective date;
- ownership or operator change.

Canonical-event identity is defined before loading existing events. Multiple
source documents may support one event. One source document may also support
several distinct events.

### `ENTITY_RELATIONSHIP`

Represents a dated link or role between entities.

Examples:

- organization develops project;
- organization operates project;
- organization owns project or parcel;
- organization contracts for asset or project scope;
- project occupies site;
- site contains parcel;
- project benefits from grid project;
- renewable project supplies load project;
- project is a phase of campus;
- organization is subsidiary of parent.

Key attributes:

- relationship ID and type;
- subject and object IDs/types;
- role and scope;
- verified ownership share if stated;
- valid-from/to dates and precision;
- source and evidence links.

An ownership or operator change closes or supersedes the earlier relationship;
it does not rewrite history.

### `SOURCE`

Represents one retrievable evidence object: filing, announcement, web page,
report, planning record, official dataset, API response, GIS feature, map
snapshot, or customer-provided document.

Key attributes:

- source ID;
- publisher and source family;
- title and official reference;
- URL or access location;
- publication/effective date and precision;
- retrieval timestamp;
- content hash and version;
- language and format;
- authority level;
- rights/reuse status;
- confidentiality class;
- local archive path where permitted;
- access and supersession status.

The existing `source_registry` table is reserved but empty. It should evolve
into this source model after rights and version fields are approved.

### `EVIDENCE_LINK`

Connects sources to accepted assertions. It permits multiple sources per fact,
different sources for different fields, and explicit conflict records.

It should not store long copyrighted extracts as a substitute for the source.
Where useful and permitted, it may retain a short supporting span, page, table,
or section reference.

## Conceptual specializations

The following concepts do not initially require separate physical tables:

- **Power agreement:** `AGREEMENT` subtype linked to typed capacity and Power
  Pathway milestone.
- **Renewable procurement:** `AGREEMENT` subtype linking load, renewable
  project, utility/network parties, and contracted quantity.
- **Grid project:** `PROJECT` subtype linked to `INFRASTRUCTURE_ASSET` records
  and beneficiaries.
- **Generation project:** `PROJECT` subtype linked to generation assets and
  generation-capacity observations.
- **Contractor:** `ORGANIZATION` in a time- and scope-bounded role.
- **Transaction:** one or more `INTELLIGENCE_EVENT` records plus an agreement
  where continuing contractual terms matter.
- **Financing:** agreement plus commitment, closing, drawdown, or maturity
  events.
- **Planning application:** persistent official reference plus submission,
  meeting, decision, amendment, and expiry events.
- **Construction event:** event with exact project/asset and physical scope;
  planned or ceremonial dates do not become physical commencement.
- **Operational milestone:** event linked to exact project phase or asset.

If repeated real records require specialized attributes or lifecycle controls,
a later design may promote one of these concepts to a physical table. The first
implementation should not pre-empt that evidence.

## Entity resolution and duplicate handling

Resolution order should be deterministic where possible:

1. official registration number, ticker, title, planning reference, source
   feature ID, or OSM primitive ID;
2. exact legal name plus jurisdiction;
3. project vehicle and parent relationship;
4. project/campus name plus site identity;
5. land-title and planning relationships;
6. analyst-reviewed alias or fuzzy match.

Every proposed merge must retain:

- source IDs and original names;
- merge decision and date;
- analyst or deterministic rule;
- surviving canonical ID;
- ability to reverse the merge.

Possible duplicates remain unresolved rather than silently merged. Splits are
required where one public name actually describes multiple campuses, phases,
or legal projects.

## Current and historical state

Entity masters may expose a current-status snapshot for convenience, but dated
events and relationships remain authoritative for chronology. Historical
analysis reconstructs state from records available at the information cutoff.

The following must not be backfilled into historical features without dated
support:

- later ownership or operator;
- later project name or phase capacity;
- later project geometry;
- later agreement quantity;
- later planning approval;
- current OSM asset;
- project-enabled line, cable, substation, or generation asset;
- later operating status.

## Source versioning

Automated retrieval should retain:

- query and external record ID;
- URL;
- publication and retrieval dates;
- content hash;
- previous hash;
- retrieval status;
- extraction version;
- supersession or correction relationship.

An unchanged source does not create another fact. A revised document becomes a
new source version and triggers review of affected evidence links. Links that
break should not delete previously retained provenance.

## Machine and LLM extraction boundary

Raw documents and API responses belong in ignored raw storage. Extracted text,
tables, and candidate facts belong in ignored staging. A machine or LLM output
does not become a verified record until deterministic validation and the
required analyst review are complete.

Material human review is mandatory for identity, MW semantics, agreement
attribution, project status, site commitment, geometry, ownership, construction,
energisation, project-enabled infrastructure, transaction meaning, and negative
or non-occurrence conclusions. No generic AI confidence score is used.

## Confidentiality and data rights

Every source should have a confidentiality and reuse class, distinguishing:

- public evidence suitable for citation;
- public evidence whose redistribution rights require review;
- licensed data;
- customer-permissioned confidential evidence;
- internal relationship or professional notes;
- legally or contractually restricted information.

Technical access to a web page, filing attachment, GIS service, or API does not
automatically grant commercial redistribution rights. Customer outputs must
include only evidence permitted for that use. Personal professional research
must not automatically flow into commercial products, and commercial
origination interests must not change evidence classification.

## Proposed storage boundaries

### Curated and committed

- normalized accepted entities and facts;
- source metadata and evidence links;
- small source-backed geometry records;
- explicit manual review decisions.

### Raw and ignored

- downloaded documents;
- API responses;
- OSM extracts and caches;
- licensed raw datasets;
- source snapshots where retention is permitted.

### Processed and ignored

- extracted text and tables;
- candidate entities and events;
- LLM candidate output;
- temporary entity matches;
- derived analytics, features, and reports.

### DuckDB

- loaded curated entities, events, relationships, capacities, agreements, and
  source metadata;
- deterministic views over existing historical records;
- analytical views and coverage reports.

Geometries may remain in GeoJSON or GeoParquet with metadata and stable IDs in
DuckDB. A graph database, distributed platform, and autonomous orchestration
are not required.

## Implementation sequence

1. Define canonical event identity and crosswalk rules.
2. Implement the smallest Intelligence Core schema.
3. Map the existing eight projects without changing source facts or current
   table counts.
4. Validate event deduplication, capacity semantics, roles, source links, and
   chronology.
5. Add a breadth-first Johor project universe.
6. Add source adapters only after the target normalized records are stable.
7. Build transparent analytics before UI, scores, or prediction.

The model succeeds only if one accepted fact has one canonical identity and a
traceable source path across every PowerStack application.
