#!/usr/bin/env python3
"""Run Centinel's forensic engine against the 64 real Honduras 2025 snapshots.

Ejecuta el motor forense de Centinel contra los 64 snapshots reales de Honduras 2025.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auditor.inconsistent_acts import InconsistentActsTracker


def parse_timestamp_from_filename(filename: str) -> datetime:
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{2})_(\d{2})_(\d{2})", filename)
    if not m:
        raise ValueError(f"Cannot parse timestamp from {filename}")
    date_str = m.group(1)
    h, mi, s = m.group(2), m.group(3), m.group(4)
    return datetime.fromisoformat(f"{date_str}T{h}:{mi}:{s}+00:00")


def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "hnd_2025"
    files = sorted(data_dir.glob("*.json"))
    print(f"Found {len(files)} snapshots in {data_dir}\n")

    tracker = InconsistentActsTracker(
        config_path=Path("/tmp/forensic_hnd_key.json"),  # nosec B108
        runtime_config_path=Path("/tmp/forensic_hnd_config.json"),  # nosec B108
        blackout_gap_minutes=30,
        max_resolution_rate=10.0,
        bulk_resolution_threshold=200,
        stagnation_cycles_threshold=4,
        prolonged_stagnation_cycles=8,
    )

    for f in files:
        raw = json.loads(f.read_text(encoding="utf-8"))
        ts = parse_timestamp_from_filename(f.name)
        tracker.load_snapshot(raw, ts)

    print(f"Loaded {len(tracker.snapshots)} snapshots")
    print(f"Detected key: {tracker.detected_inconsistent_key}")
    print(f"Events: {len(tracker.events)}")
    print()

    report = tracker.generate_forensic_report()

    output_path = Path(__file__).resolve().parent.parent / "reports" / "hnd_2025_forensic.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Forensic report written to: {output_path}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    cumulative = tracker.get_special_scrutiny_cumulative()
    print(f"\nSpecial scrutiny votes: {cumulative['total_special_scrutiny_votes']:,}")
    for c, v in sorted(cumulative["votes_by_candidate"].items()):
        print(f"  {c}: {v:+,}")

    anomalies = tracker.detect_anomalies()
    by_kind = {}
    for a in anomalies:
        by_kind.setdefault(a.kind, []).append(a)
    print(f"\nAnomalies detected: {len(anomalies)}")
    for kind, items in sorted(by_kind.items()):
        print(f"  {kind}: {len(items)}")

    blackouts = tracker.detect_blackout_windows()
    print(f"\nBlackout windows: {len(blackouts)}")
    for b in blackouts:
        print(f"  {b['gap_start']} -> {b['gap_end']} ({b['gap_minutes']} min)")
        if b["trend_shifts_pp"]:
            for c, s in sorted(b["trend_shifts_pp"].items()):
                print(f"    {c}: {s:+.3f} pp")

    velocity = tracker.detect_resolution_velocity_anomalies()
    print(f"\nVelocity anomalies: {len(velocity)}")
    for v in velocity:
        print(f"  {v['timestamp']}: {v['rate_per_minute']} actas/min ({v['delta_actas']} in {v['elapsed_minutes']} min)")

    asymmetry = tracker.detect_asymmetric_benefit()
    if asymmetry:
        print("\nAsymmetric benefit: [REDACTED]")
        print(f"  Swing: +{asymmetry['swing_pp']} pp, z={asymmetry['z_score']:+.3f}, p={asymmetry['z_pvalue']:.5f}")
        print(f"  Extra votes: ~{asymmetry['estimated_extra_votes']:,}")
    else:
        print("\nAsymmetric benefit: not detected")

    benford = tracker.detect_benford_special_scrutiny()
    if benford:
        print(f"\nBenford's Law: chi2={benford['chi2_statistic']:.4f}, p={benford['chi2_pvalue']:.5f}")
        print(f"  Significant: {benford['significant']}")
    else:
        print("\nBenford's Law: insufficient data")

    hold = tracker.detect_hold_and_release()
    print(f"\nHold-and-release patterns: {len(hold)}")
    for p in hold:
        print(f"  {p['stagnation_cycles']} cycles stagnation -> {p['released_actas']} actas released at {p['release_timestamp']}")

    progressive = tracker.detect_progressive_injection()
    if progressive:
        print(f"\nProgressive injection: DETECTED")
        print(f"  Cycles: {progressive['cycles_count']}")
        print(f"  Avg delta/cycle: {progressive['avg_delta_per_cycle']:.2f}")
        print(f"  Z-score: {progressive['z_score_acumulado']:+.3f} (p={progressive['z_score_pvalue']:.5f})")
    else:
        print("\nProgressive injection: not detected")


if __name__ == "__main__":
    main()
