# Semantic overflow

KIND: REFERENCE

Undated distilled design knowledge, **one topic per file**, provenance required
(ledger tags / experiment dirs / paper equation refs). See
[../README.md](../README.md) for what belongs here versus
`doc/design-reference.md` versus a journal entry. **Supersede, don't delete.**

*(empty — first entries land when a topic outgrows a journal entry)*

## What belongs here

| put it in | when |
|---|---|
| `doc/design-reference.md` | it is a *constraint on the design* that fits in one numbered bullet — the context pack lifts those bullets into working memory |
| `doc/journal/<slug>.md` | it is a **dated lesson**: a symptom, its mechanism, and the rule it establishes; fits in one screen |
| **here** | it is a *topic*, not a lesson — a study, a map, a table that keeps growing: it has no single date, it will be extended, and it would blow the 20 KB journal cap or drown a design-reference bullet |

Expected first occupant: the IHP SG13G2 device-behaviour study — gm/ID, gm/gds,
Vgs at 1 nA, leakage and integrated gate-referred noise versus inversion level
and geometry for `sg13_hv_nmos` / `sg13_hv_pmos` / `sg13_lv_*`, currently seeded
as a table in `doc/pdk-notes.md` and expected to outgrow it.

## Entry conventions

* **Filename**: `<topic-slug>.md`, no date (these are living topics, not events).
* **Line 1**: `# <topic>` — a noun phrase, not a claim (claims are journal
  entries).
* **Line 3**: `KIND: REFERENCE | type: semantic | status: live` — the
  `type:`/`status:` fields are read by the same lint and the same context-pack
  filter as journal entries, so keep them on line 3 and inside the first 400
  characters.
* **Provenance is mandatory and inline**: every number carries its ledger tag,
  experiment dir, deck hash, or paper equation number in the same row it appears
  in. A number with no pointer is deleted on sight, not argued with.
* **Numbers carried over from the originating campaign are marked as such**
  (`carried forward — not re-measured here`) and never presented as a
  measurement of this repo. If it has been re-measured on IHP SG13G2, say so and
  give the run.
* **Tables and plots first**; prose is interpretation only.
* **20 KB cap** per file, same as a journal entry. Past that, split the topic —
  a topic that cannot be split is a topic that was two topics.
* **Supersede, don't delete**: flip `status: superseded` on line 3 and prepend
  `[superseded <date> — see <file/section>]` as the first body line, inside the
  first 400 characters. Retire the claim that died, not the whole file.
* An overflow file that a journal entry distils from should be linked from that
  entry, and vice versa — relative markdown links only.
