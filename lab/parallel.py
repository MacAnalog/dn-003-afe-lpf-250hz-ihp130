"""The platform's ordered concurrent map, capped by this repo's LPF_JOBS."""
from __future__ import annotations

from functools import partial

from spicexplorer_harness import parallel as _P

from .config import H

jobs = partial(_P.jobs, H.jobs_env)
batch = partial(_P.batch, env=H.jobs_env)
ok = _P.ok
