import json
import math
import sys
from datetime import datetime

WINDOW_HOURS = 72

def tier_weight(tier):
    return {
        "T1": 0.95,
        "T2": 0.80,
        "T3": 0.55,
        "T4": 0.25,
        "Unknown": 0.30,
        "Negative Null": 0.40
    }.get(tier, 0.30)

def strength(event):
    return (
        event.get("anomaly_score", 0)
        * event.get("confidence", 0)
        * tier_weight(event.get("tier", "T3"))
    )

def time_diff_hours(t1, t2):
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    dt1 = datetime.strptime(t1, fmt)
    dt2 = datetime.strptime(t2, fmt)
    return abs((dt1 - dt2).total_seconds()) / 3600

def time_decay(hours):
    return math.exp(-hours / 36)

def timing_boost(max_delta_hours):
    if max_delta_hours <= 6:
        return 0.10
    if max_delta_hours <= 24:
        return 0.05
    return 0.0

def coherence_bonus(p, c, k):
    domains_present = all([p, c, k])
    if domains_present:
        return 1.10
    return 1.0

def independence_score(events):
    groups = [e.get("independence_group", "unknown") for e in events]
    unique = len(set(groups))

    if unique == 3:
        return 1.0
    if unique == 2:
        return 0.85
    return 0.70

def contamination_penalty(events):
    avg = sum(e.get("contamination_risk", 0.3) for e in events) / len(events)

    if avg >= 0.50:
        return 0.70
    if avg >= 0.25:
        return 0.85
    return 1.0

def load_events(path):
    with open(path, "r") as f:
        return json.load(f)["events"]

def run_correlation(events):
    physical = [e for e in events if e["domain"] == "physical"]
    cognitive = [e for e in events if e["domain"] == "cognitive"]
    computational = [e for e in events if e["domain"] == "computational"]

    results = []

    for p in physical:
        for c in cognitive:
            for k in computational:
                dt_pc = time_diff_hours(p["timestamp_utc"], c["timestamp_utc"])
                dt_pk = time_diff_hours(p["timestamp_utc"], k["timestamp_utc"])
                dt_ck = time_diff_hours(c["timestamp_utc"], k["timestamp_utc"])

                if dt_pc > WINDOW_HOURS or dt_pk > WINDOW_HOURS:
                    continue

                p_s = strength(p)
                c_s = strength(c) * time_decay(dt_pc)
                k_s = strength(k) * time_decay(dt_pk)

                base_score = (0.50 * p_s) + (0.25 * c_s) + (0.25 * k_s)

                max_delta = max(dt_pc, dt_pk, dt_ck)

                score = base_score
                score *= coherence_bonus(p, c, k)
                score *= independence_score([p, c, k])
                score *= contamination_penalty([p, c, k])
                score += timing_boost(max_delta)

                score = min(score, 1.0)

                results.append({
                    "physical": p["event_id"],
                    "cognitive": c["event_id"],
                    "computational": k["event_id"],
                    "base_score": round(base_score, 4),
                    "final_score": round(score, 4),
                    "dt_pc_hours": round(dt_pc, 2),
                    "dt_pk_hours": round(dt_pk, 2),
                    "dt_ck_hours": round(dt_ck, 2),
                    "coherence_bonus": coherence_bonus(p, c, k),
                    "independence_score": independence_score([p, c, k]),
                    "contamination_penalty": contamination_penalty([p, c, k]),
                    "timing_boost": timing_boost(max_delta)
                })

    return sorted(results, key=lambda x: x["final_score"], reverse=True)

def classify(score):
    if score >= 0.65:
        return "T2_candidate_requires_replication"
    elif score >= 0.40:
        return "T3_instrumented_pattern"
    else:
        return "T4_insufficient"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/axiom_correlate.py <path_to_json>")
        sys.exit(1)

    events = load_events(sys.argv[1])
    results = run_correlation(events)

    print("\nTop Correlations:\n")

    for r in results[:10]:
        r["classification"] = classify(r["final_score"])
        print(json.dumps(r, indent=2))
