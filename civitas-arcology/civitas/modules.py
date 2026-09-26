"""Pure vertical module ladder math for DDCC anchor generation."""

from __future__ import annotations

import math

from .config import FLOOR_HEIGHT, FLOOR_SLAB, MODULE_FLOORS, MODULE_M


def module_slots(z_min: float, z_max: float, floor_exclusions=None) -> list[dict]:
    """Return the 20-floor module slots spanning ``z_min`` through ``z_max``.

    The module count is the floor of the measured height divided by the
    governing module height, with a minimum of one. Any remainder is absorbed
    by the top module, so the ladder never extends beyond ``z_max``; that
    module therefore reports more than the nominal 20 floors when needed.

    ``floor_exclusions`` is an optional list of (z_min, z_max) tuples where
    no floors should be generated (e.g., below RadialDisk01 or above Cathedral).
    """
    height = max(0.0, z_max - z_min)
    count = max(1, math.floor(height / MODULE_M))
    floor_pitch = FLOOR_HEIGHT + FLOOR_SLAB
    slots = []
    next_floor = 1
    for index in range(count):
        bottom = z_min + index * MODULE_M
        top = z_max if index == count - 1 else bottom + MODULE_M
        
        # Skip this module if it falls within an exclusion zone
        if floor_exclusions:
            skip = False
            for excl_min, excl_max in floor_exclusions:
                if (bottom >= excl_min and bottom < excl_max) or \
                   (top > excl_min and top <= excl_max) or \
                   (bottom <= excl_min and top >= excl_max):
                    skip = True
                    break
            if skip:
                continue
        
        floors = max(1, math.floor((top - bottom) / floor_pitch))
        first = next_floor
        last = first + floors - 1
        slots.append(dict(
            z=(bottom + top) / 2.0,
            z_min=bottom,
            z_max=top,
            module_floors=floors,
            floor_first=first,
            floor_last=last,
        ))
        next_floor = last + 1
    return slots
