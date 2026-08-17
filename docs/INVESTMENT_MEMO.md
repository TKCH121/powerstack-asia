# PowerStack Investment Memo

**Status:** Authoritative internal investment and gating assessment

**Baseline date:** 17 August 2026

**Recommendation:** **Conditional go for a capped validation programme**

## Executive recommendation

PowerStack merits further limited investment because it has developed a
coherent evidence methodology, a differentiated Power Pathway model, working
Johor geospatial pipelines, and a plausible decision-support use. It does not
yet merit a broad software, data-platform, proprietary-data, or machine-learning
investment.

The recommended next allocation is a small, staged validation programme:

1. make the approved product and methodology durable;
2. implement a minimal normalized Intelligence Core using only existing
   evidence;
3. build a breadth-first Johor project dataset;
4. demonstrate transparent market analyses;
5. complete one prospective analyst-led Power Pathway Assessment;
6. test it with independent experts and prospective customers.

Each stage must earn the next. Sunk engineering effort is sunk cost and is not
evidence of customer demand, product-market fit, commercial differentiation,
or defensibility.

### No-go for now

Do not invest now in:

- machine learning;
- statistical scoring or a Power Pathway Score;
- a broad SaaS build;
- major cloud or data-platform engineering;
- autonomous AI research;
- expensive proprietary datasets without a demonstrated customer use;
- full Southeast Asia expansion;
- an API product;
- a polished customer UI before the workflow is proven.

## Investment thesis

Power-intensive digital infrastructure is difficult to assess because site,
land, utility, grid, generation, planning, renewable-procurement, contractor,
and capital evidence is fragmented and time-dependent. Material concepts such
as IT capacity, maximum demand, contracted capacity, electrical supply,
connection capacity, and generation capacity are commonly mixed. Present-day
infrastructure can also create historical look-ahead leakage when it was built
for the project later being assessed.

The thesis is that an evidence-first system can create decision value by:

- reducing the time required to assemble and reconcile fragmented evidence;
- making source, date, scope, and uncertainty explicit;
- distinguishing existing infrastructure from project-enabled works;
- translating evidence into a physical and commercial Power Pathway;
- identifying the unresolved facts that matter to land, investment,
  development, and utility decisions;
- accumulating longitudinal project, infrastructure, and outcome evidence that
  becomes more valuable through repeated professional use.

The potential product is not a public-data substitute for TNB or engineering
diligence. Its value must come from better framing, faster evidence assembly,
more reliable chronology, and more actionable follow-up before and alongside
those formal processes.

## Problem and current alternatives

Potential users currently rely on combinations of:

- in-house site-selection and development teams;
- utility engagement;
- electrical and grid consultants;
- planning and title advisers;
- brokers and landowners;
- market-intelligence providers;
- regulatory filings and company announcements;
- GIS and public maps;
- spreadsheets and undocumented expert judgement.

These alternatives are not necessarily deficient. Sophisticated developers and
hyperscalers may already possess better private information than PowerStack can
obtain. Utilities and engineering advisers remain necessary. PowerStack must
therefore prove that integrating these domains into a dated, auditable pathway
record changes a decision or saves meaningful work. A product that merely
repackages public announcements will not support attractive economics.

## Product

PowerStack is an evidence-first Power & Digital Infrastructure Intelligence
system. It uses one shared evidence and intelligence spine for:

- **Site Diligence:** a deep assessment of a named site, required electrical
  quantity, and required date;
- **Origination Intelligence:** evidence-backed identification and follow-up of
  potentially relevant sites, projects, companies, infrastructure, and
  transactions;
- **Market Intelligence:** longitudinal tracking of project pipelines, capacity
  disclosures, grid and generation development, renewable procurement,
  contractors, planning, land, and capital;
- **Historical Calibration:** leakage-controlled testing of pathway logic,
  timing, and later outcomes.

The central analytical object is the Power Pathway. The immediate commercial
v1 is an analyst-led Power Pathway Assessment supported by software and evidence
infrastructure. [PRODUCT_MEMO.md](PRODUCT_MEMO.md) is the product authority.

## Target customers

### Infrastructure and private-equity investors

Potential decision: whether the power-pathway evidence and unresolved risks are
sufficiently understood to proceed with an investment, acquisition, or
condition precedent.

Potential willingness to pay is relatively high because the decisions are
material. The limitation is that investors will still require formal technical
and legal advisers. PowerStack must supplement those advisers rather than
claiming to replace them.

### Development sponsors and industrial landowners

Potential decision: what a specific parcel would require before it can support
a credible data-centre or power-intensive infrastructure proposition.

The economic value can be meaningful if PowerStack identifies a required
pathway, fatal evidence gap, transaction condition, or project-enabled
infrastructure need. There is also a risk that a landowner wants marketing
support rather than an independent evidence assessment.

### Data-centre developers

Potential decision: how to prioritize site, utility, infrastructure, and
delivery work before or after a site commitment.

The pain is high, but internal expertise is also strongest. Sales friction and
trust requirements are therefore substantial. PowerStack must demonstrate
better coordination, chronology, or market coverage—not generic education.

### Lenders, hyperscalers, utilities, and consultants

These may become later users, partners, reviewers, or channels. Their evidence,
security, procurement, liability, and technical standards make them less
suitable as the first wedge.

Customer ranking remains a hypothesis. The repository contains no completed
customer-discovery programme, paid pilot, retention evidence, or independently
verified willingness to pay.

## Business model

### Initial form

The most credible initial revenue is:

- a fixed-fee Power Pathway Assessment; or
- a research/advisory retainer that includes assessments, market monitoring,
  and an origination watchlist.

This form keeps analysts responsible for judgement while the software improves
consistency and research efficiency.

### Origination

Origination intelligence may lead to advisory fees, development support,
transaction opportunities, participation, or co-investment. Those outcomes are
not assumed. Transaction-linked compensation also creates independence,
conflict, confidentiality, and potentially regulated-activity questions that
must be addressed before use.

### Scalable future forms

A market-intelligence subscription is the most plausible recurring product if
PowerStack can prove broad coverage, meaningful updates, source rights, and
repeat usage. Data/API access is later still because it requires stable entity
resolution, data contracts, rights, service levels, and customers who value the
data independently of analyst interpretation.

SaaS is not the default business model. The service must first become
repeatable, and the repeated elements must be measured before they are
automated.

## Evidence and assets built so far

### Evidence methodology

The repository preserves `VERIFIED`, `DERIVED`, `INFERRED`, and `NOT_FOUND`,
date precision, information cutoffs, typed power values, and separate
infrastructure timing. It does not use missing data as zero or current topology
as utility capacity.

### Johor geospatial base

The current pipeline produces:

- 4,103 canonical industrial planning geometries;
- 526 mapped HV line/cable features;
- 63 cleaned Johor HV substations;
- current-state line and substation proximity features.

These are useful screening and topology assets. They do not establish site
availability, legal development rights, physical commissioning, or spare
capacity.

### Historical and pathway evidence

The curated historical dataset contains eight projects, 26 connection events,
six grid-asset events, eight pathways, five pathway components, and 24
milestones. Digital Halo has a curated authoritative project polygon. TM Nxera
has a bounded parcel whose area discrepancy prevents classification as the
exact project/title polygon.

The current 100 MW agreement endpoint has two verified observed positives—TM
Nxera and Digital Halo—and no mature negative. Both positives remain
calibration cases under current generated output because historical spatial and
methodology implementation are incomplete. PDG JH1 has the only hardened
historical OSM extraction.

### Software

The local stack is simple and appropriate: Python, Pandas, GeoPandas, DuckDB,
Streamlit, Osmium, and public sources. It includes validation scripts and
conservative endpoint logic. The application itself is only a research viewer,
not a commercial workflow.

Completed engineering demonstrates technical learning and some feasibility. It
does not prove customer demand.

## Current moat

There is no strong current commercial moat.

The strongest current assets are:

- the evidence and timing discipline;
- the normalized Power Pathway semantics;
- source-resolution knowledge across Johor projects;
- leakage-aware historical methods;
- project-enabled infrastructure representation;
- a working current and historical geospatial prototype.

These create a head start and reduce repeated research effort, but they rely
substantially on public sources and open-source tools. A capable team could
reproduce the basic maps, distances, schemas, and documents.

## Potential future moat

Defensibility could arise from a compounding evidence-to-outcome system:

- longitudinal project and asset histories;
- normalized land, planning, company, contractor, and agreement relationships;
- customer-permissioned evidence unavailable in public sources;
- verified later outcomes and update history;
- a record of project-enabled grid and generation delivery;
- a trusted analyst and expert-review method;
- repeatable source-to-assessment workflow;
- integration into investment and development decisions;
- proprietary feedback about which findings changed real decisions.

The moat would be accumulated evidence, workflow trust, and outcome feedback,
not an algorithm alone.

The following are not moats by themselves:

- OSM proximity;
- public planning polygons;
- Python or Streamlit;
- the three-table schema;
- generic AI summarization;
- an arbitrary score;
- a small-sample ML model;
- a list of public URLs.

## Technical and data risks

### Unavailable capacity

PowerStack cannot infer utility headroom or connection availability from public
topology. If customers value only that answer, the product may have little
standalone value.

### Evidence timing and completeness

Material evidence may be disclosed after the relevant decision. Public sources
may identify an outcome but not what was knowable ex ante. Source silence
cannot establish a negative.

### Historical sample

The current sample is small, selected, and contextually heterogeneous. It lacks
a mature negative for the 100 MW agreement endpoint. A statistical model would
be unreliable and could disguise evidence gaps.

### Geometry and planning access

Exact project geometry, cadastral lineage, planning cases, and effective dates
can be difficult or expensive to acquire. Public GIS services may be incomplete,
unstable, or unclear about commercial reuse.

### Entity resolution

Project vehicles, parents, operators, owners, campus names, phases, and renamed
projects can be confused. Incorrect resolution would corrupt capacity totals,
developer-conversion analysis, and project timelines.

### Source rights and confidentiality

Public access does not necessarily permit commercial redistribution. Customer
and relationship evidence also requires explicit confidentiality boundaries.

### Consulting intensity

If every assessment requires bespoke research and specialist judgement, the
business may remain a consultancy with limited software leverage.

### Geography-specific scaling

Johor knowledge does not automatically transfer to Singapore, Indonesia,
Thailand, or Vietnam. Each geography has different utility, planning,
cadastral, disclosure, and regulatory systems.

## Commercial risks

- Customers may already solve the problem internally.
- Utilities and established engineering advisers may have stronger trust and
  private information.
- Users may not pay for an answer that excludes spare capacity.
- Origination candidates may not convert into mandates or transactions.
- Subscription users may not perceive enough recurring change.
- A broad intelligence product may become an expensive news and data-cleaning
  exercise.
- Independence may be questioned if PowerStack both assesses and promotes the
  same opportunity.
- The agreement endpoint may be less commercially relevant than physical
  energisation or operation.
- Historical comparison may add little beyond transparent expert judgement.

## Bear case

In the bear case, PowerStack assembles public information competently but cannot
answer the decisive capacity question. Every material conclusion still requires
TNB and engineering work. Project geometry and planning records remain manual,
negative outcomes cannot be established, the historical sample cannot support
prediction, and customers already use internal teams or advisers. The workflow
therefore remains labour-intensive, customers will not pay recurring fees, and
the data does not compound because later outcomes and private evidence are not
shared.

Under that outcome, PowerStack may still be valuable as the user's professional
intelligence system. It would not justify a standalone software company or
large capital allocation.

## Falsification tests

The commercial thesis is weakened or falsified if:

- target users consistently say that only utility-certified capacity changes
  their decision;
- a complete assessment identifies no material question, dependency, or risk
  that users did not already know;
- independent experts find the pathway representation incomplete or
  misleading;
- users treat the report only as free marketing support;
- several assessments remain almost entirely bespoke;
- authoritative geometry cannot be acquired at tolerable time and cost;
- public evidence appears too late for the intended decision context;
- customers will not share later outcomes;
- source rights prevent useful commercial outputs;
- no credible negatives or consistent historical contexts can be developed;
- the workflow does not materially reduce analyst effort after repetition.

## Cheapest next experiments

### 1. Intelligence Core unit test

Implement the minimal normalized intelligence spine and map only the existing
eight projects. Test canonical event identity, evidence links, organization
roles, phases, and capacity semantics before new breadth research.

### 2. Breadth dataset test

Attempt a source-limited 30–50 project Johor master. Measure duplicate risk,
core-field coverage, source rights, and analyst time rather than filling every
field.

### 3. One complete prospective assessment

Prepare a customer-style assessment for one named site with a typed requirement
and date. Record which conclusions depend on unavailable utility evidence and
which still create decision value.

### 4. Expert review

Ask an independent grid/electrical specialist to identify evidence-category,
pathway, and claim-boundary errors.

### 5. Customer discovery

Show the complete deliverable to five to eight relevant users. Ask what decision
it changes, what they currently pay for, what is missing, and whether they would
pay for this output or an ongoing retainer.

### 6. Repeatability measurement

Track analyst time by source retrieval, extraction, entity resolution,
geospatial analysis, pathway reasoning, review, and reporting across successive
assessments.

## Staged allocation

### Stage A — Documentation and core model

Allocate only enough time to establish one authoritative product definition and
test the normalized intelligence model against existing facts.

**Go:** facts map without duplication or semantic loss.

**Pivot:** simplify the model if it requires parallel sources of truth.

**Stop:** do not build breadth ingestion if provenance cannot remain clear.

### Stage B — Johor breadth and analytics

Allocate a fixed research period to build a project master and produce
transparent non-ML analyses.

**Go:** at least three analyses provide decision-relevant cross-project insight.

**Pivot:** narrow to advisory if authoritative breadth is materially smaller or
rights are restrictive.

**Stop:** do not build a subscription interface if the dataset is primarily
`NOT_FOUND` or restates press releases.

### Stage C — Assessment and user validation

Allocate time to one complete prospective assessment and structured expert and
customer review.

**Go:** a user identifies a decision changed and credible paid interest exists.

**Pivot:** retain PowerStack as an internal professional-intelligence system if
it creates personal value but not commercial demand.

**Stop:** end standalone product investment if users require only unavailable
capacity evidence.

### Stage D — Productization

Automate only repeated, measured workflow steps. Consider a subscription only
after recurring update value is observed. Consider statistical calibration only
after a consistent cohort, admissible historical features, observed positives,
and credible mature negatives exist.

## Final investment decision

The current decision is **conditional go**, not commitment to a software
company and not endorsement of a predictive model.

PowerStack has earned a disciplined validation programme because its evidence
method and Power Pathway structure address a real analytical problem and can
support the user's professional intelligence work. It has not earned broad
engineering, proprietary-data spending, or ML investment. The next capital and
time allocation should maximize learning about customer usefulness,
repeatability, source feasibility, and decision impact.
