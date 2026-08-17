# Historical Endpoint Labels

`build_historical_endpoint_labels.py` derives endpoint labels from the local
DuckDB. The CSV is research output, not manual evidence:

```powershell
python src/build_historical_endpoint_labels.py --evaluation-date 2026-08-14
```

Output: `data/processed/research/historical_endpoint_labels.csv`.

## Label states

- `OBSERVED_POSITIVE`: a qualifying `VERIFIED` outcome is confidently within
  the horizon.
- `OBSERVED_NEGATIVE`: the horizon elapsed and explicit evidence establishes
  that the qualifying outcome did not occur within it.
- `RIGHT_CENSORED`: no positive is observed and the complete horizon has not
  elapsed.
- `UNLABELABLE`: the endpoint, timing, electrical threshold, or evidence of
  non-occurrence is insufficient.

Missing evidence is never converted to a negative label.

## Model formulations

The implemented 100 MW endpoint is a fixed-threshold formulation:

```text
FIXED_THRESHOLD_MODEL:
P(
  qualifying electrical agreement >=100 MW within 48 months
  |
  historically observable site/grid/planning/project features at T
)
```

The 100 MW threshold belongs to the dependent variable. A project does not need
to have disclosed an electrical target at `T`. A verified later agreement and
its typed electrical quantity may determine the outcome label, but neither may
be used as a prediction-time feature.

The qualifying quantity must be asserted on the qualifying agreement milestone
itself. A `power_pathways.target_power_mw` or `ultimate_power_mw` value cannot
fill a missing agreement quantity, even when both records concern the same
project. Later commissioning, energisation, maximum demand, portfolio capacity,
and IT capacity also cannot fill that gap.

A different formulation may be implemented in the future:

```text
PROJECT_SPECIFIC_TARGET_MODEL:
P(
  required MW secured within required timeframe
  |
  requested/required MW known at T
  + historically observable features
)
```

That future model would require `electrical_target_known`. It is not currently
implemented.

## Historical Training Methodology v1 cohort

The first strict cohort asks:

> Once a specific site had been committed, how credible was securing a
> project-specific >=100 MW power agreement within 48 months?

Time zero is the earliest verifiable binding commitment to the identified site.
The strict core is:

```text
POST_SITE_COMMITMENT
+ PRE_QUALIFYING_OR_EQUIVALENT_POWER_COMMITMENT
```

An executed conditional SPA, binding site-specific acquisition agreement,
executed project lease, or exercised option may establish site commitment. A
non-binding memorandum, negotiation, generic locality announcement, or
unexercised option does not. If an earlier binding commitment is known, a later
completion, replacement agreement, or convenient announcement cannot replace
it as time zero.

The observation is excluded when a qualifying or functionally equivalent
binding project-specific power commitment of at least 100 MW was effective at
or before time zero. Verified project-specific commissioning or energisation of
at least 100 MW at or before time zero also excludes the observation because
the outcome has already progressed beyond the endpoint.

### Functionally equivalent power commitment

An arrangement is endpoint-equivalent only when all of the following are
established:

- it is attributed to the exact project/site;
- it was legally effective or binding at or before time zero;
- it was backed by the utility, electricity supplier, or connection provider;
- it created an enforceable electrical supply or connection obligation;
- it explicitly covered at least 100 MW using `ELECTRICAL_SUPPLY`,
  `MAXIMUM_DEMAND`, `CONTRACTED_CAPACITY`, or `CONNECTION_CAPACITY` with a
  qualifying lower-bound meaning.

Examples that may qualify when all conditions are evidenced include an executed
connection agreement, accepted binding connection offer, executed utility
supply agreement, or works agreement that legally commits the provider to the
specified supply or connection. A system-impact study, feasibility approval,
non-binding reservation, contractor construction contract, tender, design,
notice to proceed, or physical trench does not by itself establish an
endpoint-equivalent commitment.

### Prediction-time project states

`PRE_CONSTRUCTION` and `PRE_PROJECT_GRID_WORKS` are no longer universal hard
inclusion gates. They are replaced conceptually by prediction-time evidence
states:

```text
construction_state_at_cutoff:
  NOT_STARTED_VERIFIED
  STARTED_VERIFIED
  NOT_FOUND

project_grid_works_state_at_cutoff:
  NOT_STARTED_VERIFIED
  STARTED_VERIFIED
  NOT_FOUND
```

These values are research states and have not been added to the database
schema. `NOT_FOUND` means the state was not established; it does not mean work
had not started.

Construction before the cutoff triggers a boundary-quality and latent-selection
review because physical commitment may reflect non-public confidence in power.
It does not automatically mean the power-agreement endpoint already occurred.
Due diligence, surveys, clearing, grading, enabling works, piling, foundations,
and permanent building works should be distinguished where evidence permits.

Project-specific grid work before the cutoff triggers stricter
endpoint-equivalence review. Studies, applications, design, tendering,
procurement, contractor award, notice to proceed, mobilisation, physical works,
energisation, and handover are different states. Pre-boundary work excludes the
case only when the evidence establishes that a qualifying or functionally
equivalent binding >=100 MW commitment already existed, or that >=100 MW was
already commissioned or energised.

Source silence is not evidence of absence. A package-level commencement date
establishes chronology only for that package, and unresolved alternative
contractors or scopes leave the relevant whole-project state `NOT_FOUND`.
Later retrospective evidence may verify historical chronology, but later
project facts remain inadmissible as prediction-time features.

`PRE_SITE_COMMITMENT` and `PRE_LAND_ACQUISITION` answer an earlier site-selection
question and are reserved for separate cohorts. Evidence from the current
post-site-commitment cohort does not validate those earlier decision contexts.

The current label generator does not store the two project-state variables or
automate the functionally equivalent commitment review. Its generated
`training_eligibility` checks label, boundary, point-location, and historical
spatial-output fields only. Until code is updated in a later implementation
step, strict cohort eligibility requires a documented methodology review in
addition to generated output. Documentation and generated logic are therefore
not yet fully aligned; Step 57 changes no code.

## Endpoint mappings

| Endpoint | Horizon | Qualifying verified records |
|---|---:|---|
| `ESA_WITHIN_12M` | 12 months | `ESA / SIGNED`; `ELECTRICITY_SUPPLY_AGREEMENT / AGREED` or `SIGNED` |
| `ESA_WITHIN_24M` | 24 months | Same ESA mapping |
| `UTILITY_COMMISSIONING_WITHIN_24M` | 24 months | `UTILITY_SUPPLY_COMMISSIONING / COMMISSIONED` |
| `FIRST_PHASE_OPERATION_WITHIN_24M` | 24 months | `PHASE_ONE_OPERATION / OPERATING`; project-level `PHASE_ONE_DELIVERY / DELIVERED` |
| `POWER_AGREEMENT_100MW_WITHIN_48M` | 48 months | A mapped ESA/electricity-supply agreement whose same source-backed milestone explicitly carries a typed, project-specific electrical measure meeting the threshold |

Equivalent `connection_events` terminology is used only when no semantic
milestone exists. `POWER_PARTNERSHIP` is not automatically an ESA. Substation
energisation is not automatically utility-supply commissioning. Groundbreaking,
topping-out, land acquisition, and IT handover alone do not qualify.

## Agreement-stage 100 MW rule

Only `ELECTRICAL_SUPPLY`, `MAXIMUM_DEMAND`, `CONTRACTED_CAPACITY`, or
`CONNECTION_CAPACITY` may establish the threshold. Automated positives require
`EXACT` or `GREATER_THAN` evidence at or above 100 MW. IT capacity and untyped
`connection_events.supply_mw` are excluded. BESC/CRESS alone is not currently a
qualifying power-agreement state.

The agreement milestone must connect the specific project/pathway, executed
agreement type and status, agreement date, permitted measure, quantity,
qualifier, `VERIFIED` evidence, and source. Separate pathway-level MW is useful
context but never substitutes for missing agreement-attributed MW.

`APPROXIMATE`, `LESS_THAN`, and an upper bound such as "up to 150 MW" do not
prove a lower bound of at least 100 MW. Separate agreements are not summed
unless primary evidence explicitly states their combined qualifying electrical
commitment to the same project.

`POWER_AGREEMENT_100MW_WITHIN_48M` is an agreement-stage outcome. It must not be
described as proof that at least 100 MW was commissioned, energised, or
delivered. Separate physical-delivery endpoints require evidence definitions
that have not yet been established.

## Outcome and feature information

Supervised historical analysis keeps two time domains separate:

- **Outcome information** may occur after `T` and may be used only to derive the
  label.
- **Feature information** must have been valid or observable at `T`. Later
  agreement quantities, disclosures, and project-enabled infrastructure must
  not enter the feature set.

For Digital Halo, the prediction boundary is 11 June 2024, when PID and Digital
Halo executed the conditional Initial SPA for the exact title. The 12 July Deed
of Revocation and concurrent substitute SPA with wholly owned Nanda Digital did
not reset time zero. The verified 150 MW agreement occurred in August 2025 and
establishes the observed outcome; it is not a June 2024 predictive feature.

The curated Digital Halo polygon satisfies the Tier A geometry requirement.
Under the approved core cohort, its `NOT_FOUND` construction and
project-specific grid-work states are prediction-time metadata and review
states rather than automatic blockers. Digital Halo may proceed to historical
spatial extraction after the required boundary and endpoint-equivalence review;
no extraction has yet been run.

The current label generator reads point/proxy eligibility from
`dc_project_locations`; it does not load the separate manual GeoJSON. Its derived
`location_usable` field therefore remains false until polygon integration is
implemented. That implementation status does not change the evidence review:
`GEO-JHR-006-001` is the curated Tier A project geometry, while historical
spatial features remain unavailable because polygon integration and extraction
have not been implemented.

## Date precision and negatives

`prediction_date` is time zero. `MONTH` and `YEAR` values remain intervals; the
script never supplies an assumed day. For prediction interval `T=[T_L,T_U]` and
agreement interval `A=[A_L,A_U]`, a positive requires both:

```text
A_L > T_U
A_U <= T_L + 48 calendar months
```

Outcomes that overlap time zero or straddle a horizon are `UNLABELABLE` unless
the incomplete observation horizon instead requires `RIGHT_CENSORED`.
Same-month or same-day prediction/agreement records with unresolved ordering
are not positive.

The repository has no general structured evidence-review-complete field.
Therefore an elapsed horizon with no milestone remains `UNLABELABLE`. A verified
statement that a first phase *commenced operations* after the horizon can support
`OBSERVED_NEGATIVE`, because it explicitly dates the first-operation transition.

### Research-state mapping

The Step 47 research states remain methodological rather than database
vocabulary:

| Research state | Endpoint output | Meaning |
|---|---|---|
| `VERIFIED_POSITIVE` | `OBSERVED_POSITIVE` | The agreement record itself satisfies identity, attribution, quantity and timing rules. |
| `DERIVED_POSITIVE` | `UNLABELABLE` or `RIGHT_CENSORED` | Separate verified facts imply an outcome, but do not satisfy strict attribution. |
| `MATURE_NEGATIVE` | `OBSERVED_NEGATIVE` | The horizon and an authoritative non-occurrence review are complete. |
| `CENSORED` | `RIGHT_CENSORED` | No verified positive is observed and the complete horizon has not elapsed. |
| `NOT_FOUND` | `UNLABELABLE` | Evidence, timing, attribution or review completeness is unresolved. |

`MATURE_NEGATIVE` requires more than source silence. The review must cover the
utility, regulator/government, developer/issuer and relevant planning or
contractor sources across all project names, legal vehicles, owners and phases.
It also requires explicit non-occurrence, an authoritative first-agreement date
after the horizon, a demonstrably complete utility/regulator register, or a
verified terminal project outcome with no preceding qualifying agreement. A
completed horizon plus an unsuccessful search remains `UNLABELABLE`.

## Endpoint-specific training eligibility

The output separately records usable prediction boundaries, site geometry,
historical spatial output, prediction-time electrical targets, and label
usability. `TRAINING_READY_FOR_ENDPOINT` requires a usable observed label plus
site-quality geometry and historical spatial features. For the fixed-threshold
100 MW endpoint, `electrical_target_known` remains useful metadata but is not an
eligibility requirement. Observed labels without usable site geometry and
historical spatial features are `CALIBRATION_ONLY`; censored and unlabelable
rows are `NOT_READY`.
