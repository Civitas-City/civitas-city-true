"""The FYNYGRYF ARCOLOGY: junction disk, pylons, arrivals ring, tendrils.

The old Arrivals Ring never cut Civitas City in half because it was carried on
skinny pylons — you saw the city through it. This rebuild keeps that lesson and
makes the pylons substantial instead of dainty:

junction   lens -> +7 km       a solid disk exactly the height of the existing
                               connection (250 m): 11 full floors and one
                               three-quarter data & utility conduit. 14 tapered
                               cutaways point at the pylons, glazed so the
                               interior can see the stars and the light shines
                               out in peace.
pylons     -> 42,000 m         14 habitable pylons, each two ring window-bay
                               modules wide and carrying the same 11 floors and
                               3/4 conduit as the disk, so a pylon is a domain
                               — one per RAD02-RAD04 entity — and transports
                               run from the ring through it into GRAND CENTRAL
                               and on into the city. Clad in dragon scales,
                               private subway tubes along the top and the
                               bottom. The open sky between them is what gives
                               the city back.
ring       42,000 -> 56,000 m  the transformation zone, double the pylon
                               height. Landing zones large and small on both
                               faces, an arrivals ring above and below, its own
                               14 cutaways, and the 14 diamonds resuming their
                               vigil. The lower face is the industrial side;
                               90% of the interior is FYNYGRYF GROUP.
tendrils   56,000 m -> extent  chains of structural boxes half a pylon across:
                               the ring's own rectangles carried on outward,
                               stepping and drifting as they go, growing off
                               every other bay on both faces. They never
                               reconnect to the Arcology — they always reach
                               outward — every surface carries the dazzle
                               coating and the gold line off the pylon scales,
                               each tip is an automated defensive emplacement,
                               and none rises more than half the ring height
                               above the ring. Not every bay grows: the field
                               thickens as the ecosystem does.

The pressurised volume is the junction disk plus the ring: closed solids,
overlapping by RADIAL_SEAL, glazed at every cutaway. That is what holds air,
heat and water for the primary working volume of the NVC.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

from . import config, materials, util
from .util import TAU

LEGACY_COLLECTIONS = ("Zone_C_Mantle", "Zone_C_Maypole", "Zone_C_RimBraid",
                      "Radial_One_Armour", "Radial_Two_Forming",
                      "Radial_Three_Tendrils")
STALE_PREFIXES = ("Radial_One_", "Radial_Two_", "Radial_Three_",
                  "Arcology_Tendril_Helix_")


def purge_legacy(parent: bpy.types.Collection) -> int:
    """Drop superseded mantle/maypole/braid and three-radial geometry."""
    removed = 0
    for name in LEGACY_COLLECTIONS:
        coll = bpy.data.collections.get(name)
        if coll is None:
            continue
        for obj in list(coll.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1
        for child in list(coll.children):
            coll.children.unlink(child)
            bpy.data.collections.remove(child)
        if name in {child.name for child in parent.children}:
            parent.children.unlink(coll)
        bpy.data.collections.remove(coll)
    removed += _drop_stale(STALE_PREFIXES)
    for mesh_name in ("Arcology_RimLoop_Mesh",):
        mesh = bpy.data.meshes.get(mesh_name)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    return removed


def _drop_stale(prefixes: tuple[str, ...]) -> int:
    """Remove objects from a previous naming scheme that is no longer built."""
    removed = 0
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1
    return removed


def _seal(obj: bpy.types.Object, volume: float) -> bpy.types.Object:
    """Record that a deck is a closed pressure volume, and what it holds."""
    obj["pressure-sealed"] = 1
    obj["atmosphere-m3"] = round(volume, 1)
    return obj


def _deck_volume(r_inner: float, r_outer: float, height: float) -> float:
    """Sealed volume of a cut-away deck: the slots are not pressurised."""
    solid = 1.0 - config.CUTAWAY_ARC * (config.CUTAWAY_TAPER + 1.0) / 2.0
    return math.pi * (r_outer ** 2 - r_inner ** 2) * height * solid


def envelope_volume() -> float:
    """Air, heat and water held by the junction disk and the ring, in m3."""
    return (_deck_volume(config.JUNCTION_INNER - config.RADIAL_SEAL,
                         config.JUNCTION_OUTER, config.JUNCTION_DECK_HEIGHT)
            + _deck_volume(config.RING_INNER - config.RADIAL_SEAL,
                           config.RING_OUTER, config.RING_HEIGHT))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _radial_t(radius: float) -> float:
    """0 at the junction, 1 at the canonical extent."""
    span = config.ARCOLOGY_OUTER - config.JUNCTION_INNER
    return min(1.0, max(0.0, (radius - config.JUNCTION_INNER) / span))


def _bearing(index: int) -> float:
    return TAU * index / config.PYLON_COUNT


def scale_prototype(mats: dict) -> bpy.types.Mesh:
    """One dragon scale: a unit dome whose outer tip is a golden emitter."""
    verts, faces = util.ellipsoid(0.5, 0.5, 0.5, segments=18, rings=9)
    mesh = bpy.data.meshes.get("Arcology_Radial_Scale")
    if mesh is None:
        mesh = bpy.data.meshes.new("Arcology_Radial_Scale")
    mesh.clear_geometry()
    mesh.from_pydata(verts, [], [list(f) for f in faces])
    mesh.validate(verbose=False)
    mesh.materials.clear()
    mesh.materials.append(mats["FYNYGRYF_Hull"])
    mesh.materials.append(mats["FYNYGRYF_ScaleTip"])
    for poly in mesh.polygons:
        poly.use_smooth = True
        centre = sum((mesh.vertices[i].co.x for i in poly.vertices), 0.0)
        poly.material_index = (1 if centre / len(poly.vertices)
                               > config.SCALE_TIP else 0)
    return mesh


# --------------------------------------------------------------------------
# cutaways: the tapered slots that let the interior look out
# --------------------------------------------------------------------------


def _slot_half(u: float) -> float:
    """Half-arc of a cutaway at radial fraction u: narrow inside, wide out."""
    bay = TAU / config.CUTAWAY_COUNT
    share = config.CUTAWAY_ARC * _lerp(config.CUTAWAY_TAPER, 1.0, u)
    return bay * share / 2.0


def _in_cutaway(radius: float, theta: float,
                r_inner: float, r_outer: float) -> bool:
    bay = TAU / config.CUTAWAY_COUNT
    u = (radius - r_inner) / max(r_outer - r_inner, 1.0)
    offset = (theta + bay / 2.0) % bay - bay / 2.0
    return abs(offset) < _slot_half(min(1.0, max(0.0, u)))


def _cut_deck(name, coll, r_inner, r_outer, height, z0, mats, glass) -> dict:
    """A sealed deck built as 14 solid sectors with glazed slots between them.

    The slots are the negative space of the pylons: they taper towards the
    axis, they are walled in glass so the deck still holds pressure, and they
    are lipped in gold along both edges.
    """
    bay = TAU / config.CUTAWAY_COUNT
    steps = config.CUTAWAY_STEPS
    half = height / 2.0
    solid, panes, lips = [], [], []
    for step in range(steps):
        u0, u1 = step / steps, (step + 1) / steps
        a0 = _lerp(r_inner, r_outer, u0)
        a1 = _lerp(r_inner, r_outer, u1)
        gap = _slot_half((u0 + u1) / 2.0)
        for index in range(config.CUTAWAY_COUNT):
            centre = _bearing(index)
            solid.append(util.wedge(a0, a1, centre + gap,
                                    centre + bay - gap, -half, half,
                                    arc_steps=4))
            for sign in (1.0, -1.0):
                edge = centre + sign * gap
                inner = edge - sign * config.CUTAWAY_GLASS / max(a0, 1.0)
                panes.append(util.wedge(a0, a1, min(edge, inner),
                                        max(edge, inner), -half, half))
                for z in (half, -half):
                    lo = z - math.copysign(config.CUTAWAY_LIP, z)
                    lips.append(util.wedge(
                        a0, a1, min(edge, inner) - config.CUTAWAY_LIP / a1,
                        max(edge, inner) + config.CUTAWAY_LIP / a1,
                        min(z, lo), max(z, lo)))
    made = {}
    for parts, tag, material in ((solid, "Deck", mats["FYNYGRYF_Hull"]),
                                 (panes, "Glazing", glass),
                                 (lips, "SlotLip", mats["FYNYGRYF_GoldTrim"])):
        verts, faces = util.merge(parts)
        obj = util.ensure_mesh_object(f"{name}_{tag}", coll, verts, faces,
                                      material=material,
                                      location=(0.0, 0.0, z0))
        made[tag] = obj
    _seal(made["Deck"], _deck_volume(r_inner, r_outer, height))
    made["Deck"]["cutaways"] = config.CUTAWAY_COUNT
    return made


def _clad(coll, mesh, tag, rings, inner, outer, half_height, z_base, rng,
          disorder=0.0, skip=None, bore=None) -> int:
    """Tile a deck surface, top and bottom, with overlapping scales.

    `bore` is a radius nothing may reach inside of: the Helix Tunnel, where
    the tower and its 14 strings run and expand into their own plug.
    """
    pitch = (outer - inner) / rings
    count = config.SCALES_PER_RADIAL_RING
    made = 0
    for ring in range(rings):
        radius = inner + pitch * (ring + 0.5)
        t = _radial_t(radius)
        # a scale near the junction is a dome; out at the rim it has drawn out
        # into a woven ribbon, which is what becomes a tendril
        length = pitch * config.SCALE_OVERLAP * (1.0 + config.SCALE_RIBBON * t)
        width = TAU * radius / count * config.SCALE_SPREAD * (1.0 - 0.22 * t)
        rise = config.SCALE_RISE * (1.0 + 0.6 * t)
        for i in range(count):
            th = TAU * i / count + (ring % 2) * math.pi / count
            if skip is not None and skip(radius, th):
                continue
            wobble = rng.uniform(-disorder, disorder)
            seat = radius
            if bore is not None:
                seat = max(seat, bore + length * (1.0 + 0.30 * disorder) / 2.0)
            for sign, face in ((1.0, "Up"), (-1.0, "Dn")):
                name = f"{tag}_Scale_{face}_{ring:02d}_{i:02d}"
                obj = util.ensure_instance(
                    name, coll, mesh,
                    (seat * (1.0 + 0.05 * wobble) * math.cos(th),
                     seat * (1.0 + 0.05 * wobble) * math.sin(th),
                     z_base + half_height * sign),
                    rotation=(0.0,
                              -sign * config.SCALE_TILT * (1.0 + wobble),
                              th),
                    scale=(length * (1.0 + 0.30 * wobble),
                           width * (1.0 + 0.22 * wobble),
                           rise * sign * (1.0 + 0.35 * wobble)),
                )
                obj["radial-scale-tip-m"] = round(length / 2.0, 1)
                made += 1
    return made


# --------------------------------------------------------------------------
# the junction disk
# --------------------------------------------------------------------------


def build_junction(parent: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection("Arcology_Junction", parent)
    glass = materials.ensure_glass("FYNYGRYF_ScaleGlass",
                                   color=(0.957, 0.769, 0.188),
                                   alpha=0.16, emission=0.9)
    z0 = util.junction_z()
    height = config.JUNCTION_DECK_HEIGHT
    # the deck stops at the Helix Tunnel wall rather than sealing inside it:
    # the tower and its 14 strings pass through the bore untouched and keep
    # their own expanding oxygen plug
    inner = config.JUNCTION_INNER
    outer = config.JUNCTION_OUTER
    made = _cut_deck("Arcology_Junction", coll, inner, outer, height, z0,
                     mats, glass)
    deck = made["Deck"]
    deck["helix-bore-clear-m"] = round(inner, 1)
    deck["floors"] = config.JUNCTION_FLOORS
    deck["conduit-decks"] = config.JUNCTION_CONDUIT_SHARE
    deck["floor-height-m"] = round(
        height / (config.JUNCTION_FLOORS + config.JUNCTION_CONDUIT_SHARE), 2)

    rim_verts, rim_faces = util.torus(outer, config.RADIAL_RIM_TUBE,
                                      major_segments=224, minor_segments=8)
    util.ensure_mesh_object("Arcology_Junction_Rim", coll, rim_verts,
                            rim_faces, material=mats["FYNYGRYF_GoldTrim"],
                            location=(0.0, 0.0, z0), shade_smooth=True)

    scales = util.ensure_collection("Arcology_Junction_Scales", coll)

    def skip(radius, th):
        return _in_cutaway(radius, th, inner, outer)

    count = _clad(scales, scale_prototype(mats), "Arcology_Junction",
                  config.JUNCTION_RINGS, config.JUNCTION_INNER, outer,
                  height / 2.0, z0, random.Random(config.RADIAL_SEED),
                  disorder=0.04, skip=skip, bore=config.JUNCTION_INNER)
    return {"junction_scales": count,
            "junction_cutaways": config.CUTAWAY_COUNT,
            "grand_central_platforms": _grand_central(
                util.ensure_collection("Arcology_Grand_Central", coll),
                mats, z0)}


def _grand_central(coll, mats, z0) -> int:
    """The first 2.5 km around the Helix Tower: a commons, not a station.

    It begins outside the Helix Tunnel, so the tower and its 14 strings run
    through a bore this never touches and keep their own expanding plug. The
    14 platforms stand on the pylon bearings, one per pylon, and the lines
    stop here: inside Civitas City people travel by flight and gravity
    control, so nothing leaves GRAND CENTRAL for the city.
    """
    bay = TAU / config.PYLON_COUNT
    half = config.JUNCTION_DECK_HEIGHT / 2.0
    inner = config.GRAND_CENTRAL_INNER
    outer = inner + config.GRAND_CENTRAL_SPAN
    verts, faces = util.annulus(inner, outer, half * 1.72, segments=196)
    obj = util.ensure_mesh_object(
        "Arcology_Grand_Central_Commons", coll, verts, faces,
        material=mats["FYNYGRYF_Interior"], location=(0.0, 0.0, z0))
    obj["transit-hall"] = "GRAND-CENTRAL"
    obj["commons-span-m"] = config.GRAND_CENTRAL_SPAN
    obj["helix-bore-clear-m"] = round(inner, 1)
    obj["platform-count"] = config.PYLON_COUNT * config.PYLON_TRANSIT_LANES
    obj["city-transit-lines"] = config.GRAND_CENTRAL_CITY_LINES
    parts = []
    for index in range(config.PYLON_COUNT):
        centre = _bearing(index) + bay / 2.0
        arc = bay * config.GRAND_CENTRAL_ARC / 2.0
        parts.append(util.wedge(outer - config.GRAND_CENTRAL_SPAN * 0.34,
                                outer, centre - arc, centre + arc,
                                -half * 0.7, half * 0.7, arc_steps=4))
    verts, faces = util.merge(parts)
    util.ensure_mesh_object("Arcology_Grand_Central_Platforms", coll, verts,
                            faces, material=mats["FYNYGRYF_AmberCore"],
                            location=(0.0, 0.0, z0))
    return config.PYLON_COUNT


# --------------------------------------------------------------------------
# the pylons
# --------------------------------------------------------------------------


def _pylon_path(index: int):
    """Centre line, widths and thicknesses of one flattened pylon."""
    z0 = util.junction_z()
    bearing = _bearing(index) + TAU / (2 * config.PYLON_COUNT)
    start = config.JUNCTION_OUTER - config.RADIAL_SEAL
    end = config.RING_INNER + config.RADIAL_SEAL
    width = config.PYLON_WIDTH
    points, widths, thick = [], [], []
    for k in range(config.PYLON_SAMPLES):
        s = k / (config.PYLON_SAMPLES - 1)
        radius = _lerp(start, end, s)
        # the graceful arc: the pylon leaves the disk far wider than it runs,
        # easing to its section over the first PYLON_ARC of the span
        arc = max(0.0, 1.0 - s / config.PYLON_ARC)
        flare = 1.0 + (config.PYLON_ROOT_FLARE - 1.0) * arc ** 2.0
        # and the far end does the same in reverse: the spoke radiates back
        # out into the ring on a soft arc, welding the two together
        tip = max(0.0, 1.0 - (1.0 - s) / config.PYLON_TIP_ARC)
        flare *= 1.0 + (config.PYLON_TIP_FLARE - 1.0) * tip ** 2.4
        points.append((radius * math.cos(bearing), radius * math.sin(bearing),
                       z0))
        widths.append(width * flare)
        thick.append(config.PYLON_HEIGHT
                     * (1.0 + 0.18 * arc ** 2.0 + 0.30 * tip ** 2.4))
    return points, widths, thick


def _clad_pylon(coll, mesh, index, points, widths, thick) -> int:
    """Dragon scales along both faces of a pylon."""
    rows, cols = config.PYLON_SCALE_ROWS, config.PYLON_SCALE_COLS
    made = 0
    last = len(points) - 1
    for row in range(rows):
        s = (row + 0.5) / rows
        i = min(last, int(s * last))
        x, y, z = points[i]
        radius = math.hypot(x, y)
        bearing = math.atan2(y, x)
        length = (config.RING_INNER - config.JUNCTION_OUTER) / rows \
            * config.SCALE_OVERLAP
        width = widths[i] / cols * config.SCALE_SPREAD
        rise = config.SCALE_RISE * (0.6 + 0.5 * s)
        for col in range(cols):
            offset = (col - (cols - 1) / 2.0) * widths[i] / cols
            th = bearing + offset / max(radius, 1.0)
            for sign, face in ((1.0, "Up"), (-1.0, "Dn")):
                name = (f"Arcology_Pylon_{index + 1:02d}"
                        f"_Scale_{face}_{row:02d}_{col}")
                util.ensure_instance(
                    name, coll, mesh,
                    (radius * math.cos(th), radius * math.sin(th),
                     z + thick[i] / 2.0 * sign),
                    rotation=(0.0, -sign * config.SCALE_TILT, bearing),
                    scale=(length, width, rise * sign))
                made += 1
    return made


def build_pylons(parent: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection("Arcology_Pylons", parent)
    scales = util.ensure_collection("Arcology_Pylon_Scales", coll)
    tubes = util.ensure_collection("Arcology_Subway_Tubes", coll)
    mesh = scale_prototype(mats)
    made = {"pylons": 0, "pylon_scales": 0, "subway_tubes": 0}
    for index in range(config.PYLON_COUNT):
        points, widths, thick = _pylon_path(index)
        verts, faces = util.sweep_band(points, widths, thick)
        obj = util.ensure_mesh_object(
            f"Arcology_Pylon_{index + 1:02d}", coll, verts, faces,
            material=mats["FYNYGRYF_Hull"], shade_smooth=True)
        obj["pylon-width-m"] = round(config.PYLON_WIDTH, 1)
        obj["pylon-tip-width-m"] = round(widths[-1], 1)
        obj["pylon-height-m"] = round(config.PYLON_HEIGHT, 1)
        obj["pylon-aspect"] = round(config.PYLON_ASPECT, 2)
        obj["pylon-ring-modules"] = config.PYLON_MODULES
        obj["habitable"] = 1
        obj["pylon-domain"] = index + 1
        obj["domain-architecture"] = "RAD02-RAD04"
        obj["floors"] = config.PYLON_FLOORS
        obj["conduit-decks"] = config.PYLON_CONDUIT_SHARE
        obj["transit-lanes"] = config.PYLON_TRANSIT_LANES
        obj["transit-terminus"] = "GRAND-CENTRAL"
        _seal(obj, sum(w * t for w, t in zip(widths, thick))
              / len(widths) * (config.RING_INNER - config.JUNCTION_OUTER))
        made["pylons"] += 1
        made["pylon_scales"] += _clad_pylon(scales, mesh, index, points,
                                            widths, thick)
        # the private subway tubes: one along the top, one along the bottom
        for sign, face in ((1.0, "Up"), (-1.0, "Dn")):
            path = [(x, y, z + sign * (t / 2.0 + config.TUBE_RADIUS))
                    for (x, y, z), t in zip(points, thick)]
            tverts, tfaces = util.sweep(
                path, [config.TUBE_RADIUS] * len(path), sides=10)
            tube = util.ensure_mesh_object(
                f"Arcology_Subway_{face}_{index + 1:02d}", tubes,
                tverts, tfaces, material=mats["FYNYGRYF_Hull"],
                shade_smooth=True)
            tube["subway-private"] = 1
            made["subway_tubes"] += 1
    return made


# --------------------------------------------------------------------------
# the arrivals ring
# --------------------------------------------------------------------------


def _window_bays(coll, mats, glass, z0) -> int:
    """Vertical windows standing inside the metal, on the outer ring bays."""
    inner, outer = config.RING_INNER, config.RING_OUTER
    rings, sectors = config.RING_RINGS, config.WINDOW_SECTORS
    half = config.RING_HEIGHT / 2.0
    pitch = (outer - inner) / rings
    step = TAU / sectors
    rise = half * config.WINDOW_RISE
    pane, rib, lamp, roof, trim = [], [], [], [], []
    made = 0
    for ring in range(rings - config.WINDOW_RINGS, rings):
        r0 = inner + pitch * ring
        r1 = r0 + pitch
        pad_r = pitch * config.WINDOW_INSET
        pad_t = step * (1.0 - config.WINDOW_PANE) / 2.0
        strips = 2 * config.WINDOW_SLOTS + 1
        for sector in range(sectors):
            t0 = step * sector + pad_t
            t1 = step * (sector + 1) - pad_t
            if _in_cutaway((r0 + r1) / 2.0, (t0 + t1) / 2.0, inner, outer):
                continue
            a0, a1 = r0 + pad_r, r1 - pad_r
            slot = (t1 - t0) / strips
            for sign in (1.0, -1.0):
                base = sign * half * 0.98
                top = base + sign * rise
                lo, hi = min(base, top), max(base, top)
                for strip in range(strips):
                    s0 = t0 + slot * strip
                    target = pane if strip % 2 else rib
                    target.append(util.wedge(a0, a1, s0, s0 + slot, lo, hi))
                lamp.append(util.wedge(a0 + pad_r * 0.5, a1 - pad_r * 0.5,
                                       t0 + slot * 0.6, t1 - slot * 0.6,
                                       lo + rise * 0.05, hi - rise * 0.05))
                cap = top + sign * config.RADIAL_RIM_TUBE
                roof.append(util.wedge(a0 - pad_r * 0.25, a1 + pad_r * 0.25,
                                       t0 - pad_t * 0.18, t1 + pad_t * 0.18,
                                       min(top, cap), max(top, cap)))
                lip = top - sign * rise * 0.015
                trim.append(util.wedge(a0 - pad_r * 0.45, a1 + pad_r * 0.45,
                                       t0 - pad_t * 0.3, t1 + pad_t * 0.3,
                                       min(top, lip), max(top, lip)))
            made += 1
    for parts, tag, material in (
        (pane, "Window", glass),
        (rib, "WindowRib", mats["FYNYGRYF_Hull"]),
        (lamp, "Lantern", mats["FYNYGRYF_AmberCore"]),
        (roof, "WindowRoof", mats["FYNYGRYF_Hull"]),
        (trim, "WindowTrim", mats["FYNYGRYF_GoldTrim"]),
    ):
        verts, faces = util.merge(parts)
        util.ensure_mesh_object(f"Arcology_Ring_{tag}", coll, verts, faces,
                                material=material, location=(0.0, 0.0, z0))
    return made


def _landing_zones(coll, mats, z0) -> dict:
    """Pads on both faces: the top greets, the bottom works."""
    half = config.RING_HEIGHT / 2.0
    rng = random.Random(config.RADIAL_SEED + 5)
    made = {"landing_large": 0, "landing_small": 0}
    marks = []
    for kind, count, radius in (
        ("Large", config.LANDING_LARGE, config.LANDING_LARGE_RADIUS),
        ("Small", config.LANDING_SMALL, config.LANDING_SMALL_RADIUS),
    ):
        per_face = count // 2
        for slot in range(count):
            face = 1.0 if slot < per_face else -1.0
            index = slot % per_face
            if kind == "Large":
                bearing = _bearing(index % config.PYLON_COUNT) \
                    + TAU / (2 * config.PYLON_COUNT)
                span = _lerp(config.RING_INNER, config.RING_OUTER,
                             0.32 if face > 0 else 0.68)
            else:
                bearing = TAU * index / per_face + rng.uniform(-0.02, 0.02)
                span = _lerp(config.RING_INNER, config.RING_OUTER,
                             rng.uniform(0.12, 0.9))
            verts, faces = util.cylinder(radius, config.LANDING_PAD_RISE,
                                         segments=18)
            obj = util.ensure_mesh_object(
                f"Arcology_Landing_{kind}_"
                f"{'Up' if face > 0 else 'Dn'}_{index + 1:02d}",
                coll, verts, faces, material=mats["FYNYGRYF_DazzleCoat"],
                location=(span * math.cos(bearing), span * math.sin(bearing),
                          z0 + face * (half + config.LANDING_PAD_RISE / 2.0)))
            obj["landing-class"] = kind.lower()
            obj["landing-face"] = "industrial" if face < 0 else "reception"
            made[f"landing_{kind.lower()}"] += 1
            # the pads are dazzle coat, i.e. near black on a near black deck;
            # a lit circle painted on each is what makes them legible
            ring = util.torus(radius * 0.82, config.LANDING_PAD_RISE * 0.34,
                              major_segments=36, minor_segments=6)
            top = z0 + face * (half + config.LANDING_PAD_RISE)
            marks.append(([(x + span * math.cos(bearing),
                            y + span * math.sin(bearing), z + top)
                           for x, y, z in ring[0]], ring[1]))
    verts, faces = util.merge(marks)
    util.ensure_mesh_object("Arcology_Landing_Markings", coll, verts, faces,
                            material=mats["FYNYGRYF_GoldenThread"],
                            shade_smooth=True)
    return made


def _diamond_vigil(coll, mats, z0) -> int:
    """The 14 diamonds standing watch, outside the rim of the second ring.

    Each waist sits on the arcology deck plane at the outer edge of the ring,
    reaching a full RadialDisk03 height above and the same below, held to the
    Sovereignty Tower's own slenderness so they read as spires and not slabs.
    """
    bearings = [b for _, b, _ in diamond_anchors()]
    made = 0
    for slot in range(config.PYLON_COUNT):
        bearing = _bearing(slot) + TAU / (2 * config.PYLON_COUNT)
        radius = config.RING_OUTER + config.VIGIL_STANDOFF
        rings = []
        # bottom tip -> waist on the deck plane -> top tip: one solid
        # double-ended diamond, not two floating caps
        for u, wide in ((-1.0, 0.03), (-0.5, 0.62), (0.0, 1.0),
                        (0.5, 0.62), (1.0, 0.03)):
            z = z0 + config.VIGIL_HEIGHT * u
            rings.append(util.superellipse_ring(
                config.VIGIL_SPAN * wide, config.VIGIL_SPAN * wide, z,
                power=2.4, segments=16))
        verts, faces = util.loft(rings)
        obj = util.ensure_mesh_object(
            f"Arcology_Vigil_Diamond_{slot + 1:02d}", coll, verts, faces,
            material=mats["FYNYGRYF_GoldTrim"], shade_smooth=True,
            location=(radius * math.cos(bearing), radius * math.sin(bearing),
                      0.0))
        obj["diamond-vigil"] = slot + 1
        obj["diamond-height-m"] = round(config.VIGIL_HEIGHT * 2.0, 1)
        obj["diamond-seam"] = "RING-OUTER"
        obj["diamond-width-m"] = round(config.VIGIL_SPAN * 2.0, 1)
        obj["diamond-proportion"] = "SOVEREIGNTY-TOWER"
        obj["diamond-tethered"] = 1
        obj["diamond-pillar-bearing"] = round(
            bearings[slot % len(bearings)], 5) if bearings else 0.0
        made += 1
    return made


def build_ring(parent: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection("Arcology_Ring", parent)
    glass = materials.ensure_glass("FYNYGRYF_ScaleGlass",
                                   color=(0.957, 0.769, 0.188),
                                   alpha=0.16, emission=0.9)
    z0 = util.junction_z()
    inner = config.RING_INNER - config.RADIAL_SEAL
    outer, height = config.RING_OUTER, config.RING_HEIGHT
    half = height / 2.0
    made = _cut_deck("Arcology_Ring", coll, inner, outer, height, z0, mats,
                     glass)
    deck = made["Deck"]
    deck["nvc-primary-workspace"] = 1
    deck["fynygryf-interior-share"] = config.RING_INTERIOR_SHARE
    deck["industrial-face"] = "lower"

    # the arrivals rings, one above and one below the ring Civitas added
    for sign, face in ((1.0, "Up"), (-1.0, "Dn")):
        for slot, u in enumerate((0.22, 0.78)):
            major = _lerp(config.RING_INNER, outer, u)
            verts, faces = util.torus(major, config.ARRIVALS_RING_TUBE,
                                      major_segments=196, minor_segments=10)
            obj = util.ensure_mesh_object(
                f"Arcology_Arrivals_Ring_{face}_{slot + 1:02d}", coll,
                verts, faces, material=mats["FYNYGRYF_Hull"],
                shade_smooth=True,
                location=(0.0, 0.0,
                          z0 + sign * (half + config.ARRIVALS_RING_TUBE)))
            obj["arrivals-face"] = "industrial" if sign < 0 else "reception"

    stats = {"ring_cutaways": config.CUTAWAY_COUNT}
    stats["ring_windows"] = _window_bays(coll, mats, glass, z0)
    stats.update(_landing_zones(util.ensure_collection(
        "Arcology_Landing_Zones", coll), mats, z0))
    stats["vigil_diamonds"] = _diamond_vigil(util.ensure_collection(
        "Arcology_Vigil", coll), mats, z0)

    scales = util.ensure_collection("Arcology_Ring_Scales", coll)
    plates = util.ensure_collection("Arcology_Ring_Dazzle", coll)
    mesh = scale_prototype(mats)
    split = _lerp(config.RING_INNER, outer, config.RING_SCALE_SHARE)

    def skip_scale(radius, th):
        return (radius > split
                or _in_cutaway(radius, th, config.RING_INNER, outer))

    stats["ring_scales"] = _clad(
        scales, mesh, "Arcology_Ring", config.RING_RINGS, config.RING_INNER,
        outer, half, z0, random.Random(config.RADIAL_SEED + 2),
        disorder=0.34, skip=skip_scale)
    stats["ring_dazzle_plates"] = _dazzle_plates(plates, mats, split, outer,
                                                 half, z0)
    return stats


def _dazzle_plates(coll, mats, inner, outer, half, z0) -> int:
    """The outer half of the ring: dazzle surface, not scales."""
    rings = max(1, config.RING_RINGS // 2)
    sectors = config.PYLON_COUNT * 4
    pitch = (outer - inner) / rings
    step = TAU / sectors
    made = 0
    for face, sign in (("Up", 1.0), ("Dn", -1.0)):
        parts = []
        for ring in range(rings):
            r0 = inner + pitch * ring
            r1 = r0 + pitch * 0.94
            for sector in range(sectors):
                t0 = step * sector + step * 0.06
                t1 = step * (sector + 1) - step * 0.06
                if _in_cutaway((r0 + r1) / 2.0, (t0 + t1) / 2.0, inner,
                               outer):
                    continue
                z = sign * half
                parts.append(util.wedge(r0, r1, t0, t1,
                                        min(z, z + sign * 22.0),
                                        max(z, z + sign * 22.0)))
                made += 1
        verts, faces = util.merge(parts)
        util.ensure_mesh_object(f"Arcology_Ring_DazzlePlate_{face}", coll,
                                verts, faces,
                                material=mats["FYNYGRYF_DazzleCoat"],
                                location=(0.0, 0.0, z0))
    return made


# --------------------------------------------------------------------------
# the outer tendrils
# --------------------------------------------------------------------------


def _measured_diamonds() -> list[tuple[float, float, float]]:
    """Cap centres from CIVITAS_DIAMONDS, ups first, then downs, by bearing.

    The diamond objects all sit at the origin, so the cap position has to come
    from the transformed bounding box rather than the object location.
    """
    coll = bpy.data.collections.get("CIVITAS_DIAMONDS")
    if coll is None:
        return []
    groups: dict[str, list[tuple[float, float, float]]] = {"Up": [], "Dn": []}
    for obj in coll.all_objects:
        end = obj.name[-2:]
        if end not in groups or "Pillar" not in obj.name:
            continue
        pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        x = sum(p.x for p in pts) / 8.0
        y = sum(p.y for p in pts) / 8.0
        z = sum(p.z for p in pts) / 8.0
        groups[end].append((math.hypot(x, y), math.atan2(y, x), z))
    if len(groups["Up"]) != config.DIAMOND_BEARINGS or \
            len(groups["Dn"]) != config.DIAMOND_BEARINGS:
        return []
    return (sorted(groups["Up"], key=lambda a: a[1])
            + sorted(groups["Dn"], key=lambda a: a[1]))


def diamond_anchors() -> list[tuple[float, float, float]]:
    """The 14 diamond pillar caps: (radius, bearing, z), 7 up and 7 down."""
    measured = _measured_diamonds()
    if measured:
        return measured
    out = []
    for z in config.DIAMOND_Z:
        for i in range(config.DIAMOND_BEARINGS):
            out.append((config.DIAMOND_RADIUS,
                        TAU * i / config.DIAMOND_BEARINGS, z))
    return out


def _tendril_chain(index: int, rng: random.Random, prime: bool = False):
    """One tendril: a chain of structural boxes growing off a ring bay.

    Every other bay grows, and a growing bay grows twice — once off the upper
    deck edge, once off the lower — which is what keeps 98 of them spread all
    through the outer disk without the ring turning into a solid crown. Each
    box is the ring's own rectangle, tapering, stepping and drifting as the
    chain reaches out; the returned boxes are polar cells, ready for wedge().

    A prime tendril is the reserved one: dead centre of its section both
    horizontally and vertically, twice the width and height, running straight
    out with no drift. Every chain ends in a blunt, untapered cap.
    """
    z0 = util.junction_z()
    half = config.RING_HEIGHT / 2.0
    ceiling = half + config.RING_HEIGHT * config.TENDRIL_RISE_SHARE
    bay = TAU / config.WINDOW_SECTORS
    per_bay = config.TENDRIL_SPARS_PER_BAY
    # bays 0, 2, 4 ... grow; the odd ones are the room left for later growth
    bay_index = (index // per_bay) * 2
    face = 1.0 if index % per_bay == 0 else -1.0
    scale = config.TENDRIL_PRIME_SCALE if prime else 1.0
    width = config.PYLON_WIDTH * config.TENDRIL_WIDTH_SHARE * scale
    height = config.PYLON_HEIGHT * scale
    lo, hi = config.TENDRIL_REACH
    budget = (config.ARCOLOGY_OUTER - config.RING_OUTER) * rng.uniform(lo, hi)
    modules = rng.randint(*config.TENDRIL_MODULES)
    bearing = bay * (bay_index + 0.5) + rng.uniform(-1.0, 1.0) * bay * 0.2
    yaw = rng.uniform(-1.0, 1.0) * config.TENDRIL_YAW
    step = rng.uniform(*config.TENDRIL_STEP)
    if prime:
        # the exact middle of section `index`, on the pylon bearing, and the
        # exact middle of the ring height: it runs dead straight and level
        bearing = _bearing(index) + TAU / (2 * config.PYLON_COUNT)
        yaw, step = 0.0, 0.0
        budget = (config.ARCOLOGY_OUTER - config.RING_OUTER) * hi
        modules = config.TENDRIL_MODULES[1]
        face = 0.0
    radius = config.RING_OUTER - config.RADIAL_SEAL
    z = z0 + face * (half - height / 2.0)
    length = config.TENDRIL_MODULE_LEN
    boxes, gold = [], []
    reach = 0.0
    for k in range(modules):
        s = k / max(modules - 1, 1)
        taper = config.TENDRIL_TAPER ** k
        span = min(length * taper, max(budget - reach, length * 0.35))
        arc = (width * taper / 2.0) / max(radius, 1.0)
        centre = bearing + yaw * s ** 1.3
        rise = height * taper
        top, bottom = z + rise / 2.0, z - rise / 2.0
        boxes.append(util.wedge(radius, radius + span, centre - arc,
                                centre + arc, bottom, top, arc_steps=3))
        # the gold of the interior scales, running the length of every box
        lip = arc * 0.16
        for edge in (centre - arc + lip, centre + arc - lip):
            gold.append(util.wedge(radius + span * 0.04,
                                   radius + span * 0.96,
                                   edge - lip * 0.4, edge + lip * 0.4,
                                   top, top + config.THREAD_TUBE))
        reach += span
        joint = span * config.TENDRIL_JOINT
        # the collar steps the next box up or down, always inside the cap of
        # half a ring height above the ring
        climb = face * rise * step
        if abs(z + climb - z0) + rise / 2.0 >= ceiling:
            climb = 0.0
        if k < modules - 1:
            collar = arc * 0.45
            boxes.append(util.wedge(
                radius + span, radius + span + joint,
                centre - collar, centre + collar,
                min(bottom, z + climb - rise / 2.0),
                max(top, z + climb + rise / 2.0), arc_steps=2))
        radius += span + joint
        z += climb
        length = span
    # the blunt end: a square cap at full section, never tapered or rounded,
    # and the platform the weapons emplacement bolts onto
    centre = bearing + yaw
    cap_arc = (width * config.TENDRIL_TAPER ** (modules - 1) / 2.0) \
        / max(radius, 1.0)
    cap_rise = height * config.TENDRIL_TAPER ** (modules - 1)
    cap = config.TENDRIL_BLUNT_LEN * scale
    boxes.append(util.wedge(radius, radius + cap, centre - cap_arc,
                            centre + cap_arc, z - cap_rise / 2.0,
                            z + cap_rise / 2.0, arc_steps=3))
    radius += cap
    tip = (radius * math.cos(centre), radius * math.sin(centre), z)
    return boxes, gold, tip


def _tendril_gold(name, coll, gold, mats) -> None:
    """The gold of the pylon scales, carried out along a tendril chain."""
    verts, faces = util.merge(gold)
    util.ensure_mesh_object(name, coll, verts, faces,
                            material=mats["FYNYGRYF_GoldenThread"])


def _emplacement(name, coll, tip, mats, scale=1.0) -> None:
    """A fleet-pattern battery bolted to a blunt tendril end, aimed out.

    Boxed barbette and square barrels, the same emplacement the host hulls
    carry, so the tip reads as armament rather than a softened point.
    """
    reach = math.hypot(tip[0], tip[1]) or 1.0
    aim = [tip[0] / reach, tip[1] / reach, 0.0]
    span = config.EMPLACEMENT_SPAN * scale
    yaw = math.atan2(aim[1], aim[0])
    parts = [util.box(span * 0.9, span * 1.5, span * 0.8),
             util.box(span * 0.5, span * 0.9, span * 1.1,
                      centre=(span * 0.55, 0.0, 0.0))]
    for barrel in range(config.EMPLACEMENT_BARRELS):
        offset = ((barrel - (config.EMPLACEMENT_BARRELS - 1) / 2.0)
                  * span * 0.34)
        parts.append(util.box(span * 2.2, span * 0.18, span * 0.18,
                              centre=(span * 1.6, offset, 0.0)))
    verts, faces = util.merge(parts)
    cos, sin = math.cos(yaw), math.sin(yaw)
    verts = [(tip[0] + x * cos - y * sin, tip[1] + x * sin + y * cos,
              tip[2] + z) for x, y, z in verts]
    obj = util.ensure_mesh_object(name, coll, verts, faces,
                                  material=mats["FYNYGRYF_Hull"])
    obj["weapon-emplacement"] = 1
    obj["automated"] = 1
    obj["emplacement-pattern"] = "FLEET"
    obj["blunt-mount"] = 1


def build_floodlights(parent: bpy.types.Collection, mats: dict) -> dict:
    """Floodlights DISABLED - replaced with side lighting on pylons and dragon screens."""
    return {"floodlights": 0}


def build_dragon_coils(parent: bpy.types.Collection, mats: dict) -> dict:
    """Dragon skin coiling around the junction waist.
    
    Coiling bands that wrap around the central connection, creating a dragon-scale
    effect with progressive tightening and rotation. Each coil gets tighter as it
    spirals outward, simulating the dragon's skin tightening around the waist.
    """
    coll = util.ensure_collection("Arcology_Dragon_Coils", parent)
    z0 = util.junction_z()
    rng = random.Random(config.RADIAL_SEED + 11)
    made = {"dragon_coils": 0, "coil_segments": 0}
    
    # Create coiling bands that spiral around the waist
    for coil_index in range(config.DRAGON_COIL_COUNT):
        # Each coil gets progressively tighter
        tightening = config.DRAGON_COIL_TIGHTENING ** coil_index
        # Calculate radius for this coil
        coil_radius = _lerp(config.DRAGON_COIL_INNER_RADIUS, 
                           config.DRAGON_COIL_OUTER_RADIUS, 
                           coil_index / (config.DRAGON_COIL_COUNT - 1))
        
        # Create segments that form the coil band
        segments_per_coil = 28  # base14 * 2 for detailed coiling
        for seg in range(segments_per_coil):
            s = seg / (segments_per_coil - 1)
            
            # Progressive rotation around the waist
            base_rotation = coil_index * config.DRAGON_COIL_ROTATION
            segment_rotation = base_rotation + (s * TAU * 0.5)
            
            # Slight color variation between coils
            color_shift = coil_index * config.DRAGON_COIL_COLOR_SHIFT
            coil_color = max(0.02, min(0.08, 0.035 + color_shift))
            
            # Create the coil segment as a curved band
            # Using torus segments for the coiling effect
            segment_length = (TAU * coil_radius) / segments_per_coil
            segment_width = segment_length * 0.9
            
            # Create a curved band segment
            coil_thickness = config.DRAGON_COIL_THICKNESS * tightening
            coil_height = config.DRAGON_COIL_HEIGHT
            
            # Use box for the coil segment (simplified)
            verts, faces = util.box(segment_length, coil_thickness, coil_height)
            
            # Position the coil segment
            th = segment_rotation
            radius_at_segment = coil_radius
            
            # Add vertical offset for the 3D coiling effect
            z_offset = (s - 0.5) * coil_height * 0.3
            
            obj = util.ensure_mesh_object(
                f"Dragon_Coil_{coil_index + 1:02d}_Seg_{seg:02d}", coll,
                verts, faces, material=mats["FYNYGRYF_DragonCoil"],
                location=(radius_at_segment * math.cos(th), 
                         radius_at_segment * math.sin(th), 
                         z0 + z_offset),
                rotation=(0.0, 0.0, th), shade_smooth=True
            )
            
            obj["dragon-coil"] = 1
            obj["coil-index"] = coil_index
            obj["coil-segment"] = seg
            obj["tightening-factor"] = tightening
            obj["waist-coiling"] = 1
            
            made["coil_segments"] += 1
        made["dragon_coils"] += 1
    
    return made


def build_dragon_screens(parent: bpy.types.Collection, mats: dict) -> dict:
    """Dragon screen bands: non-connected defense vessels extending from ring outward.
    
    Located at 7,000 m across the main disk, extending 7,000 m beyond the ring.
    Whisper-thin dragon-scale shapes in varying dark colors with gold-lit sides.
    One side always brighter and facing away from the city - defense/attack vessels.
    """
    coll = util.ensure_collection("Arcology_Dragon_Screens", parent)
    z0 = util.junction_z()
    rng = random.Random(config.RADIAL_SEED + 9)
    made = {"dragon_screens": 0, "dragon_segments": 0}
    
    for index in range(config.DRAGON_SCREEN_COUNT):
        bearing = _bearing(index) + TAU / (2 * config.DRAGON_SCREEN_COUNT)
        
        # Start at 7,000 m across the ring (49,000 m radius)
        start_radius = config.DRAGON_SCREEN_START_RADIUS
        # Extend 7,000 m beyond ring (63,000 m total)
        end_radius = config.RING_OUTER + config.DRAGON_SCREEN_EXTENSION
        
        # Create multiple segments per screen for the tapered effect
        segments = 14  # base14 number of segments
        for seg in range(segments):
            s = seg / (segments - 1)
            radius = _lerp(start_radius, end_radius, s)
            
            # Density decreases as they extend
            density = config.DRAGON_SCREEN_DENSITY_DECREASE ** seg
            # Height increases as they extend
            height = config.DRAGON_SCREEN_HEIGHT * (config.DRAGON_SCREEN_HEIGHT_INCREASE ** s)
            # Width stays relatively constant but slightly tapers
            width = config.DRAGON_SCREEN_WIDTH * (0.9 + 0.1 * (1.0 - s))
            # Thickness decreases (whisper-thin effect)
            thickness = 20.0 * (config.DRAGON_SCREEN_DENSITY_DECREASE ** seg)
            
            # Dragon-scale shape: simplified box-based structure
            # Varying dark colors
            scale_color = _lerp(0.02, 0.08, rng.random())
            
            # Main scale body using box
            verts, faces = util.box(width, thickness, height)
            
            # Position with slight spread around the bearing
            spread = config.DRAGON_SCREEN_SPREAD * (1.0 + 0.5 * s)
            offset = rng.uniform(-spread, spread)
            th = bearing + offset
            
            # Determine which side faces away from city (outward)
            city_angle = math.atan2(radius * math.sin(th), radius * math.cos(th))
            outward_normal = (math.cos(th), math.sin(th))
            
            obj = util.ensure_mesh_object(
                f"Dragon_Screen_{index + 1:02d}_Seg_{seg:02d}", coll,
                verts, faces, material=mats["FYNYGRYF_DragonArmor"],
                location=(radius * math.cos(th), radius * math.sin(th), z0),
                rotation=(0.0, 0.0, th), shade_smooth=True
            )
            
            obj["dragon-screen"] = 1
            obj["dragon-segment"] = seg
            obj["dragon-bearing"] = index
            obj["defense-vessel"] = 1
            obj["outward-facing"] = 1
            # Add 15% emission to show off FYNYGRYF tower armor
            util.custom_prop(obj, "emission", 0.15)
            
            # Add gold-lit side facing away from city
            gold_material = mats["FYNYGRYF_GoldenThread"]
            # Create a thin gold strip on the outward-facing side
            gold_strip_width = width * 0.1
            gold_verts, gold_faces = util.box(gold_strip_width, height, 20.0)
            gold_offset = width * 0.45  # position at outer edge
            
            gold_obj = util.ensure_mesh_object(
                f"Dragon_Screen_{index + 1:02d}_Seg_{seg:02d}_Gold", coll,
                gold_verts, gold_faces, material=gold_material,
                location=((radius + gold_offset) * math.cos(th),
                         (radius + gold_offset) * math.sin(th), z0),
                rotation=(0.0, 0.0, th), shade_smooth=True
            )
            gold_obj["gold-lit-side"] = 1
            gold_obj["outward-facing"] = 1
            
            made["dragon_segments"] += 1
        made["dragon_screens"] += 1
    
    return made


def build_tendrils(parent: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection("Arcology_Tendrils", parent)
    band_coll = util.ensure_collection("Arcology_Tendril_Bands", coll)
    thread_coll = util.ensure_collection("Arcology_Tendril_Threads", coll)
    guns = util.ensure_collection("Arcology_Emplacements", coll)
    rng = random.Random(config.RADIAL_SEED + 3)
    made = {"tendrils": 0, "tendril_threads": 0, "emplacements": 0}
    width = config.PYLON_WIDTH * config.TENDRIL_WIDTH_SHARE
    for index in range(config.TENDRIL_COUNT):
        boxes, gold, tip = _tendril_chain(index, rng)
        verts, faces = util.merge(boxes)
        obj = util.ensure_mesh_object(
            f"Arcology_Tendril_{index + 1:02d}", band_coll, verts, faces,
            material=mats["FYNYGRYF_DazzleCoat"])
        obj["dazzle-coated"] = 1
        obj["tendril-width-m"] = round(width, 1)
        obj["tendril-modules"] = len(boxes)
        util.custom_prop(obj, "tendril-extend", 0.0)
        made["tendrils"] += 1
        _tendril_gold(f"Arcology_Tendril_Gold_{index + 1:02d}", thread_coll,
                      gold, mats)
        made["tendril_threads"] += 1
        _emplacement(f"Arcology_Emplacement_{index + 1:02d}", guns, tip, mats)
        made["emplacements"] += 1
    made.update(_prime_tendrils(band_coll, thread_coll, guns, mats))
    made["envelope_m3"] = round(envelope_volume(), 0)
    return made


def _prime_tendrils(band_coll, thread_coll, guns, mats) -> dict:
    """The 14 reserved tendrils: one per section, twice the section, red.

    Dead centre of its section horizontally and of the ring height vertically,
    running straight out where the standard tendrils drift, in blood orange
    red because nothing but FLEET, EMBASSY and INTELLIGENCE traffic uses it.
    """
    rng = random.Random(config.RADIAL_SEED + 7)
    scale = config.TENDRIL_PRIME_SCALE
    width = config.PYLON_WIDTH * config.TENDRIL_WIDTH_SHARE * scale
    made = {"prime_tendrils": 0}
    for index in range(config.TENDRIL_PRIME_COUNT):
        boxes, gold, tip = _tendril_chain(index, rng, prime=True)
        verts, faces = util.merge(boxes)
        obj = util.ensure_mesh_object(
            f"Arcology_Tendril_Prime_{index + 1:02d}", band_coll, verts,
            faces, material=mats["FYNYGRYF_PrimeTendril"])
        obj["tendril-prime"] = index + 1
        obj["tendril-reserved-for"] = config.TENDRIL_PRIME_USE
        obj["tendril-width-m"] = round(width, 1)
        obj["tendril-height-m"] = round(config.PYLON_HEIGHT * scale, 1)
        obj["tendril-scale"] = scale
        obj["tendril-modules"] = len(boxes)
        util.custom_prop(obj, "tendril-extend", 0.0)
        _tendril_gold(f"Arcology_Tendril_Prime_Gold_{index + 1:02d}",
                      thread_coll, gold, mats)
        gun = f"Arcology_Emplacement_Prime_{index + 1:02d}"
        _emplacement(gun, guns, tip, mats, scale=scale)
        made["prime_tendrils"] += 1
    return made
