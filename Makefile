# The front door.  `make help` lists everything; every target is one command an
# agent (or a human) is expected to run directly.  The generic harness (lint,
# pack, runs, freeze) is the platform's spicexplorer-harness driven by
# harness.yaml; scripts/ and lab/ hold what is specific to this design.

# Prefer the checkout's own venv (uv sync creates it); fall back to python3.
PY ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
HARNESS := $(PY) -m spicexplorer_harness.cli --repo .
ARGS ?=

# Fail with a readable message instead of a ModuleNotFoundError when a target
# points at a lab module that is not in this checkout yet.
define need
@$(PY) -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('$(1)') else 1)" 2>/dev/null \
  || { echo "MISSING: $(1) is not in this checkout."; echo "  $(2)"; exit 1; }
endef

help:  ## list every target
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

baseline:  ## simulate the frozen reference deck and print its scorecard
	@$(PY) scripts/baseline.py $(ARGS)

check:  ## lint + unit tests + the reference deck still reproduces its certified scorecard
	@rc=0; $(PY) scripts/lint.py || rc=1; echo; $(PY) -m unittest discover -s tests -q || rc=1; \
	  echo; $(PY) scripts/baseline.py --check || rc=1; exit $$rc

test:  ## the pure-python unit tests (no simulator; they pin CLAIMS, not measurements)
	@$(PY) -m unittest discover -s tests -v

lint:  ## repo invariants (harness.yaml + scripts/lint.py extras); failures carry their remediation
	@$(PY) scripts/lint.py

runs:  ## query the run ledger (ARGS="--fails" | "--best irn_uv" | "--exp 006" | "--kind thd" | "--where topology=b")
	@$(HARNESS) runs $(ARGS)

pack:  ## working-memory context pack (K="noise irn" S="symptom text")
	@$(HARNESS) pack $(K) $(if $(S),--symptom "$(S)") $(ARGS)

freeze:  ## write decks/reference/SHA256SUMS after a deliberate re-certification
	@$(HARNESS) freeze

thd:  ## THD sign-off: 175 mVpp differential at fin = 50 Hz (S7)
	$(call need,lab.thd,run the transient by hand via lab.deck.tran_thd until lab/thd.py lands)
	@$(PY) -m lab.thd $(ARGS)

doctor:  ## is the simulation lane alive? (ngspice + PDK preflight)
	@$(PY) -m lab.ngspice

char:  ## regenerate the device characterisation LUTs in pdk/lut/
	$(call need,lab.char,see doc/pdk-notes.md for how the tables were measured)
	@$(PY) -m lab.char $(ARGS)

clean:  ## delete this checkout's simulation work dir (never the ledger)
	@d=$$($(PY) -c "from lab import config; print(config.WORK)"); \
	  echo "rm -rf $$d"; rm -rf "$$d"

.PHONY: help baseline check test lint runs pack freeze thd doctor char clean
