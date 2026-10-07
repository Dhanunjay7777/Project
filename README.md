# Claude AI Engineer: Evaluation and Observability — Capstone Project

**Course:** Claude AI Engineer (`cd15552`)  
**Project:** Evaluation and Observability Capstone Evidence Pack  

---

## Overview

This repository contains the completed **Evaluation and Observability Capstone Project** evidence pack and full Python implementation packages for all three mission-critical systems:

1. **System 1: Validated, Routed Insurance Policy Extraction Pipeline (`01-policy-pipeline/`)**
   - Resilient retry loop distinguishing recoverable schema/format failures from unrecoverable `missing_source` escalation.
   - SLA-driven batch submission frequency calculation.
   - Independent within-policy integration reviewer pass.
   - Deterministic Human-in-the-Loop (HITL) routing with calibration slicing and stratified sampling.
   - Includes production on-call runbook (`ON_CALL_RUNBOOK.md`) and extended calibration slice analysis (`extended_calibration_slice.py`).

2. **System 2: Schema-Enforced Two-Pass Mortgage Extraction System (`02-mortgage-extraction/`)**
   - Two-pass classify-then-extract pipeline with forced Anthropic `tool_choice`.
   - Strict JSON Schema with nullable unions and enum-plus-`other` spillover.
   - Deterministic cross-field mathematical consistency validation.

3. **System 3: Resilient Multi-Source Supply Chain Risk Investigator (`03-supply-chain/`)**
   - Canonical `Claim` model across four diverse source readers (audit, logistics, news, quality database).
   - Provenance-preserving conflict annotation (never silently arbitrates contradictory evidence).
   - Resilient coordinator with timeout fallback paths for dark/unreachable data sources.

---

## Repository Structure

```
├── README.md                      # Project documentation and reproduction guide
├── reflection-brief.md            # Completed capstone reflection brief with quantitative citations
├── perturbation-log.md            # Completed perturbation experiments across all 3 systems
├── environment.txt                # System runtime specification (Python 3.12, Windows 11)
│
├── 01-policy-pipeline/
│   ├── policy_extractor/          # Python source code package
│   ├── tests/                     # Pytest test suite (45 passing tests)
│   ├── pyproject.toml             # Package configuration & dependencies
│   ├── tests.txt                  # Full pytest output
│   ├── static-checks.txt          # mypy & ruff verification output
│   ├── pipeline-run.txt           # CLI execution output (policy-extractor pipeline)
│   ├── routing_decisions.json     # Generated routing decisions artifact
│   ├── calibration-report.txt     # Sliced calibration & Brier score report
│   ├── extended-calibration-report.txt # High-granularity slice report
│   ├── extended_calibration_slice.py  # Calibration slicing script
│   ├── ON_CALL_RUNBOOK.md         # Production on-call operations runbook
│   └── screenshots/               # Visual proof of successful pipeline execution
│
├── 02-mortgage-extraction/
│   ├── mortgage_extractor/        # Python source code package
│   ├── tests/                     # Pytest test suite (25 passing tests)
│   ├── pyproject.toml             # Package configuration & dependencies
│   ├── tests.txt                  # Full pytest output
│   ├── static-checks.txt          # mypy & ruff verification output
│   ├── extract-run.txt            # Successful document extraction capture
│   ├── discrepancy-run.txt        # Mathematical consistency validator discrepancy capture
│   └── screenshots/               # Visual proof of extraction execution
│
└── 03-supply-chain/
    ├── supply_chain_risk/         # Python source code package
    ├── tests/                     # Pytest test suite (23 passing tests)
    ├── pyproject.toml             # Package configuration & dependencies
    ├── tests.txt                  # Full pytest output
    ├── static-checks.txt          # mypy & ruff verification output
    ├── investigation-run.txt      # Multi-source synthesis briefing output
    ├── briefing.md                # Generated multi-source briefing artifact
    ├── timeout-run.txt            # Graceful degradation with simulated source timeout
    └── screenshots/               # Visual proof of investigation run
```

---

## Verifying and Running Tests

Each system can be verified using `pytest` within its respective directory.

### 1. Insurance Policy Pipeline
```bash
cd 01-policy-pipeline
pytest -v tests/
```

### 2. Mortgage Extraction
```bash
cd 02-mortgage-extraction
pytest -v tests/
```

### 3. Supply Chain Investigation
```bash
cd 03-supply-chain
pytest -v tests/
```

---

## Key Artifacts & Citations

All values and metrics quoted in [`reflection-brief.md`](reflection-brief.md) are directly verifiable in the respective output captures:
- **System 1 Test Count:** 45 passed, 3 skipped (`01-policy-pipeline/tests.txt`)
- **System 1 Routing Output:** 4 auto-approve, 1 human-review, 4 spot-check, 1 escalation (`01-policy-pipeline/routing_decisions.json`)
- **System 2 Test Count:** 25 passed (`02-mortgage-extraction/tests.txt`)
- **System 3 Test Count:** 23 passed (`03-supply-chain/tests.txt`)
