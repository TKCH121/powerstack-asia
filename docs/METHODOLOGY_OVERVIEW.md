# PowerStack Methodology Overview

**Status:** Authoritative conceptual methodology

**Baseline date:** 17 August 2026

This document is the concise entry point to PowerStack methodology. It explains
the governing concepts and links to the implementation authorities. It does not
duplicate field definitions, endpoint code, or historical OSM mechanics.

## Purpose

PowerStack converts fragmented public and permissioned evidence into a
time-aware account of a power-intensive infrastructure project and its Power
Pathway. Its methodology is designed to prevent three common errors:

1. treating unknown information as false or zero;
2. treating current mapped topology as available grid capacity;
3. using later agreements, infrastructure, or disclosures as if they had been
   known at an earlier decision date.

The methodology supports Site Diligence, Origination Intelligence, Market
Intelligence, and Historical Calibration over one evidence spine. It does not
turn all four into the same decision question.

## Decision Contract

A formal assessment begins with a Decision Contract. It defines:

- the exact project, site, campus, or phase;
- the geometry accepted for the analysis;
- the required power value, measure type, qualifier, and scope;
- the required agreement, commissioning, energisation, or operating date;
- the decision context;
- the prediction or event boundary;
- the latest information the assessment may use;
- the outcome or decision being evaluated.

The principal decision contexts are:

- `PRE_SITE_COMMITMENT`: a site is being screened or considered but has not
  been committed;
- `POST_SITE_COMMITMENT / PRE_POWER_COMMITMENT`: a site is committed but no
  qualifying or functionally equivalent binding power commitment exists;
- `POST_AGREEMENT / PRE_ENERGISATION`: an agreement exists and the principal
  question is delivery.

Evidence or calibration from one context does not validate another context.

## Evidence types

### `VERIFIED`

A source directly supports the asserted fact. Verification applies only to what
the source actually says. A verified announcement that an ESA was signed does
not verify an unstated MW quantity or physical delivery.

### `DERIVED`

A result is reproducibly calculated from verified inputs. Examples include
geometry area, a distance to a mapped line, elapsed time, or an endpoint label
produced by documented rules.

### `INFERRED`

The record is an explicit interpretation that is not directly stated by a
source. It must retain its reasoning and must not be presented as verified.

### `NOT_FOUND`

The fact was not established within the defined evidence review. It is not
false, zero, not required, or evidence that an event did not happen.

`NOT_REQUIRED_VERIFIED` is used only where a source explicitly verifies that a
Power Pathway component or requirement is unnecessary. It is not a general
evidence type.

## Infrastructure timing states

Evidence strength and infrastructure timing are separate dimensions.

### `CURRENT_STATE`

The feature is present in the current source snapshot. Its historical timing,
physical status, commissioning, and capacity are not established merely by its
current presence.

### `PRE_EXISTING_VERIFIED`

Independent dated evidence establishes that the infrastructure existed by the
assessment cutoff.

### `PROJECT_ENABLED`

The infrastructure was or is being developed as part of the project's Power
Pathway. It may be a legitimate route to future power, but it cannot be treated
as a pre-decision predictor.

### `POST_DECISION`

The infrastructure is observed after the decision boundary without evidence
that it already existed at that boundary.

### `NOT_FOUND`

Existence or timing has not been established.

Public-map lifecycle tags are retained as map evidence. They do not by
themselves prove physical construction or operation.

## Power and capacity semantics

PowerStack keeps the following measures distinct:

- `IT_CAPACITY`: computing-load design or deployed IT load;
- `ELECTRICAL_SUPPLY`: electricity supply explicitly stated by the source;
- `MAXIMUM_DEMAND`: stated maximum electrical demand;
- `CONTRACTED_CAPACITY`: capacity contractually attributed to an agreement;
- `CONNECTION_CAPACITY`: capacity attributed to a network connection;
- `GENERATION_CAPACITY`: capacity of a generating asset or project.

Every capacity observation should preserve:

- value;
- unit;
- measure type;
- qualifier such as `EXACT`, `APPROXIMATE`, `GREATER_THAN`, `LESS_THAN`, or
  `NOT_FOUND`;
- project, phase, agreement, or asset scope;
- source and date.

Different measures are not automatically additive. IT MW cannot satisfy an
electrical-supply endpoint. Generation MW is not the same as contracted load.
`MW`, `MWac`, `MWp`, `MVA`, and `MWh` must not be silently converted.

The implemented Power Pathway tables currently permit electrical supply,
maximum demand, contracted capacity, and connection capacity in pathway power
fields. `GENERATION_CAPACITY` belongs to the broader intelligence capacity model
and source-stated component units; it is not an implemented pathway power
measure type.

## Geometry hierarchy

PowerStack uses the strongest geometry the evidence supports:

1. `AUTHORITATIVE_PROJECT_POLYGON`: an authoritative project-linked polygon
   plus evidence that the represented land is the project site;
2. authoritative project point or exact `SITE_COORDINATE`;
3. `BOUNDED_PARCEL`: an official project-linked containing boundary whose
   completeness or area reconciliation remains unresolved;
4. exact lot or title identity without geometry;
5. park, campus-section, or locality proxy;
6. approximate locality;
7. `NOT_FOUND`.

A bounded parcel is not silently promoted to the project polygon. Its centroid
is not a project coordinate. An industrial-planning polygon is not necessarily
a cadastral parcel or available development site. Geometry sources, CRS, area,
effective-date status, title succession, and hashes must be preserved.

Tier A project geometry can support direct spatial features. Bounded or Tier B
geometry requires interval-aware features, such as minimum and maximum distance
over the admissible boundary, before it can support equivalent use. That method
is not yet implemented.

## Power Pathway structure

The Power Pathway model has three implemented tables:

- `power_pathways`: assessment envelope, prediction boundary, information
  cutoff, typed target/ultimate power, pathway type, and evidence;
- `power_pathway_components`: physical infrastructure, requirement state,
  infrastructure timing, capacity unit, delivery party, and completion evidence;
- `power_pathway_milestones`: dated agreements, studies, supply,
  commissioning, energisation, handover, planning, construction, or operating
  milestones.

The model permits existing infrastructure and infrastructure developed
concurrently with the data centre. It does not require artificial rows for
unknown components. Each independently asserted fact retains its own source and
evidence classification.

See [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for implemented fields and
controlled values.

## Prediction boundary and information cutoff

`prediction_date` is the decision or event boundary being assessed.
`information_cutoff_date` is the latest date of information permitted in the
assessment. They may coincide, but they are not conceptually interchangeable.

Outcome evidence may occur after the prediction boundary and may be used to
derive an outcome label. It must not enter prediction-time features.

For the current strict historical cohort, time zero is the earliest verifiable
binding commitment to the identified site. The observation must be
`POST_SITE_COMMITMENT` and
`PRE_QUALIFYING_OR_EQUIVALENT_POWER_COMMITMENT`.

Construction and project-specific grid-work states at the cutoff are recorded
as:

- `NOT_STARTED_VERIFIED`;
- `STARTED_VERIFIED`;
- `NOT_FOUND`.

They are prediction-time states and review triggers, not automatic universal
exclusions. A binding qualifying or functionally equivalent project-specific
power commitment of at least 100 MW at or before time zero excludes the
observation because the endpoint has already occurred. Verified commissioning
or energisation of at least 100 MW at or before time zero also excludes it.

The detailed test for equivalent commitments is defined in
[HISTORICAL_ENDPOINT_LABELS.md](HISTORICAL_ENDPOINT_LABELS.md).

## Historical agreement endpoint

The implemented fixed-threshold endpoint is:

`POWER_AGREEMENT_100MW_WITHIN_48M`

A positive requires a verified qualifying agreement milestone within the
horizon whose own evidence explicitly attributes at least 100 MW of an approved
electrical measure to the exact project. A separate project or pathway value,
IT capacity, portfolio total, or later commissioning quantity cannot fill an
unquantified agreement.

This endpoint records an agreement-stage outcome. It is not proof that 100 MW
was commissioned, energised, delivered, or used.

Missing agreement evidence is not a negative. A mature negative requires a
complete horizon and affirmative evidence that supports non-occurrence under
the detailed methodology.

## Leakage control

PowerStack prevents look-ahead leakage by:

- separating prediction time from outcome time;
- enforcing an information cutoff;
- excluding later agreement values from prediction features;
- distinguishing current, pre-existing, project-enabled, and post-decision
  infrastructure;
- preserving source dates and date precision;
- retaining month and year dates as intervals;
- preventing later owner, operator, capacity, geometry, or status disclosures
  from being backfilled into earlier features without dated support;
- treating OSM mapped-at-cutoff status as map evidence, not proof of physical
  operation.

The Yondr/Sedenak calibration remains the central warning: infrastructure that
now appears colocated with a project can have been developed as part of that
project's pathway and must not be used as if it were available beforehand.

## Prohibited inferences

PowerStack must not infer:

- spare or available grid capacity;
- utility willingness to connect;
- commissioning or operation from a standard OSM tag;
- power agreement MW from unrelated project capacity;
- electrical supply from IT capacity;
- whole-project construction chronology from one contractor package;
- verified absence from source silence;
- project geometry from a guessed map point or parent-parcel centroid;
- exact dates from month or year precision;
- feasibility or bankability from proximity alone;
- a probability, score, or ranking unsupported by calibrated evidence.

## Methodology flow

```text
Decision Contract
→ Evidence Engine
→ Shared Intelligence Spine
→ Power Pathway Reasoning
→ Site / Origination / Market application
→ Later observed outcomes
→ Historical Calibration
```

The Evidence Engine and Power Pathway reasoning must create value independently
of prediction. Historical Calibration tests and improves them; it does not
retroactively convert uncertainty into fact.

## Detailed authorities

- [PRODUCT_MEMO.md](PRODUCT_MEMO.md): product and application context
- [MARKET_INTELLIGENCE_MODEL.md](MARKET_INTELLIGENCE_MODEL.md): shared entity,
  event, source, and evidence design
- [PROJECT_SPEC.md](PROJECT_SPEC.md): current technical implementation scope
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md): implemented tables and vocabularies
- [HISTORICAL_ENDPOINT_LABELS.md](HISTORICAL_ENDPOINT_LABELS.md): endpoint,
  cohort, censoring, and training rules
- [HISTORICAL_OSM_PROTOTYPE.md](HISTORICAL_OSM_PROTOTYPE.md): historical OSM
  extraction and interpretation
- [SOURCE_REGISTER.md](SOURCE_REGISTER.md): current source inventory
- [CALIBRATION_NOTES.md](CALIBRATION_NOTES.md): historical findings and warnings
