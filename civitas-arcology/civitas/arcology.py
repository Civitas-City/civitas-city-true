"""FYNYGRYF ARCOLOGY — the Human Ring, grown from the Shaft_L2_L3 junction.

Zone A (Dragon's Back, 11,700 m)  — armoured scales + inhabited floor plates
Zone B (The Last Normalcy, 7,800 m) — 32 spherical nodes on the golden thread
Zone C (Self-Determining Weave, 58,500 m) — 8 spiral rings, 24 -> 8 nodes

The silhouette itself is the three radial systems in `radials`.
"""

from __future__ import annotations

import math
import random

import bpy

from . import config, materials, radials, util
from .util import TAU

ROOT = materials.ROOT_EMPTY


def _ring_radius(index: int, count: int, inner: float, outer: float) -> float:
    """Evenly spaced ring radii, inclusive of both ends."""
    if count == 1:
        return inner
    return inner + (outer - inner) * index / (count - 1)


# --------------------------------------------------------------------------
# root + waist
# --------------------------------------------------------------------------


def build_root(parent_coll: bpy.types.Collection) -> bpy.types.Object:
    z = util.junction_z()
    root = util.ensure_empty(ROOT, parent_coll, (0.0, 0.0, z),
                             kind="SPHERE", size=config.HULL_RADIUS)
    util.custom_prop(root, materials.DAZZLE_PROP, 0.0)
    util.custom_prop(root, "show-cross-sections", 0.0)
    util.custom_prop(root, "ark-visible", 0.0)
    root["arcology-extent-m"] = config.ARCOLOGY_EXTENT
    root["junction-z-m"] = z
    return root


def build_lens(coll: bpy.types.Collection, mats: dict) -> bpy.types.Object:
    """The organic square-to-round merge over the 1,600 m shaft junction."""
    verts, faces = util.square_to_round(
        inner_span=config.JUNCTION_SPAN,
        outer_radius=config.LENS_OUTER,
        height_inner=config.JUNCTION_HEIGHT,
        height_outer=config.JUNCTION_HEIGHT * 3.2,
        steps=10, segments=96,
    )
    return util.ensure_mesh_object(
        "Arcology_Junction_Lens", coll, verts, faces,
        material=mats["FYNYGRYF_Hull"], location=(0.0, 0.0, util.junction_z()),
        shade_smooth=True,
    )


# --------------------------------------------------------------------------
# Zone A — Dragon's Back
# --------------------------------------------------------------------------


def build_zone_a(parent: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection("Zone_A_DragonsBack", parent)
    scales_coll = util.ensure_collection("Zone_A_Scales", coll)
    floors_coll = util.ensure_collection("Zone_A_Floors", coll)
    atria_coll = util.ensure_collection("Zone_A_Atria", coll)
    z0 = util.junction_z()
    counts = dict(scales=0, plates=0, corridors=0, atria=0)

    sx, sy, sz = config.SCALE_SIZE
    scale_mesh = bpy.data.meshes.get("Arcology_Scale_Mesh")
    if scale_mesh is None:
        verts, faces = util.ellipsoid(sx / 2.0, sy / 2.0, sz / 2.0,
                                      segments=16, rings=6)
        scale_mesh = bpy.data.meshes.new("Arcology_Scale_Mesh")
        scale_mesh.from_pydata(verts, [], faces)
        scale_mesh.validate()
        scale_mesh.shade_smooth()
    scale_mesh.materials.clear()
    scale_mesh.materials.append(mats["FYNYGRYF_Hull"])

    for ring in range(config.SCALE_RINGS):
        radius = _ring_radius(ring, config.SCALE_RINGS,
                              config.ZONE_A_INNER + 400.0, config.ZONE_A_OUTER)
        z = z0 + (ring - (config.SCALE_RINGS - 1) / 2.0) * config.SCALE_STAGGER
        offset = TAU / config.SCALES_PER_RING / 2.0 * (ring % 2)
        for i in range(config.SCALES_PER_RING):
            th = TAU * i / config.SCALES_PER_RING + offset
            name = f"Scale_R{ring:02d}_{i:02d}"
            util.ensure_instance(
                name, scales_coll, scale_mesh,
                (radius * math.cos(th), radius * math.sin(th), z),
                rotation=(0.0, 0.0, th + math.pi / 2.0),
            )
            counts["scales"] += 1

    # inhabited floor plates: one annulus per corridor level, per ring band
    for ring in range(config.CORRIDOR_RINGS):
        r_in = _ring_radius(ring, config.CORRIDOR_RINGS,
                            config.ZONE_A_INNER, config.ZONE_A_OUTER)
        r_out = min(config.ZONE_A_OUTER,
                    r_in + config.ZONE_A_DEPTH / config.CORRIDOR_RINGS)
        z = z0 + (ring - (config.CORRIDOR_RINGS - 1) / 2.0) * config.SCALE_STAGGER
        for level in range(config.CORRIDOR_LEVELS):
            zl = z + (level - 1) * config.CORRIDOR_SPACING
            verts, faces = util.annulus(r_in, r_out, config.FLOOR_SLAB,
                                        segments=96)
            util.ensure_mesh_object(
                f"Zone_A_FloorPlate_R{ring:02d}_L{level}", floors_coll,
                verts, faces, material=mats["FYNYGRYF_Interior"],
                location=(0.0, 0.0, zl),
            )
            counts["plates"] += 1

    # radial corridors every 30 m of arc at the mid radius of each band
    corridor_mesh = bpy.data.meshes.get("Arcology_Corridor_Mesh")
    if corridor_mesh is None:
        verts, faces = util.box(config.ZONE_A_DEPTH / config.CORRIDOR_RINGS,
                                6.0, config.FLOOR_HEIGHT)
        corridor_mesh = bpy.data.meshes.new("Arcology_Corridor_Mesh")
        corridor_mesh.from_pydata(verts, [], faces)
        corridor_mesh.validate()
    corridor_mesh.materials.clear()
    corridor_mesh.materials.append(mats["FYNYGRYF_Interior"])

    for ring in range(config.CORRIDOR_RINGS):
        r_in = _ring_radius(ring, config.CORRIDOR_RINGS,
                            config.ZONE_A_INNER, config.ZONE_A_OUTER)
        band = config.ZONE_A_DEPTH / config.CORRIDOR_RINGS
        r_mid = r_in + band / 2.0
        z = z0 + (ring - (config.CORRIDOR_RINGS - 1) / 2.0) * config.SCALE_STAGGER
        spacing = config.CORRIDOR_SPACING
        n = max(1, int(TAU * r_mid / spacing))
        # one corridor per 30 m of circumference is millions of objects at
        # 12 km radius; cap the count per band and record the true pitch.
        step = max(1, n // 256)
        for i in range(0, n, step):
            th = TAU * i / n
            util.ensure_instance(
                f"Zone_A_Corridor_R{ring:02d}_{i:04d}", floors_coll,
                corridor_mesh,
                (r_mid * math.cos(th), r_mid * math.sin(th), z),
                rotation=(0.0, 0.0, th),
            )
            counts["corridors"] += 1

    # atrium voids every 100 m of arc, again decimated for viability
    atrium_mesh = bpy.data.meshes.get("Arcology_Atrium_Mesh")
    if atrium_mesh is None:
        verts, faces = util.box(*config.ATRIUM_SIZE)
        atrium_mesh = bpy.data.meshes.new("Arcology_Atrium_Mesh")
        atrium_mesh.from_pydata(verts, [], faces)
        atrium_mesh.validate()
    atrium_mesh.materials.clear()
    atrium_mesh.materials.append(mats["FYNYGRYF_AmberCore"])

    for ring in range(config.CORRIDOR_RINGS):
        r_in = _ring_radius(ring, config.CORRIDOR_RINGS,
                            config.ZONE_A_INNER, config.ZONE_A_OUTER)
        r_mid = r_in + config.ZONE_A_DEPTH / config.CORRIDOR_RINGS / 2.0
        z = z0 + (ring - (config.CORRIDOR_RINGS - 1) / 2.0) * config.SCALE_STAGGER
        n = max(1, int(TAU * r_mid / config.ATRIUM_SPACING))
        step = max(1, n // 64)
        for i in range(0, n, step):
            th = TAU * i / n
            util.ensure_instance(
                f"Zone_A_Atrium_R{ring:02d}_{i:04d}", atria_coll, atrium_mesh,
                (r_mid * math.cos(th), r_mid * math.sin(th), z),
                rotation=(0.0, 0.0, th),
            )
            counts["atria"] += 1

    return counts


def build_vc_pillars(parent: bpy.types.Collection, mats: dict) -> int:
    """7 VC pillars at the junction, penetrating the first 3 Zone A rings."""
    coll = util.ensure_collection("Zone_A_VC_Pillars", parent)
    z0 = util.junction_z()
    r_pen = _ring_radius(config.VC_PILLAR_PENETRATION_RINGS - 1,
                         config.SCALE_RINGS, config.ZONE_A_INNER + 400.0,
                         config.ZONE_A_OUTER)
    length = r_pen - config.HULL_RADIUS * 0.5
    verts, faces = util.cylinder(config.VC_PILLAR_DIAMETER / 2.0, length,
                                 segments=24)
    for i in range(config.VC_PILLAR_COUNT):
        th = TAU * i / config.VC_PILLAR_COUNT
        r_mid = config.HULL_RADIUS * 0.5 + length / 2.0
        util.ensure_mesh_object(
            f"VC_Pillar_Arcology_{i + 1:02d}", coll, verts, faces,
            material=mats["FYNYGRYF_GoldenThread"],
            location=(r_mid * math.cos(th), r_mid * math.sin(th), z0),
            rotation=(0.0, math.pi / 2.0, th), shade_smooth=True,
        )

    label_mat = mats["Platinum_Pearl"]
    for label, slot in config.VC_MARKERS:
        idx = config.VC_MARKERS.index((label, slot))
        th = TAU * idx / len(config.VC_MARKERS)
        r = config.ZONE_A_INNER + 900.0
        util.ensure_empty(
            f"VC_Marker_{label.split()[0]}", coll,
            (r * math.cos(th), r * math.sin(th), z0 + 200.0 + slot * 120.0),
            kind="SPHERE", size=140.0,
        )
        util.ensure_text(
            f"VC_Label_{label.split()[0]}", coll, label,
            (r * math.cos(th), r * math.sin(th), z0 + 320.0 + slot * 120.0),
            size=180.0, material=label_mat,
        )
    return config.VC_PILLAR_COUNT


# --------------------------------------------------------------------------
# Zone B — The Last Normalcy
# --------------------------------------------------------------------------


def build_zone_b(parent: bpy.types.Collection, mats: dict) -> int:
    coll = util.ensure_collection("Zone_B_LastNormalcy", parent)
    z0 = util.junction_z()
    radius = (config.ZONE_B_INNER + config.ZONE_B_OUTER) / 2.0

    node_mesh = bpy.data.meshes.get("Arcology_ZoneB_Node")
    if node_mesh is None:
        verts, faces = util.icosphere(config.ZONE_B_NODE_DIAMETER / 2.0,
                                      subdivisions=2)
        node_mesh = bpy.data.meshes.new("Arcology_ZoneB_Node")
        node_mesh.from_pydata(verts, [], faces)
        node_mesh.validate()
        node_mesh.shade_smooth()
    node_mesh.materials.clear()
    node_mesh.materials.append(mats["FYNYGRYF_Interior"])

    thread_ring = []
    for i in range(config.ZONE_B_NODES):
        th = TAU * i / config.ZONE_B_NODES
        z = z0 + math.sin(th * 7.0) * 900.0
        pos = (radius * math.cos(th), radius * math.sin(th), z)
        util.ensure_instance(f"Zone_B_Node_{i:02d}", coll, node_mesh, pos)
        thread_ring.append(pos)

    # the golden thread that strings the nodes together
    verts = []
    faces = []
    tube = 14.0
    n = len(thread_ring)
    for i, (x, y, z) in enumerate(thread_ring):
        th = TAU * i / n
        nx, ny = math.cos(th), math.sin(th)
        verts.extend([
            (x, y, z + tube), (x + nx * tube, y + ny * tube, z),
            (x, y, z - tube), (x - nx * tube, y - ny * tube, z),
        ])
    for i in range(n):
        a, b = i * 4, ((i + 1) % n) * 4
        for k in range(4):
            faces.append((a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k))
    util.ensure_mesh_object("Zone_B_GoldenThread", coll, verts, faces,
                            material=mats["FYNYGRYF_GoldenThread"],
                            shade_smooth=True)
    return config.ZONE_B_NODES


# --------------------------------------------------------------------------
# Zone C — The Self-Determining Weave
# --------------------------------------------------------------------------


def build_zone_c(parent: bpy.types.Collection, mats: dict) -> int:
    coll = util.ensure_collection("Zone_C_Weave", parent)
    z0 = util.junction_z()
    rng = random.Random(config.ZONE_C_SEED)

    node_mesh = bpy.data.meshes.get("Arcology_ZoneC_Node")
    if node_mesh is None:
        verts, faces = util.icosphere(config.ZONE_C_NODE_DIAMETER / 2.0,
                                      subdivisions=1)
        node_mesh = bpy.data.meshes.new("Arcology_ZoneC_Node")
        node_mesh.from_pydata(verts, [], faces)
        node_mesh.validate()
        node_mesh.shade_smooth()
    node_mesh.materials.clear()
    node_mesh.materials.append(mats["FYNYGRYF_AmberCore"])

    total = 0
    for ring in range(config.ZONE_C_RINGS):
        radius = _ring_radius(ring, config.ZONE_C_RINGS,
                              config.ZONE_C_INNER, config.ZONE_C_OUTER)
        count = config.ZONE_C_NODES_PER_RING[ring]
        spiral = TAU * ring / config.ZONE_C_RINGS * 0.5
        # the nodes ride inside whichever radial system they fall in, so they
        # stay within the silhouette instead of scattering above the city
        if radius <= config.JUNCTION_OUTER:
            band = config.JUNCTION_DECK_HEIGHT * 0.5
        elif radius <= config.RING_OUTER:
            band = config.RING_HEIGHT * 0.5
        else:
            band = config.RING_HEIGHT * config.TENDRIL_RISE_SHARE
        for i in range(count):
            th = TAU * i / count + spiral
            jitter = rng.uniform(-0.02, 0.02)
            r = radius * (1.0 + jitter)
            util.ensure_instance(
                f"Zone_C_Node_R{ring}_{i:02d}", coll, node_mesh,
                (r * math.cos(th), r * math.sin(th),
                 z0 + rng.uniform(-band, band)),
            )
            total += 1
    return total


# --------------------------------------------------------------------------


def build(scene_root: bpy.types.Collection) -> dict:
    mats = materials.all_materials()
    coll = util.ensure_collection("FYNYGRYF_ARCOLOGY", scene_root)
    root = build_root(coll)
    build_lens(coll, mats)
    stats = build_zone_a(coll, mats)
    stats["vc_pillars"] = build_vc_pillars(coll, mats)
    stats["zone_b_nodes"] = build_zone_b(coll, mats)
    stats["zone_c_nodes"] = build_zone_c(coll, mats)
    stats["legacy_mantle_removed"] = radials.purge_legacy(coll)
    stats.update(radials.build_junction(coll, mats))
    stats.update(radials.build_pylons(coll, mats))
    stats.update(radials.build_ring(coll, mats))
    stats.update(radials.build_tendrils(coll, mats))
    stats.update(radials.build_floodlights(coll, mats))
    stats.update(radials.build_dragon_coils(coll, mats))
    stats.update(radials.build_dragon_screens(coll, mats))
    stats["driven_materials"] = len(materials.wire_dazzle(root))
    materials.keyframe_dazzle_test(root)
    return stats
