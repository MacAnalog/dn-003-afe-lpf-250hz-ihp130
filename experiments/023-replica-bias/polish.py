"""Long Butterworth fit of a built candidate's caps (device sizing untouched)."""
import json, sys
from common import HERE, M, K, AXES, from_json, to_json
from lab import shape as S, thd as T
name = sys.argv[1]; it = int(sys.argv[2]) if len(sys.argv) > 2 else 200
J = json.loads((HERE / f"{name}.json").read_text())
d = from_json(J["design"])
d, res = S.fit_butter(d, f"pol023_{name}", fc_target=250.0, maxiter=it, verbose=False)
s = M.evaluate(d, f"pol023_{name}_sc", record=False)
print(M.table({name: s}), flush=True)
J["design"] = to_json(d); J["nominal"] = dict(s.values); J["violations"] = s.violations
t = T.measure(d, tag=f"pol023_{name}_thd", gate=False); J["thd_db"] = t.thd_db
print(f"THD {t.thd_db:.2f}", flush=True)
r = K.run(d, f"pol023_{name}_axes", corners=AXES, record=False)
print(K.table(r), flush=True)
J["axes"] = [{"corner": x.corner.as_dict(), "status": x.status, "values": (dict(x.score.values) if x.score else {}), "violations": x.violations} for x in r]
(HERE / f"{name}.json").write_text(json.dumps(J, indent=1, default=str))
