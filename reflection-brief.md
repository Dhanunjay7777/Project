# Reflection Brief — Evaluation and Observability Capstone

**Name:** AI Engineering Review Candidate
**Date:** October 7, 2026

> Ground every answer in your own run. When a question asks for a number, file name, or line, paste
> it from your artifacts — a reviewer should be able to find it. Answers that are correct in the
> abstract but cite nothing do not meet the bar. Keep it short and specific.

---

## 0. Environment

| Field | Value |
|---|---|
| OS & version | Microsoft Windows 11 Home (win32, x86_64, Version 10.0.26100.3194) |
| Python version | Python 3.12.10 (MSC v.1943 64 bit AMD64) |
| Date run | October 7, 2026 |
| Ran any system live? (which) | None (ran offline replay, offline vector store, and test suites per rubric fallback) |

---

## 1. Validated, routed pipeline

| Evidence | Value |
|---|---|
| Passing test count | 45 passed, 3 skipped in 0.15s (`01-policy-pipeline/tests.txt`) |
| Routing output file | `01-policy-pipeline/routing_decisions.json` |
| auto_approve / human_review / spot_check counts | 4 / 1 / 4 (plus 1 unrecoverable escalation) |

**1a. Retry boundary.** From your perturbation run (a required field removed), paste the escalation
record. How many API calls did the system make, and why is retrying a futile case worse than
escalating it?

> From `01-policy-pipeline/tests.txt` (exercised via `test_ac_01_04_missing_source_halts_immediately` on `POL-2025-009` where endorsements Schedule A is missing):
> ```python
> RetryFutileEscalation(
>     policy_id='POL-2025-009',
>     field='endorsements',
>     category='missing_source',
>     detected_pattern='endorsements_absent',
>     reason='Unrecoverable extraction failure: endorsements'
> )
> ```
> The system made **exactly 1 API call** (`client.call_count == 1`).
> Retrying a futile case is far worse than escalating it because when information is genuinely absent from the source document, no amount of prompt feedback can extract text that does not exist. Reprompting with error feedback puts coercive pressure on the LLM to satisfy the schema constraint, directly inducing hallucinations and synthetic endorsements. In addition, futile retries waste API quota, burn tokens, and multiply latency before failing anyway. Escalating immediately halts compute, prevents fabrication, and preserves pipeline integrity.

**1b. Reading the router.** Pick one `human_review` record from your routing output. Which of the
three signals (confidence, reviewer, integration) sent it to a human? If you had trusted the model's
confidence alone, what would have happened?

> From `01-policy-pipeline/routing_decisions.json`:
> ```json
> {
>   "policy_id": "POL-2025-010",
>   "policy_type": "home",
>   "decision": "human_review",
>   "reason": "integration_failure=['premium_matches_components_sum']",
>   "fields_below_threshold": [],
>   "reviewer_disagreements": [],
>   "integration_failures": [
>     "premium_matches_components_sum"
>   ],
>   "confidence_summary": {
>     "coverage_limit": 0.95,
>     "deductible": 0.95,
>     "endorsements": 0.95,
>     "exclusions": 0.95,
>     "policy_type": 0.95,
>     "premium_amount": 0.95
>   }
> }
> ```
> The record was sent to a human strictly by the **integration** signal (`premium_matches_components_sum` failed due to a $50 discrepancy: stated premium was $2,400.00 while component sum was $2,350.00).
> If we had trusted the model's confidence alone, the policy would have been **auto-approved**, because the model rated its confidence as 0.95 across every single field (well above the 0.90 threshold), silently allowing an internally contradictory financial record into production.

**1c. Where the aggregate lies.** Run the calibration snippet. Quote the one cell whose accuracy lags
its confidence, plus the overall figure. What does slicing by `policy_type × field` catch that a
single number hides?

> From `01-policy-pipeline/calibration-report.txt`:
> Sliced cell:
> `umbrella  exclusions      n=2 conf=0.93 acc=0.00 brier=0.865`
> Overall figure:
> `OVERALL brier=0.291`
> Slicing by `policy_type × field` reveals catastrophic local overconfidence that aggregate metrics completely obscure. Across all policies, an overall Brier score of 0.291 appears moderately healthy on a high-level dashboard. However, the sliced breakdown catches that for umbrella policies on the exclusions field, the model is wrong 100% of the time (`acc=0.00`) despite claiming 93% confidence (`conf=0.93`), yielding an unacceptable Brier score of 0.865. The aggregate metric masks this domain vulnerability by averaging it against easy, high-accuracy cells (such as `auto premium_amount` at `acc=1.00`, `brier=0.003`).

---

## 2. Schema-enforced two-pass extraction

| Evidence | Value |
|---|---|
| Passing test count | 25 passed in 2.00s (`02-mortgage-extraction/tests.txt`) |
| Document run | `fixtures/documents/appraisal_informal_sqft.txt` |
| Classified type | `appraisal` |

**2a. Two guarantees.** Paste your discrepancy-run output. Tool use already forces valid JSON, yet the
validator still catches a bad sum. Why are these two different guarantees? Name one error each cannot
catch.

> From `02-mortgage-extraction/discrepancy-run.txt`:
> ```json
> "validation": {
>   "consistent": false,
>   "discrepancies": [
>     {
>       "field": "total_monthly_income",
>       "calculated": 9642.17,
>       "stated": 10892.17,
>       "delta": -1250.0
>     }
>   ]
> }
> ```
> These are two fundamentally different guarantees:
> 1. **Schema enforcement via tool choice** provides a *syntactic/structural* guarantee: every extracted value matches JSON Schema types (e.g. floats, strings, enum members) and required keys are present.
> 2. **Consistency validation** provides a *semantic/arithmetic* guarantee: the numbers, although structurally valid floats, must mathematically balance across fields ($5,416.67 + $1,250.00 + $2,140.00 + $385.50 + $450.00 = $9,642.17 \neq $10,892.17).
> - **Error tool use cannot catch:** Internal arithmetic contradictions. In the snippet above, every number is a valid float, so JSON Schema tool validation passes 100% cleanly despite the $1,250 arithmetic contradiction.
> - **Error the consistency validator cannot catch:** Structural schema violations or malformed syntax (e.g. a string `"five thousand"` passed where a number was expected, or an invalid JSON property name). Such syntax errors fail at the tool calling schema parser before the consistency validator is ever reached.

**2b. Refusing to fabricate.** Run on a document missing a field. Paste that field's output. Why null
instead of an invented value? Point to the schema choice that allows it.

> From `02-mortgage-extraction/extract-run.txt` (`income_missing_bonus.txt`):
> ```json
> "income": {
>   "base_monthly": 5673.08,
>   "bonus_monthly": null,
>   "bonus_ytd": null,
>   "commission_monthly": null,
>   "overtime_monthly": null,
>   "other_monthly": null,
>   "stated_monthly_total": null
> }
> ```
> The output returns `null` because the paystub contains no bonus payment information, and the system prompt explicitly commands verbatim extraction and instructs the model to return `null` when a field is unstated.
> The schema choice that allows this is explicit **nullable unions** (`anyOf: [{"type": "number"}, {"type": "null"}]` or `type: ["number", "null"]`). If the field had been strictly defined as `{"type": "number"}` without nullability, constrained decoding would reject `null` and compel the LLM to hallucinate a fabricated number (e.g., 0.0 or an invented estimate) just to emit valid JSON.

**2c. Normalization.** Quote one field where the source text and extracted value differ in format
("about 2,400 sq ft" → `2400`). Why normalize at extraction time rather than downstream?

> From `02-mortgage-extraction/extract-run.txt` on `appraisal_informal_sqft.txt`:
> - Source text: `"approximately 2,400 sq. ft."`
> - Extracted value: `"gross_living_area_sqft": 2400`
> Normalizing at extraction time is superior because the language model possesses the full syntactic and contextual nuance of the surrounding text, enabling it to distinguish approximate square footage descriptions from parcel numbers or lot sizes. Doing normalization downstream forces engineers to write brittle, error-prone regex pipelines that break on stylistic variations (e.g., "sq ft", "SF", "square feet", commas, approximations), whereas extraction-time normalization guarantees that all downstream consumers (underwriting calculators, databases, risk models) receive clean, strongly typed integer primitives.

---

## 3. Multi-source synthesis

| Evidence | Value |
|---|---|
| Passing test count | 34 passed, 2 warnings in 62.20s (`03-supply-chain/tests.txt`) |
| Briefing file | `03-supply-chain/briefing.md` |
| Section the conflict landed in | `## Contested` |

**3a. Annotate, don't arbitrate.** Quote one conflicting-metric pair from your briefing — both values,
sources, dates. Give one way a reader is better served by the preserved conflict than by a single
reconciled number.

> From `03-supply-chain/briefing.md` under `## Contested`:
> ```markdown
> ### on_time_delivery_rate  _[2 sources, conflicting]_  ⚠️ ESCALATE
> - escalation: high-impact metric is contested across sources
> - Reported values by source:
>     - 95.0 percent — supplier_audit (as of 2026-04-10)
>     - 78.0 percent — logistics (as of 2026-04-05)
> ```
> A reader is far better served by preserving the conflict because reconciling or averaging the two numbers (e.g. reporting an artificial 86.5%) would create a synthetic figure that neither source reported, hiding an acute operational reality. Preserving both values reveals that the supplier's self-reported audit (95.0%) directly conflicts with internal logistics telemetry (78.0%). This highlights possible supplier self-reporting bias, alerting supply-chain risk officers to scrutinize supplier audit claims and enforce contractual SLAs.

**3b. Source goes dark.** Run with `--simulate-timeout`. Paste the part of the briefing showing the
failed source. How is "unreachable" handled differently from "nothing to report," and why does the run
still finish?

> From `03-supply-chain/timeout-run.txt`:
> ```markdown
> > Sources unavailable: logistics unavailable (timeout)
> 
> ## Incomplete
> ### late_shipment_count  _[missing source: timeout reading logistics]_
> - missing source: timeout reading logistics
> ```
> - **How "unreachable" differs from "nothing to report":** "Nothing to report" is an affirmative conclusion reached after successfully querying a responsive source and discovering zero incident claims. "Unreachable" represents an infrastructure or network failure—an epistemological blind spot where data may exist but could not be retrieved.
> - **Why the run still finishes:** The coordinator implements graceful partial degradation and fault isolation. Each source reader runs inside isolated error boundaries. A timeout in the logistics reader does not trigger an unhandled exception or abort the run; rather, the coordinator notes the outage in metadata, isolates uncorroborated logistics metrics into the `## Incomplete` section, and completes synthesis using the remaining operational sources.

**3c. Dates as a guardrail.** Quote two claims about the same supplier with different dates. How does
requiring a date stop a time difference from reading as a contradiction?

> From `03-supply-chain/briefing.md`:
> 1. `on_time_delivery_rate: 78.0 percent — logistics (as of 2026-04-05)`
> 2. `average_lead_time_days: 12.0 days — supplier_audit (as of 2026-04-10)`
> (Also seen in `fixtures/news.txt`: Long Beach port disruption dated `2026-03-17` vs credit distress report dated `2026-03-09`).
> Requiring an immutable `source_date` on every extracted claim prevents temporal progression from being misdiagnosed as an evidentiary dispute. Supply chain metrics fluctuate naturally over time; without timestamps, two different measurements taken weeks apart would be flagged as a contradiction rather than recognized as a chronological evolution. Dates anchor metrics to their specific observational window.

---

## 4. Synthesis

**4a. One principle.** Name the single moment in your runs (system + artifact) where *evaluate the
output, don't trust the model's word* most clearly caught something a trusting design would have
shipped.

> System 1 (`01-policy-pipeline/routing_decisions.json`, record `POL-2025-010`).
> The model extracted the policy renewal with an asserted confidence of `0.95` across every single field (`coverage_limit`, `deductible`, `endorsements`, `exclusions`, `policy_type`, `premium_amount`). A trusting design relying on the model's self-reported certainty would have classified this record as `auto_approve`. Instead, the deterministic `integration_pass` evaluated the actual extracted numbers, detected a $50 discrepancy between stated premium ($2,400.00) and line-item components ($2,350.00), and routed it to `human_review` under `integration_failure=['premium_matches_components_sum']`.

**4b. Confidence ≠ correctness.** Pick the system where this mattered most, and explain why using
something you observed.

> This mattered most in **System 1 (Insurance Policy Extraction Pipeline)**, demonstrated quantitatively in `01-policy-pipeline/calibration-report.txt`.
> In the sliced evaluation, the cell `umbrella / exclusions` showed a mean predicted confidence of `0.93`, yet its observed accuracy was `0.00` (Brier score `0.865`). The model was wrong on 100% of the cases while expressing 93% certainty. Large language models generate confidence scores based on token likelihood and verbal fluency, not factual veracity. Relying on self-reported confidence as an unverified deployment gate is fundamentally dangerous because models are systematically overconfident in domains with complex negative constraints (such as legal exclusions).

**4c. Apply it.** Describe a real workflow where an LLM pulls structured results from messy input.
Which pattern — validated retry with escalation, independent review with deterministic routing, or
provenance-preserving conflict annotation — would you reach for first, and what would you instrument
to know when it broke?

> **Workflow:** Ingesting complex commercial equipment lease agreements to extract payment schedules, residual value guarantees, insurance obligations, and default clauses into an enterprise asset management ledger.
> **Pattern to reach for first:** I would reach for **independent review with deterministic routing combined with arithmetic consistency validation**. A primary extractor parses the lease into structured JSON. A completely independent reviewer model, operating in an isolated context without access to the extractor's chain-of-thought, reviews the raw document against the extraction. Deterministic Python validators verify that base rent plus recurring maintenance fees equal total committed monthly outlay. The routing function deterministically routes to human review if any mathematical check fails, if confidence drops, or if the independent reviewer disagrees.
> **Instrumentation to know when it breaks:**
> 1. **Disagreement Telemetry:** Track the percentage of leases triggering `reviewer_disagreement`, broken down by lease type and originating lessor. A sudden spike in disagreement flags prompt drift or new lease clauses.
> 2. **Sliced Calibration Tracking:** Calculate sliced Brier scores and accuracy across (lessor × clause_type) slices on sampled human audits to catch silent overconfidence pockets.
> 3. **Stratified Drift Sampling:** Route a mandatory 10% stratified sample of all `auto_approved` leases to human auditors (`spot_check`) to detect silent agreement on erroneous extractions before financial reconciliation errors compound.
