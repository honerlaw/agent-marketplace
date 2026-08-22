"""Q2 of issue #74: is the treatment-control delta separable from run-to-run variance?

Runs ONE skill / ONE case N times per arm through the REAL control mechanism, judging
every transcript with the same rubric, and reports within-arm spread alongside the
between-arm difference. A delta smaller than the noise is a no-go for backfilling.
"""
import json, statistics, sys, pathlib
sys.path.insert(0, "scripts")
import run_skill_evals as r

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
SKILL, CASE_ID = "debug", "stale-cache-incident"

cases = r.load_cases(SKILL)
case = next(c for c in cases if c.id == CASE_ID)

out = {"skill": SKILL, "case": CASE_ID, "n": N, "rubric_max": len(case.rubric),
       "treatment": [], "control": []}
for arm, available in (("treatment", True), ("control", False)):
    for i in range(N):
        try:
            transcript = r.claude_invoke(case.prompt, available, SKILL)
            score = float(r.claude_judge(case.prompt, transcript, case.rubric)["score"])
        except Exception as e:
            score = None
            print(f"{arm}[{i}] ERROR {e}", file=sys.stderr)
        out[arm].append(score)
        print(f"{arm}[{i}] = {score}", flush=True)

for arm in ("treatment", "control"):
    xs = [x for x in out[arm] if x is not None]
    out[arm + "_mean"] = statistics.mean(xs) if xs else None
    out[arm + "_stdev"] = statistics.stdev(xs) if len(xs) > 1 else 0.0
    out[arm + "_range"] = (min(xs), max(xs)) if xs else None
if out["treatment_mean"] is not None and out["control_mean"] is not None:
    out["delta"] = out["treatment_mean"] - out["control_mean"]
    pooled = max(out["treatment_stdev"], out["control_stdev"])
    out["pooled_noise"] = pooled
    out["separable"] = abs(out["delta"]) > 2 * pooled if pooled else None
print(json.dumps(out, indent=2))
