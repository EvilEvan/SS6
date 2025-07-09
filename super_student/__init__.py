"""Super Student root package.

This package contains the modernized codebase. During the migration
period it simply ensures that the repository root is on the import
path so legacy modules (still at the project root) can be imported
from packages located inside *super_student*.
"""

from __future__ import annotations

import sys
import pathlib

# Add repository root to `sys.path` for implicit relative imports
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

__all__: list[str] = []