# Procedural overflow

KIND: REFERENCE

Undated recipes and checklists (multi-step flows) that outgrow
[../../environment.md](../../environment.md), **one per file**. Procedural
memory is the **high-risk tier** ([../README.md](../README.md)): entries here
land **human-reviewed**, and anything that proposes a change to `lab/`,
`scripts/`, `xschem/`, an agent definition or `CLAUDE.md` goes to
`doc/proposed-lab-fixes.md` first. **Supersede, don't delete.**

* [layout-lane-recipe.md](layout-lane-recipe.md) — the certified-cell → GDS → DRC/LVS/PEX → post-layout benches → review flow (agents, runners, gates, commands)

## What belongs here

| put it in | when |
|---|---|
| `doc/environment.md` | it is a **one-line trap or setting**: a simulator gotcha, a lane variable, a flag that must be set. The running gotcha list |
| `doc/journal/<slug>.md` | it is a **dated lesson**: symptom → mechanism → rule. One trap, one entry |
| **here** | it is a **procedure**: an ordered multi-step flow with preconditions, checks between steps, and a stated failure mode per step |
| `lab/` or `scripts/` | the procedure has run three times without changing — promote it to code and delete the recipe (**that promotion is a procedural write: propose the diff, do not self-apply**) |

Expected first occupants:

* the corner / Monte-Carlo run recipe (which `.lib` sections
  `cornerMOShv.lib` actually provides — `mos_tt`, `mos_ss`, `mos_ff`, `mos_sf`,
  `mos_fs` — how to batch them through `lab.parallel`, and the mandatory
  self-test that two Monte-Carlo samples are **not** bit-identical before any
  yield claim is made);
* the xschem → netlist → `lab.verify` recipe (draw, netlist, diff the delivered
  netlist against the netlist-lane netlist through the **same** netlister,
  re-certify as-built).

## Entry conventions

* **Filename**: `<recipe-slug>.md`, no date.
* **Line 1**: `# <recipe name>` — an imperative or a noun phrase for the flow.
* **Line 3**: `KIND: REFERENCE | type: procedural | status: live` — same
  position and same first-400-character window as a journal entry, because the
  same lint and the same context-pack filter read it.
* **Structure**: *Preconditions* → *Steps* (numbered, each with the exact
  command and its expected output) → *Checks* (what proves the step worked) →
  *Failure modes* (what it looks like when it silently did not).
* **Every step that can fail silently must name its check.** This is the whole
  reason procedures live here rather than in someone's head: in this lane a
  failed dc operating point still exits 0, an unqualified `.nodeset` is a no-op
  that only warns, and a starved noise analysis leaves the previous plot
  current. A recipe without checks reproduces those failures faithfully.
* **Provenance**: cite the journal entry or ledger tag the step exists because
  of, so a reader can see which failure bought it.
* **20 KB cap**, same as a journal entry.
* **Supersede, don't delete**: flip `status: superseded` on line 3, prepend
  `[superseded <date> — see <file>]` as the first body line. A retired recipe
  that people still have in muscle memory is more dangerous than a missing one.
* **Human review**: a new or changed recipe here that alters what "sign-off"
  means is a procedural write — open the `doc/proposed-lab-fixes.md` section and
  end the accompanying journal entry with
  `Procedural write (lab/) — flagged for owner review per CLAUDE.md rule 10.`
