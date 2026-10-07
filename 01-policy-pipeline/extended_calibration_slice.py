"""Extended calibration slice adding document complexity and carrier dimension.

Extends the standard policy_type x field breakdown with a multi-dimensional slice
(policy_type x carrier_tier x field) to demonstrate how aggregate numbers hide
carrier-specific extraction vulnerabilities.
"""
from dataclasses import dataclass
from collections import defaultdict
from typing import Sequence

@dataclass(frozen=True)
class MultiDimCalibrationLabel:
    policy_id: str
    policy_type: str
    carrier_tier: str       # 'tier1_standard' vs 'specialty_surplus'
    field: str
    predicted_confidence: float
    correct: bool

@dataclass
class SlicedCell:
    slice_key: str
    samples: int
    mean_confidence: float
    accuracy: float
    brier_score: float

labels = [
    # Tier 1 standard policies: high accuracy, well calibrated
    MultiDimCalibrationLabel("POL-1", "auto", "tier1_standard", "premium_amount", 0.95, True),
    MultiDimCalibrationLabel("POL-2", "auto", "tier1_standard", "premium_amount", 0.95, True),
    MultiDimCalibrationLabel("POL-3", "auto", "tier1_standard", "deductible", 0.92, True),
    MultiDimCalibrationLabel("POL-4", "home", "tier1_standard", "dwelling_limit", 0.94, True),
    MultiDimCalibrationLabel("POL-5", "home", "tier1_standard", "dwelling_limit", 0.94, True),
    
    # Specialty / Surplus lines: model reports high confidence due to fluent phrasing,
    # but fails to parse non-standard manuscript endorsements/exclusions
    MultiDimCalibrationLabel("POL-6", "umbrella", "specialty_surplus", "exclusions", 0.93, False),
    MultiDimCalibrationLabel("POL-7", "umbrella", "specialty_surplus", "exclusions", 0.93, False),
    MultiDimCalibrationLabel("POL-8", "commercial", "specialty_surplus", "endorsements", 0.91, False),
    MultiDimCalibrationLabel("POL-9", "commercial", "specialty_surplus", "endorsements", 0.91, False),
]

def run_multidim_calibration(labels: Sequence[MultiDimCalibrationLabel]):
    by_slice = defaultdict(list)
    for l in labels:
        key = f"{l.policy_type:10} | {l.carrier_tier:17} | {l.field:15}"
        by_slice[key].append(l)

    print("=" * 80)
    print("EXTENDED MULTI-DIMENSIONAL CALIBRATION REPORT (POLICY_TYPE x TIER x FIELD)")
    print("=" * 80)
    print(f"{'Slice Key (Type | Tier | Field)':48} | {'N':3} | {'Conf':5} | {'Acc':5} | {'Brier':6}")
    print("-" * 80)
    
    total_brier = 0.0
    for key, items in sorted(by_slice.items()):
        n = len(items)
        conf = sum(i.predicted_confidence for i in items) / n
        acc = sum(1 for i in items if i.correct) / n
        brier = sum((i.predicted_confidence - (1.0 if i.correct else 0.0)) ** 2 for i in items) / n
        total_brier += sum((i.predicted_confidence - (1.0 if i.correct else 0.0)) ** 2 for i in items)
        print(f"{key:48} | {n:3} | {conf:5.2f} | {acc:5.2f} | {brier:6.3f}")
        
    overall_brier = total_brier / len(labels)
    overall_acc = sum(1 for i in labels if i.correct) / len(labels)
    overall_conf = sum(i.predicted_confidence for i in labels) / len(labels)
    print("-" * 80)
    print(f"{'OVERALL AGGREGATE':48} | {len(labels):3} | {overall_conf:5.2f} | {overall_acc:5.2f} | {overall_brier:6.3f}")
    print("=" * 80)
    print("\nInsight: The aggregate Brier score of 0.380 and aggregate accuracy of 56% hide that")
    print("tier1_standard operates at 100% accuracy (brier=0.005), whereas specialty_surplus")
    print("suffers 0% accuracy (brier=0.846) despite 92% reported confidence!")

if __name__ == "__main__":
    run_multidim_calibration(labels)
