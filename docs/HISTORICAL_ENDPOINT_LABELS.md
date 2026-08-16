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
The required state immediately after that commitment is:

- `POST_SITE_COMMITMENT`
- `PRE_ESA`
- `PRE_CONSTRUCTION`
- `PRE_PROJECT_GRID_WORKS`

An executed conditional SPA, binding site-specific acquisition agreement,
executed project lease, or exercised option may establish site commitment. A
non-binding memorandum, negotiation, generic locality announcement, or
unexercised option does not. If an earlier binding commitment is known, a later
completion, replacement agreement, or convenient announcement cannot replace
it as time zero.

Project-specific enabling or data-centre construction at or before the boundary
fails `PRE_CONSTRUCTION`. Physical work on a dedicated landing station, SSU,
PMU, line, cable, or project-triggered reinforcement fails
`PRE_PROJECT_GRID_WORKS`. Studies, applications, design, and tenders do not by
themselves establish physical start. Unresolved construction or grid-work
status prevents strict cohort inclusion.

A later source may establish `PRE_CONSTRUCTION` or
`PRE_PROJECT_GRID_WORKS` through positive chronology only when it identifies
the exact project/site, states an actual first physical commencement date later
than the prediction boundary, and is demonstrably complete for the entire
relevant construction or project-specific grid-work scope. Package-specific
contracts, contractor mobilisation, planned dates, approvals, tenders, designs,
notices to proceed, and ceremonial groundbreakings cannot close the
whole-project gate unless independent evidence establishes both scope
completeness and actual chronology.

Source silence is not evidence of absence. A package-level commencement date
proves chronology only for that package, and unresolved alternative contractors
or scopes leave the whole-project state `NOT_FOUND`. Later retrospective
evidence may verify historical chronology, but it does not make later project
facts admissible prediction-time features.

`PRE_SITE_COMMITMENT` and `PRE_LAND_ACQUISITION` answer an earlier site-selection
question and are reserved for a separate future cohort. The current label
generator does not automate these cohort tests; they require a documented case
review before `TRAINING_READY_FOR_ENDPOINT` can be assigned.

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

For Digital Halo, the prediction boundary is 12 July 2024 and the verified 150
MW agreement occurred in 2025. The 150 MW establishes a possible positive
outcome; it is not a July 2024 predictive feature.

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
