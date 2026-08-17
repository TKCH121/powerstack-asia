# PowerStack Product Memo

**Status:** Authoritative internal product definition

**Baseline date:** 17 August 2026

## Executive product position

PowerStack is an evidence-first Power & Digital Infrastructure Intelligence
system for Southeast Asia, beginning in Johor. It connects projects, sites,
land, power agreements, grid and generation infrastructure, planning,
renewable procurement, contractors, capital, and dated source evidence.

The central analytical object is the **Power Pathway**: the combination of
commercial commitments, physical infrastructure, approvals, delivery parties,
and milestones required to obtain a stated electrical quantity by a stated
date. PowerStack distinguishes infrastructure that is currently mapped,
independently verified as pre-existing, developed for the project, or observed
only after the decision being assessed.

PowerStack Intelligence supports four applications over one common evidence
and intelligence spine:

```text
POWERSTACK INTELLIGENCE
    |
    +-- Site Diligence
    +-- Origination Intelligence
    +-- Market Intelligence
    +-- Historical Calibration
```

The first commercial product is an **analyst-led Power Pathway Assessment**
supported by software and evidence infrastructure. It is not initially SaaS,
an automated site verdict, or a statistical probability product.

## The customer problem

Power-intensive digital infrastructure decisions require information that is
fragmented across utilities, regulators, planning authorities, land records,
company disclosures, contractor awards, renewable-procurement announcements,
maps, and technical documents. The important terms are also easy to conflate:

- IT capacity is not electrical supply.
- Maximum demand is not necessarily contracted or delivered power.
- An electricity-supply agreement does not by itself prove commissioning.
- A nearby line or substation does not establish spare capacity.
- Infrastructure visible today may not have existed at an earlier decision
  date and may have been built because of the project.
- A land parcel, planning polygon, industrial park, project campus, and
  individual data-centre phase are not interchangeable geometries.

Developers and investors ultimately require utility, engineering, legal,
planning, title, and commercial diligence. Before and alongside that work,
however, they need a coherent account of what is already evidenced, which
pathway is being asserted, which infrastructure must be delivered, who is
responsible, and what remains unknown. Conventional market directories and
simple proximity maps do not answer that question. Undocumented expert
judgement is also difficult to audit, update, or compare across sites.

PowerStack's job is to turn the available evidence into a time-aware,
source-linked decision record without presenting unavailable facts as known.

## Decision contexts

PowerStack must state the decision context before analysis. Evidence and
historical validation from one context cannot be presented as proof of
performance in another.

### Pre-site-commitment

The user is deciding whether to pursue, acquire, option, or prioritize a site.
The analysis may compare planning, land, topology, market activity, and
possible Power Pathways. The site may still be rejected or restructured.

This context has high potential value for origination and land diligence, but
the current historical cohort does not validate a pre-acquisition prediction
product. Any comparative or predictive claim for this context requires its own
historical decision boundaries and evidence standards.

### Post-site-commitment / pre-power-commitment

A specific site has been committed, but no qualifying or functionally
equivalent binding power commitment exists at the assessment boundary. The
commercial question is what must happen to obtain the required power and how
credible the documented pathway is.

This is the current historical calibration context for the 100 MW agreement
endpoint. Construction and project-grid-work states at the cutoff are recorded
and reviewed; they are not universal exclusions. A pre-existing qualifying or
equivalent binding power commitment is an exclusion because the endpoint has
already occurred at time zero.

### Post-agreement / pre-energisation

A power agreement exists, but delivery remains incomplete. The decision shifts
to infrastructure execution, commissioning, handover, programme dependencies,
and interim versus permanent supply. Agreement-stage historical evidence does
not validate an energisation or physical-delivery prediction.

## Product architecture

### Foundation — Decision Contract

Every formal site assessment defines:

- the exact project or site;
- admissible geometry and its evidence class;
- the required power value, measure type, qualifier, and scope;
- the required energisation or agreement date;
- the assessment context;
- the prediction or decision boundary;
- the information cutoff;
- the outcome or decision being assessed.

This prevents a later disclosure, a different phase, or a different MW meaning
from silently changing the question.

### Layer 1 — Evidence Engine

The Evidence Engine answers what is known, when it was knowable, and how it is
supported. It uses `VERIFIED`, `DERIVED`, `INFERRED`, and `NOT_FOUND`, while
keeping evidence strength separate from infrastructure timing.

Existing assets include source-backed manual records, current and historical
geospatial pipelines, date precision, typed power values, curated project
geometry, source URLs and dates, and regression validation. The evidence layer
also preserves positive unknowns: lack of a public agreement, geometry, or
commissioning record remains `NOT_FOUND`, not zero, false, or failure.

The future shared Intelligence Spine will normalize organizations, projects,
sites, parcels, infrastructure assets, agreements, capacity observations,
events, relationships, sources, and evidence links. It must reference and
crosswalk existing historical evidence rather than create a second unrelated
source of truth. [MARKET_INTELLIGENCE_MODEL.md](MARKET_INTELLIGENCE_MODEL.md)
is the design authority for that layer.

### Layer 2 — Power Pathway Reasoning

Power Pathway reasoning asks what must happen to obtain at least a specified
electrical quantity by a specified date. A pathway may involve:

- existing connection infrastructure;
- a consumer landing station or SSU;
- a new PMU or substation;
- new line or cable works;
- upstream reinforcement;
- right-of-way and planning approvals;
- interim followed by permanent supply;
- project-enabled generation or renewable procurement;
- utility studies, agreements, commissioning, energisation, and handover.

The approved three-table model separates the assessment envelope, physical
components, and dated milestones. It can represent alternative real-world
pathways without asserting that every project requires every component.

The current repository stores pathways; it does not yet automate pathway
construction, schedule reasoning, alternative comparison, or report
generation. Those activities remain analyst-led.

### Layer 3 — Historical Calibration

Historical Calibration reconstructs information available at a defensible
earlier boundary and observes later outcomes separately. The implemented
`POWER_AGREEMENT_100MW_WITHIN_48M` endpoint is an agreement-stage outcome. It
requires a verified qualifying agreement milestone that itself carries an
approved, project-specific electrical measure of at least 100 MW.

Historical Calibration may support interval analysis, case comparison,
development-velocity analysis, censored outcomes, and later statistical work.
It does not currently support a marketable probability claim. Machine learning
is optional future functionality and remains gated by consistent contexts,
geometry, historical features, positive outcomes, and credible mature
negatives.

## Commercial applications

### Site Diligence

Site Diligence starts with a named site and a typed power requirement. It
produces a decision-specific evidence and pathway assessment covering site
identity, planning and land context, mapped topology, pre-existing and
project-enabled infrastructure, power agreements, required components,
delivery parties, timing, and unresolved facts.

It supplements utility, engineering, planning, title, legal, and investment
diligence. It does not replace them.

### Origination Intelligence

Origination Intelligence starts with a geography, land universe, organization,
or observable signal stream. It identifies candidates that warrant follow-up
using explicit facts and derived features such as industrial zoning, parcel
area, topology distance, project and planning activity, project-enabled grid
works, renewable procurement, transactions, corporate activity, and contractor
awards.

An Origination Candidate is a research object, not a feasibility verdict. It
contains evidence, interpretations, unknowns, next actions, and a review date.
PowerStack does not combine these signals into an arbitrary score.

### Market Intelligence

Market Intelligence tracks the observable development system rather than only
individual data centres. It should support project pipeline, capacity
reconciliation, development velocity, developer conversion, grid development,
renewable-to-load relationships, contractor activity, land and planning
activity, transactions, financing, and geographic clustering.

The first breadth dataset is intended to cover approximately 30–50 material
Johor projects or campuses. It is breadth-first: it should not reproduce a full
historical reconstruction for every record. Capacities, phases, ownership, and
sources must nevertheless remain normalized and explicit.

## Current capabilities

The repository currently provides:

- 4,103 canonical industrial planning geometries after exact-geometry
  deduplication;
- 526 current mapped HV line/cable features and 63 cleaned Johor HV
  substations;
- current-state site proximity features with explicit `DERIVED` provenance;
- eight source-backed Johor data-centre projects;
- 26 connection events, six grid-asset events, eight Power Pathways, five
  pathway components, and 24 milestones;
- a curated authoritative project polygon for Digital Halo and a bounded
  parcel for TM Nxera;
- a hardened historical OSM extraction for PDG JH1;
- conservative historical endpoint generation and regression validation;
- two verified positive outcomes for the 100 MW agreement endpoint: TM Nxera
  and Digital Halo.

## Current limitations

These are functional research assets, not proof of product demand. The
structured DuckDB `source_registry` is not populated, the curated geometry is
not yet integrated into the historical feature builder, no mature negative
exists for the 100 MW agreement endpoint, and the current Streamlit application
is only a thin project/event viewer.

## PowerStack v1

The minimum commercially useful v1 is an **analyst-led Power Pathway
Assessment**. The customer buys a versioned decision report and supporting
evidence, while software improves analyst consistency and research efficiency.

### Inputs

- named site and admissible geometry;
- project/campus/phase scope;
- required electrical quantity and measure type;
- target date;
- decision context and information cutoff;
- current project stage;
- available utility, land, planning, engineering, and corporate documents;
- customer-provided evidence with explicit permission and confidentiality
  status.

### Workflow

1. Establish the Decision Contract.
2. Validate project, site, and geometry identity.
3. Normalize source evidence and dated project facts.
4. Build the current and, where relevant, historical topology context.
5. Separate independently pre-existing assets from project-enabled works.
6. Construct the candidate Power Pathway and alternatives.
7. Record components, milestones, delivery parties, and dependencies.
8. Identify unresolved evidence and required utility/engineering questions.
9. Review material assertions and prohibited inferences.
10. Deliver a versioned assessment with a validity date and update triggers.

### Deliverable

The assessment should contain:

- executive decision context;
- evidence-quality summary;
- site and topology maps;
- Power Pathway diagram;
- component and milestone register;
- current, pre-existing, project-enabled, and post-decision distinctions;
- schedule and dependency narrative;
- evidence-gap and risk register;
- utility, engineering, planning, title, and legal diligence questions;
- source appendix and change log.

Individual assertions may be described as supported, partially supported,
unresolved, or not found. They must not be collapsed into an overall score or
probability.

## Initial customers and commercial form

The most plausible initial users are infrastructure and private-equity
investors, development sponsors, industrial landowners, and data-centre
developers evaluating a named Johor site or project. Lenders, hyperscalers,
utilities, and engineering consultants have potential later uses but face
higher trust, procurement, liability, or substitution barriers.

Customer demand and willingness to pay have not yet been demonstrated. The
recommended initial commercial form is a paid assessment or research/advisory
retainer, supported by internal software. Origination mandates may later create
advisory, development, transaction, or investment opportunities, subject to
conflict management and relevant professional and regulatory requirements.

A market-intelligence subscription is the most plausible scalable recurring
product only after coverage, freshness, source rights, and repeated user value
are proven. A data/API business comes later. PowerStack should not assume SaaS
economics before it has a repeatable service and customers.

## Explicit non-claims

PowerStack v1 does not claim:

- available or spare grid capacity;
- a guaranteed utility agreement or connection;
- utility willingness to connect;
- engineering or power-flow feasibility;
- connection-cost certainty;
- physical commissioning, energisation, or delivery unless separately
  verified;
- bankability certification;
- a probability of success;
- a Power Pathway Score;
- that current mapped infrastructure existed at a historical cutoff;
- that an agreement-stage outcome proves delivery or operation;
- replacement of utility, engineering, legal, title, planning, surveying, or
  lender technical diligence.

## Roadmap

1. Lock the product, investment, methodology, and intelligence-model
   documentation.
2. Implement the normalized Intelligence Core and test it with the existing
   eight projects without duplicating historical facts.
3. Build the 30–50 project Johor breadth dataset with coverage reporting.
4. Produce transparent non-ML market analyses.
5. Complete one prospective Power Pathway Assessment.
6. Test it with independent experts and real prospective users.
7. Productize only the workflow that demonstrates repeated value.
8. Consider statistical calibration only after evidence-quality gates are met.

## Non-goals

PowerStack is not currently building:

- machine learning or statistical scores;
- autonomous project research;
- a generic news aggregator;
- a real-time utility network model;
- a graph database or large distributed data platform;
- an unattended customer SaaS product;
- a comprehensive ASEAN dataset before the Johor model is proven;
- private-capacity estimates from public topology;
- investment recommendations or automated origination rankings.

Further engineering is justified only by evidence that the resulting workflow
improves a real decision, reduces research effort, or supports a customer or
professional intelligence use that would otherwise be materially harder.
