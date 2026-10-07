# 2:00 AM On-Call Runbook — Insurance Policy Extraction & Routing Pipeline

**Service:** `policy-extractor` (Renewal Ingestion & HITL Router)  
**Audience:** Primary On-Call AI Engineer  
**Severity Level:** P2 (Queue backpressure / routing anomaly) / P1 (Data corruption / silent approval leak)

---

### 1. What a Healthy Run Looks Like
A normal production batch of renewal documents shows:
- **Routing Ratio:** ~60–80% `auto_approve`, ~15–30% `human_review`, and exactly 10% `spot_check` (drift-detection stratum).
- **Escalation Count:** Low single digits (< 3%), strictly matching known document mutilations (`category="missing_source"`).
- **Validation Retries:** Format and consistency retries succeed on attempt 2 (< 15% retry rate).
- **Calibration Health:** Overall Brier score $\le 0.15$; no individual `(policy_type, field)` cell above $0.35$.

---

### 2. The Golden Rule: Which Signal Lies?
> **NEVER TRUST THE EXTRACTOR'S SELF-REPORTED CONFIDENCE (`confidence_summary`). IT LIES.**

- **The Trap:** When an LLM encounters complex legal phrasing (e.g. umbrella exclusions or custom endorsements), it frequently outputs `confidence: 0.95` simply because the generated text is grammatically fluent and matches schema types.
- **The Reality:** Our calibration reports prove that `umbrella / exclusions` operates at **0% observed accuracy** despite the model asserting **93% confidence** (Brier score 0.865).
- **On-Call Action:** If a teammate or product manager suggests lowering routing thresholds or relying on confidence alone to drain a backed-up human review queue, **refuse immediately**. It will leak corrupted policy renewals directly into binding financial contracts.

---

### 3. Step-by-Step 2 A.M. Triage Tree

#### Step 1: Check `routing_decisions.json` Reason Distribution
Run this command on the latest batch output:
```bash
jq -r '.[] | .decision + ": " + .reason' routing_decisions.json | sort | uniq -c
```
- **If `fields_below_threshold` is spiking:** Inspect upstream OCR quality. Low confidence across all fields indicates blurry scans, corrupted PDFs, or missing pages.
- **If `reviewer_disagreement` is spiking:** Compare the model versions. Ensure extractor is on Haiku and reviewer is on Sonnet. Check whether an upstream model release shifted extraction formatting.
- **If `integration_failure` is spiking:** Inspect the specific checks. If `premium_matches_components_sum` is failing, check if the carrier changed how taxes, surcharges, or discounts are itemized on page 2.

#### Step 2: Check for Unrecoverable Escalation Loops
Inspect the run log for `RetryFutileEscalation`:
```bash
grep "RetryFutileEscalation" /var/log/policy-extractor/*.log
```
- If you see documents looping 3 times before failing on missing fields, the validator's pattern classifier is failing to tag `category="missing_source"`. Ensure the document parser is correctly flagging null required fields so they halt on attempt 1 instead of burning tokens and stalling pipeline throughput.

#### Step 3: Check Drift on the `spot_check` Sample
Review the latest 20 `spot_check` audits returned by human underwriters:
- If humans are rejecting more than 2% of `spot_check` items, **the automated gate is leaking**. 
- Immediately decrease the confidence threshold from `0.90` to `0.95` or temporarily force 100% human review for that specific policy stratum until business hours.

---

### 4. Emergency Fallback Commands
- **Dry-run sample before running large batches:**
  `policy-extractor batch data/policies/ --dry-run-sample 5 --sample-threshold 0.8`
- **Force human review on a compromised stratum (e.g., umbrella):**
  Adjust threshold in config or run with `--spot-check-pct 1.0` for the affected policy type.
