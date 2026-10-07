# Perturbation Log

For each system, make one deliberate change to an input or configuration, predict the outcome, run
it, and record what actually happened. See the starters in the Instructions, or design your own (your
own experiment earns more credit).

---

### System 1 — validated, routed pipeline

- **Change I made (file + what I changed):**
  Perturbed document input by evaluating a policy renewal document where a mandatory field is missing from source: `data/policies/POL-2025-009.txt` references "Schedule A" for endorsement details, but Schedule A is completely unattached in the source text. In the pipeline/test (`tests/test_us01_retry.py::test_ac_01_04_missing_source_halts_immediately`), the extractor extracts `endorsements: None` with low confidence (0.2).
- **Command I ran:**
  `.\.venv\Scripts\pytest.exe tests/test_us01_retry.py -k test_ac_01_04_missing_source_halts_immediately -v`
- **What I predicted:**
  The validation logic will identify that `endorsements` is null on a required policy type and categorize it as `category="missing_source"` (`detected_pattern="endorsements_absent"`). Rather than wasting API calls attempting futile retries, the system will immediately escalate by returning a `RetryFutileEscalation` record on the very first attempt (`call_count == 1`).
- **What actually happened (paste the key output line):**
  `tests/test_us01_retry.py::test_ac_01_04_missing_source_halts_immediately PASSED [100%]`
  Emitted escalation record:
  `RetryFutileEscalation(policy_id='POL-2025-009', field='endorsements', category='missing_source', detected_pattern='endorsements_absent', reason='Unrecoverable extraction failure: endorsements')`
  Asserted API calls: `assert client.call_count == 1`
- **How this differs from the unperturbed run:**
  On unperturbed clean documents (such as `POL-2025-001` through `POL-2025-008`), the system extracts complete fields and proceeds cleanly to routing (`auto_approve` or `spot_check`). On recoverable failures (such as negative premiums or arithmetic mismatches tested in `test_ac_01_03`), the system re-prompts the model up to 3 times with validation feedback. On unrecoverable `missing_source`, it immediately halts without retrying.

---

### System 2 — schema-enforced two-pass extraction

- **Change I made (file + what I changed):**
  In `fixtures/documents/income_sum_mismatch.txt`, modified the borrower's stated total monthly income on the paystub to `$10,892.17`, which diverges by $1,250.00 from the sum of the extracted earnings components: base ($5,416.67) + bonus ($1,250.00) + commission ($2,140.00) + overtime ($385.50) + other ($450.00) = $9,642.17.
- **Command I ran:**
  `.\.venv\Scripts\mortgage-extract.exe fixtures/documents/income_sum_mismatch.txt --mode replay`
- **What I predicted:**
  The initial JSON Schema tool call validation will succeed because all individual line items and the stated total are valid floats matching the schema contract. However, the subsequent cross-field mathematical consistency check (`validate_consistency`) will sum the line items, compare against stated total, detect the $1,250.00 gap, and flag `consistent: false`.
- **What actually happened (paste the key output line):**
  `"validation": { "consistent": false, "discrepancies": [ { "field": "total_monthly_income", "calculated": 9642.17, "stated": 10892.17, "delta": -1250.0 } ] }`
  (Command exited with returncode 1).
- **How this differs from the unperturbed run:**
  On an unperturbed consistent document such as `fixtures/documents/appraisal_informal_sqft.txt`, the consistency validator confirms matching values:
  `"validation": { "consistent": true, "discrepancies": [] }` and exits with returncode 0.

---

### System 3 — multi-source synthesis

- **Change I made (file + what I changed):**
  Simulated an external source outage during coordinator execution by passing `--simulate-timeout` to force the `logistics` source reader to time out.
- **Command I ran:**
  `.\.venv\Scripts\supply-chain-investigate.exe meridian --offline --simulate-timeout`
- **What I predicted:**
  The coordinator will not crash or abandon the investigation. It will catch the timeout, record the degraded source state in briefing metadata, divert claims that depend solely on logistics into the `## Incomplete` section, and successfully render the briefing from the remaining 3 operational sources (`supplier_audit`, `internal_quality`, `industry_news`).
- **What actually happened (paste the key output line):**
  `> Sources unavailable: logistics unavailable (timeout)`
  `## Incomplete`
  `### late_shipment_count  _[missing source: timeout reading logistics]_`
  `- missing source: timeout reading logistics`
  (Command completed with exit code 0).
- **How this differs from the unperturbed run:**
  In the unperturbed run (`supply-chain-investigate meridian --offline`), all 4 sources are queried successfully:
  1. `late_shipment_count` is confirmed under `## Well-Established` (`11.0 shipments — logistics`).
  2. `on_time_delivery_rate` is placed under `## Contested` with ⚠️ ESCALATE due to conflicting claims between `supplier_audit` (95.0%) and `logistics` (78.0%).
  Under timeout perturbation, the conflict disappears because the second source is absent, so `on_time_delivery_rate` falls back to `## Well-Established` (95.0% from audit), while `late_shipment_count` moves to `## Incomplete`.
