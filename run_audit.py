"""Convenience entrypoint for Capability Audit.

Allows running directly without setting PYTHONPATH or installing editable mode:
    python run_audit.py
    python run_audit.py --config configs/capability_audit.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path
_SRC_DIR = Path(__file__).resolve().parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from repguard.audit.capability_audit import main

if __name__ == "__main__":
    main()
