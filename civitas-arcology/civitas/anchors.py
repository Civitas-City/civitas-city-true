"""DDCC coordinate anchors.

The Devin Digital City Cartography registry resolves four spatial fields per
artifact — radialdisk, spoke, level, sector — by looking up a NAMED NODE in
the exported .glb, never by hardcoding a position. Anchors are empties (zero
geometry cost, movable without touching a mesh) named with dashes only, per
SBCS 3.1:

    radialdisk-01
    radialdisk-01-spoke-04
    radialdisk-01-level-03
    radialdisk-01-level-03-sector-b

Positions are derived from the real world-space bounds of the source city
meshes, so the registry and the model cannot drift apart.
"""

from __future__ import annotations

import math
import re
import string

import bpy

from . import config, modules, util
from .util import TAU

ANCHOR_COLLECTION = "CIVITAS-ANCHORS"
SPOKES = 14  # Base-14
SECTORS = 14  # a .. n
DISKS = 7

# radialdisk-NN -> source object prefixes that make up that disk
DISK_SOURCES = {
    1: ("L1_",),
    2: ("L2_",),
    3: ("L3_",),
    4: ("L4_",),
    5: ("L5_",),
    6: ("L6_",),
    7: ("L7_",),
}

# level anchors follow the numbered sub-disks actually present in the source
LEVEL_PATTERNS = {
    1: ("L1_Cargo_Ring", "L1_Hollow_Hub_Wall"),
}

SECTOR_LETTERS = string.ascii_lowercase[:SECTORS]
ANCHOR_NAME_RE = re.compile(
    r"^radialdisk-(?:\d{2}|helix)"
    r"(?:(?:-spoke-\d{2})|(?:-level-\d{2,}(?:-sector-[a-n])?))?$"
)


def is_anchor_name(name: str) -> bool:
    return ANCHOR_NAME_RE.fullmatch(name) is not None


def _level_name(root: str, index: int) -> str:
    """Return a level name whose numeric width is a minimum of two digits."""
    return f"{root}-level-{index:02d}"

# The Helix Tower is the void running up the axis, not a radial disk, so it
# lives outside the radialdisk namespace: one root, one anchor per string, and
# a base-14 level ladder up the shaft with fourteen sectors each.
HELIX_ROOT = "helix"
HELIX_SOURCES = ("Tower_Sec", "Zenith_Sec")
HELIX_STRINGS = 14
HELIX_LEVELS = 14


def _members(prefixes) -> list[bpy.types.Object]:
    return [o for o in bpy.data.objects
            if o.type == "MESH" and o.name.startswith(tuple(prefixes))]


def _bounds(objects):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for obj in objects:
        (bx0, by0, bz0), (bx1, by1, bz1) = util.world_bounds(obj)
        for i, (a, b) in enumerate(((bx0, bx1), (by0, by1), (bz0, bz1))):
            lo[i] = min(lo[i], a)
            hi[i] = max(hi[i], b)
    return lo, hi


def _level_meshes(disk: int) -> list[bpy.types.Object]:
    """Ordered bottom-to-top level meshes for a radial disk."""
    prefix = f"L{disk}_Disk_"
    levels = [o for o in bpy.data.objects if o.name.startswith(prefix)]
    if not levels:
        levels = [bpy.data.objects[n] for n in LEVEL_PATTERNS.get(disk, ())
                  if n in bpy.data.objects]
    return sorted(levels, key=lambda o: o.matrix_world.translation.z)


def _level_slots(disk: int, lo, hi, radius: float, floor_exclusions=None) -> list[dict]:
    """A 20-floor module ladder of level slots, bottom to top.

    A real sub-disk mesh whose centre falls inside a module takes that
    module's exact centre, bounds and radius instead of the module's.
    """
    z0, z1 = lo[2], hi[2]
    meshes = _level_meshes(disk)
    slots = []
    for slot in modules.module_slots(z0, z1, floor_exclusions):
        b0, b1 = slot["z_min"], slot["z_max"]
        slot.update(radius=radius, source="")
        for mesh in meshes:
            (mx0, my0, mz0), (mx1, my1, mz1) = util.world_bounds(mesh)
            centre = (mz0 + mz1) / 2.0
            if b0 <= centre < b1 or (b1 == z1 and centre == b1):
                # Floor indices stay on the canonical module grid; mesh bounds
                # describe geometry and intentionally do not recalculate them.
                slot.update(z=centre, z_min=mz0, z_max=mz1,
                            radius=max((mx1 - mx0) / 2.0, (my1 - my0) / 2.0),
                            source=mesh.name)
                break
        slots.append(slot)
    return slots


def _helix_ladder(coll, cx, cy, lo, hi, radius, stats) -> None:
    """Coordinates up the Helix shaft: helix / -string-NN / -level-NN-sector-x."""
    name = HELIX_ROOT
    cz = (lo[2] + hi[2]) / 2.0
    anchor = util.ensure_empty(name, coll, (cx, cy, cz),
                               kind="SPHERE", size=radius * 0.05)
    anchor["radius-m"] = radius
    anchor["z-min-m"] = lo[2]
    anchor["z-max-m"] = hi[2]
    stats["helix"] += 1

    for strand in range(1, HELIX_STRINGS + 1):
        th = TAU * (strand - 1) / HELIX_STRINGS
        string_anchor = util.ensure_empty(
            f"{name}-string-{strand:02d}", coll,
            (cx + radius * math.cos(th), cy + radius * math.sin(th), cz),
            kind="SINGLE_ARROW", size=radius * 0.02)
        string_anchor.parent = anchor
        string_anchor.matrix_parent_inverse.identity()
        string_anchor["bearing-deg"] = math.degrees(th)
        stats["helix-strings"] += 1

    span = (hi[2] - lo[2]) / HELIX_LEVELS
    for i in range(1, HELIX_LEVELS + 1):
        z0 = lo[2] + span * (i - 1)
        level_name = f"{name}-level-{i:02d}"
        level_anchor = util.ensure_empty(
            level_name, coll, (cx, cy, z0 + span / 2.0),
            kind="PLAIN_AXES", size=radius * 0.05)
        level_anchor.parent = anchor
        level_anchor.matrix_parent_inverse.identity()
        level_anchor["radius-m"] = radius
        level_anchor["z-min-m"] = z0
        level_anchor["z-max-m"] = z0 + span
        stats["helix-levels"] += 1

        for s, letter in enumerate(SECTOR_LETTERS):
            th = TAU * s / SECTORS + TAU / SECTORS / 2.0
            r = radius * 0.62
            sector = util.ensure_empty(
                f"{level_name}-sector-{letter}", coll,
                (cx + r * math.cos(th), cy + r * math.sin(th),
                 z0 + span / 2.0),
                kind="CUBE", size=radius * 0.01)
            sector.parent = level_anchor
            sector.matrix_parent_inverse.identity()
            sector["bearing-deg"] = math.degrees(th)
            stats["helix-sectors"] += 1


def build(scene_root: bpy.types.Collection) -> dict:
    coll = util.ensure_collection(ANCHOR_COLLECTION, scene_root)
    stats = {"disks": 0, "spokes": 0, "levels": 0, "sectors": 0,
             "helix": 0, "helix-strings": 0, "helix-levels": 0,
             "helix-sectors": 0}

    helix = _members(HELIX_SOURCES)
    if helix:
        lo, hi = _bounds(helix)
        _helix_ladder(coll, (lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0,
                      lo, hi, max(hi[0] - (lo[0] + hi[0]) / 2.0,
                                  hi[1] - (lo[1] + hi[1]) / 2.0), stats)

    for disk in range(1, DISKS + 1):
        members = _members(DISK_SOURCES[disk])
        if not members:
            continue
        lo, hi = _bounds(members)
        cx = (lo[0] + hi[0]) / 2.0
        cy = (lo[1] + hi[1]) / 2.0
        cz = (lo[2] + hi[2]) / 2.0
        radius = max(hi[0] - cx, hi[1] - cy)
        disk_name = f"radialdisk-{disk:02d}"
        anchor = util.ensure_empty(disk_name, coll, (cx, cy, cz),
                                   kind="SPHERE", size=radius * 0.05)
        anchor["radius-m"] = radius
        anchor["z-min-m"] = lo[2]
        anchor["z-max-m"] = hi[2]
        stats["disks"] += 1

        for spoke in range(1, SPOKES + 1):
            th = TAU * (spoke - 1) / SPOKES
            spoke_anchor = util.ensure_empty(
                f"{disk_name}-spoke-{spoke:02d}", coll,
                (cx + radius * math.cos(th), cy + radius * math.sin(th), cz),
                kind="SINGLE_ARROW", size=radius * 0.02)
            spoke_anchor.parent = anchor
            spoke_anchor.matrix_parent_inverse.identity()
            spoke_anchor["bearing-deg"] = math.degrees(th)
            stats["spokes"] += 1

        for i, slot in enumerate(_level_slots(disk, lo, hi, radius, None), start=1):
            lz = slot["z"]
            lradius = slot["radius"]
            level_name = f"{disk_name}-level-{i:02d}"
            level_anchor = util.ensure_empty(level_name, coll, (cx, cy, lz),
                                             kind="PLAIN_AXES",
                                             size=lradius * 0.05)
            level_anchor.parent = anchor
            level_anchor.matrix_parent_inverse.identity()
            level_anchor["source-object"] = slot["source"]
            level_anchor["radius-m"] = lradius
            level_anchor["z-min-m"] = slot["z_min"]
            level_anchor["z-max-m"] = slot["z_max"]
            level_anchor["module-floors"] = slot["module_floors"]
            level_anchor["floor-first"] = slot["floor_first"]
            level_anchor["floor-last"] = slot["floor_last"]
            stats["levels"] += 1

            for s, letter in enumerate(SECTOR_LETTERS):
                th = TAU * s / SECTORS + TAU / SECTORS / 2.0
                r = lradius * 0.62
                sector = util.ensure_empty(
                    f"{level_name}-sector-{letter}", coll,
                    (cx + r * math.cos(th), cy + r * math.sin(th), lz),
                    kind="CUBE", size=lradius * 0.01)
                sector.parent = level_anchor
                sector.matrix_parent_inverse.identity()
                sector["bearing-deg"] = math.degrees(th)
                stats["sectors"] += 1

    helix_members = _members(("Tower_", "Zenith_"))
    if helix_members:
        helix_lo, helix_hi = _bounds(helix_members)
        helix_cx = (helix_lo[0] + helix_hi[0]) / 2.0
        helix_cy = (helix_lo[1] + helix_hi[1]) / 2.0
        helix_cz = (helix_lo[2] + helix_hi[2]) / 2.0
        helix_radius = max(helix_hi[0] - helix_cx, helix_hi[1] - helix_cy)
        helix_name = "radialdisk-helix"
        helix_anchor = util.ensure_empty(
            helix_name, coll, (helix_cx, helix_cy, helix_cz),
            kind="SPHERE", size=helix_radius * 0.05)
        helix_anchor["radius-m"] = helix_radius
        helix_anchor["z-min-m"] = helix_lo[2]
        helix_anchor["z-max-m"] = helix_hi[2]
        stats["disks"] += 1

        for spoke in range(1, config.HELIX_STRINGS + 1):
            th = TAU * (spoke - 1) / config.HELIX_STRINGS
            spoke_anchor = util.ensure_empty(
                f"{helix_name}-spoke-{spoke:02d}", coll,
                (helix_cx + helix_radius * math.cos(th),
                 helix_cy + helix_radius * math.sin(th), helix_cz),
                kind="SINGLE_ARROW", size=helix_radius * 0.02)
            spoke_anchor.parent = helix_anchor
            spoke_anchor.matrix_parent_inverse.identity()
            spoke_anchor["bearing-deg"] = math.degrees(th)
            stats["spokes"] += 1

        level_number = 1
        previous_floor_last = 0
        for segment, prefixes in (("tower", ("Tower_",)),
                                  ("zenith", ("Zenith_",))):
            members = _members(prefixes)
            if not members:
                continue
            lo, hi = _bounds(members)
            cx = (lo[0] + hi[0]) / 2.0
            cy = (lo[1] + hi[1]) / 2.0
            radius = max(hi[0] - cx, hi[1] - cy)
            # Apply floor exclusions based on segment type
            floor_exclusions = None
            if segment == "tower":
                # No floors below RadialDisk01 in convergence tower
                floor_exclusions = [(config.CONVERGENCE_TOWER_FLOOR_EXCLUSION_MIN,
                                    config.CONVERGENCE_TOWER_FLOOR_EXCLUSION_MAX)]
            elif segment == "zenith":
                # No floors above Cathedral of Light in Sovereignty tower
                # Cathedral sits on top of RD07 (28036-33636)
                floor_exclusions = [(config.CATHEDRAL_FLOOR_EXCLUSION_MIN,
                                    config.CATHEDRAL_FLOOR_EXCLUSION_MAX)]
            
            segment_slots = modules.module_slots(lo[2], hi[2], floor_exclusions)
            
            floor_offset = previous_floor_last
            for slot in segment_slots:
                floor_first = slot["floor_first"] + floor_offset
                floor_last = slot["floor_last"] + floor_offset
                level_name = _level_name(helix_name, level_number)
                level_anchor = util.ensure_empty(
                    level_name, coll, (cx, cy, slot["z"]),
                    kind="PLAIN_AXES", size=radius * 0.05)
                level_anchor.parent = helix_anchor
                level_anchor.matrix_parent_inverse.identity()
                level_anchor["source-object"] = ""
                level_anchor["segment"] = segment
                level_anchor["radius-m"] = radius
                level_anchor["z-min-m"] = slot["z_min"]
                level_anchor["z-max-m"] = slot["z_max"]
                level_anchor["module-floors"] = slot["module_floors"]
                level_anchor["floor-first"] = floor_first
                level_anchor["floor-last"] = floor_last
                stats["levels"] += 1

                for s, letter in enumerate(SECTOR_LETTERS):
                    th = TAU * s / SECTORS + TAU / SECTORS / 2.0
                    r = radius * 0.62
                    sector = util.ensure_empty(
                        f"{level_name}-sector-{letter}", coll,
                        (cx + r * math.cos(th), cy + r * math.sin(th),
                         slot["z"]),
                        kind="CUBE", size=radius * 0.01)
                    sector.parent = level_anchor
                    sector.matrix_parent_inverse.identity()
                    sector["bearing-deg"] = math.degrees(th)
                    stats["sectors"] += 1
                level_number += 1
            previous_floor_last = segment_slots[-1]["floor_last"] + floor_offset
    return stats


def manifest() -> list[str]:
    """Every anchor name currently in the scene, for registry validation."""
    coll = bpy.data.collections.get(ANCHOR_COLLECTION)
    if coll is None:
        return []
    return sorted(o.name for o in coll.all_objects if is_anchor_name(o.name))
