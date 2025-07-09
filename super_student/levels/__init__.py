"""Levels subpackage providing compatibility shims.

All existing level implementations live under the top-level *levels/*
directory.  They will be gradually moved inside this package.  Until the
migration is finished we simply re-export them so that *both*

    from levels import ColorsLevel
and
    from super_student.levels import ColorsLevel

work identically.
"""

from __future__ import annotations

from levels.colors_level import ColorsLevel  # type: ignore
from levels.shapes_level import ShapesLevel  # type: ignore
from levels.alphabet_level import AlphabetLevel  # type: ignore
from levels.numbers_level import NumbersLevel  # type: ignore
from levels.cl_case_level import CLCaseLevel  # type: ignore

__all__ = [
    "ColorsLevel",
    "ShapesLevel",
    "AlphabetLevel",
    "NumbersLevel",
    "CLCaseLevel",
]