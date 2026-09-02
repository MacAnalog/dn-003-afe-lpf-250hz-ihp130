# 2026-09-02 — the generic harness is now the platform's `spicexplorer-harness`

KIND: journal entry | type: procedural | status: live

**What moved.** The ledger append/read/query/table, the parallel batch, the context pack and
eight of the ten lint checks were design-agnostic (2–7 design tokens each). They now come from
`spicexplorer-platform/packages/spicexplorer-harness`, installed here as an editable path
dependency (`pyproject.toml` `[tool.uv.sources]`), and every literal they used to carry became a
key in **`harness.yaml`**: the eight spec rows, `frozen: [decks/reference]`, the provenance
denylist, the gitignore musts, the `make runs` column layouts per row kind, `LPF_EXP`/`LPF_JOBS`.

**What stayed.** `lab/ledger.py` and `lab/parallel.py` are shims (row fields `topology`/`vdd`/
`lane`, `design_dict`, the `LPF_JOBS` cap) so the eleven callers in `lab/`, `scripts/` and
`signoff/paper-draft/` did not change. `lab.metrics.SPEC` is derived from `harness.yaml` in its
historic `{key: (label, op, bound)}` shape. `scripts/lint.py` keeps the two checks only this repo
can state: the deck rebuild from `design.json`, and the S5 headline/reference-IRN phrasing.

**Gotchas.**
- `REFERENCE_SHA` in `lint.py` became `decks/reference/SHA256SUMS`; `make freeze` rewrites it
  and is a deliberate act paired with `make check`.
- The deck hash stays 12 hex (the platform package was aligned to this ledger's contract).
- Violation strings changed shape (`S5 … < 40 uVrms: got 49.98`, `S1 …: missing`); nothing in
  the tree parses them, and `lab.metrics.gate` still filters by label substring.
- The path dependency assumes the workspace layout (`../../spicexplorer-platform`); a checkout
  elsewhere edits that one line.

Verified: `make lint` (11 checks), `make runs` on the 435-row ledger, `scripts/baseline.py
--check` on the native lane (row written through the shim; reference reproduced).
