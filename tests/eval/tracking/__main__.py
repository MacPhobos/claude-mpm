"""Allow running degradation detection via ``python -m tests.eval.tracking``."""

from __future__ import annotations

import sys

from tests.eval.tracking.degradation_detector import main

sys.exit(main())
