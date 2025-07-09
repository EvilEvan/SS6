"""New project entry point.

Eventually this script will bootstrap the refactored engine contained in the
*super_student* package.  For now it simply imports the previous standalone
script so behaviour stays identical.
"""

import importlib
import pathlib
import runpy
import sys

# Ensure repository root is on *sys.path* so that relative imports in the
# legacy code continue to work even if the project is executed as an
# installed module.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Execute the legacy monolithic script.  This will start the game loop.
runpy.run_path(str(_REPO_ROOT / "SS6.origional.py"), run_name="__main__")