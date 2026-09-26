"""SC-003 Boarding School, SC-002 Broadcast, and Viola's Ark."""

from __future__ import annotations

import math

import bpy

from . import config, materials, util
from .util import TAU


# --------------------------------------------------------------------------
# SC-003 — the Boarding School (200 km)
# --------------------------------------------------------------------------


def build_school(scene_root: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection("CIVITAS_BOARDING_SCHOOL", scene_root)
    ox, oy, oz = config.SCHOOL_POSITION
    length = config.SCHOOL_LENGTH
    radius = config.SCHOOL_DIAMETER / 2.0
    profile, power = config.PROFILES["station"]

    verts, faces = util.hull(length, config.SCHOOL_DIAMETER, profile,
                             power=power, segments=32)
    util.ensure_mesh_object("SC003_Hull", coll, verts, faces,
                            material=mats["FYNYGRYF_Hull"],
                            location=config.SCHOOL_POSITION,
                            rotation=(0.0, 0.0, math.pi / 2.0),
                            shade_smooth=True)

    # decks every 10 m -> 20,000 plates; represented as sampled deck rings
    decks = util.ensure_collection("SC003_Decks", coll)
    deck_total = int(length / config.SCHOOL_DECK_SPACING)
    drawn = 0
    step = max(1, deck_total // 200)
    for i in range(0, deck_total, step):
        y = oy - length / 2.0 + i * config.SCHOOL_DECK_SPACING
        t = abs((y - oy) / (length / 2.0))
        r = radius * max(0.15, math.sqrt(max(0.0, 1.0 - t ** power)))
        verts, faces = util.annulus(r * 0.35, r, config.FLOOR_SLAB,
                                    segments=48)
        util.ensure_mesh_object(
            f"SC003_Deck_{i:05d}", decks, verts, faces,
            material=mats["FYNYGRYF_Interior"],
            location=(ox, y, oz), rotation=(math.pi / 2.0, 0.0, 0.0))
        drawn += 1

    # great halls every 50 m along the spine
    halls = util.ensure_collection("SC003_Halls", coll)
    hall_mesh = bpy.data.meshes.get("SC003_Hall_Mesh")
    if hall_mesh is None:
        v, f = util.ellipsoid(600.0, 600.0, 300.0, segments=16, rings=8)
        hall_mesh = bpy.data.meshes.new("SC003_Hall_Mesh")
        hall_mesh.from_pydata(v, [], f)
        hall_mesh.validate()
        hall_mesh.shade_smooth()
    hall_mesh.materials.clear()
    hall_mesh.materials.append(mats["FYNYGRYF_AmberCore"])
    hall_total = int(length / config.SCHOOL_HALL_SPACING)
    hall_step = max(1, hall_total // 56)
    halls_drawn = 0
    for i in range(0, hall_total, hall_step):
        y = oy - length / 2.0 + i * config.SCHOOL_HALL_SPACING
        util.ensure_instance(f"SC003_Hall_{i:05d}", halls, hall_mesh,
                             (ox, y, oz))
        halls_drawn += 1

    # 14 km temporal denial / warp field
    field = util.ensure_collection("SC003_TemporalDenialZone", coll)
    v, f = util.icosphere(config.SCHOOL_WARP_RADIUS, subdivisions=3)
    warp_mat = materials.ensure_glass("FYNYGRYF_TemporalDenial")
    obj = util.ensure_mesh_object("SC003_TemporalDenialZone", field, v, f,
                                  material=warp_mat,
                                  location=config.SCHOOL_POSITION,
                                  shade_smooth=True)
    obj.display_type = "TEXTURED"
    obj["radius_m"] = config.SCHOOL_WARP_RADIUS

    util.ensure_text("SC003_Label", coll, "SC-003 BOARDING SCHOOL",
                     (ox, oy, oz + radius + 3_000.0), size=2_400.0,
                     material=mats["Platinum_Pearl"])
    return dict(decks_drawn=drawn, decks_canonical=deck_total,
                halls_drawn=halls_drawn, halls_canonical=hall_total)


# --------------------------------------------------------------------------
# SC-002 — the Broadcast (25 km hull, 56 km antenna array)
# --------------------------------------------------------------------------


def build_broadcast(scene_root: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection("CIVITAS_BROADCAST", scene_root)
    ox, oy, oz = config.BROADCAST_POSITION
    profile, power = config.PROFILES["warship"]
    verts, faces = util.hull(config.BROADCAST_HULL_LENGTH,
                             config.BROADCAST_HULL_BEAM, profile,
                             power=power, segments=28)
    util.ensure_mesh_object("SC002_Hull", coll, verts, faces,
                            material=mats["FYNYGRYF_Hull"],
                            location=config.BROADCAST_POSITION,
                            rotation=(0.0, 0.0, math.pi / 2.0),
                            shade_smooth=True)

    array = util.ensure_collection("SC002_AntennaArray", coll)
    spar_len = config.BROADCAST_ANTENNA_LENGTH / 2.0
    verts, faces = util.cylinder(90.0, spar_len, segments=12,
                                 radius_top=20.0)
    for i in range(config.BROADCAST_SPARS):
        th = TAU * i / config.BROADCAST_SPARS
        r = spar_len / 2.0
        util.ensure_mesh_object(
            f"SC002_Spar_{i + 1:02d}", array, verts, faces,
            material=mats["FYNYGRYF_GoldenThread"],
            location=(ox + r * math.cos(th), oy, oz + r * math.sin(th)),
            rotation=(math.pi / 2.0 - th, 0.0, math.pi / 2.0),
            shade_smooth=True)

    dish_mesh = bpy.data.meshes.get("SC002_Dish_Mesh")
    if dish_mesh is None:
        v, f = util.ellipsoid(1_400.0, 1_400.0, 220.0, segments=24, rings=6)
        dish_mesh = bpy.data.meshes.new("SC002_Dish_Mesh")
        dish_mesh.from_pydata(v, [], f)
        dish_mesh.validate()
        dish_mesh.shade_smooth()
    dish_mesh.materials.clear()
    dish_mesh.materials.append(mats["Platinum_Pearl"])
    for i in range(config.BROADCAST_DISHES):
        th = TAU * i / config.BROADCAST_DISHES
        r = spar_len
        util.ensure_instance(
            f"SC002_Dish_{i + 1:02d}", array, dish_mesh,
            (ox + r * math.cos(th), oy, oz + r * math.sin(th)),
            rotation=(math.pi / 2.0, 0.0, th))

    util.ensure_text("SC002_Label", coll, "SC-002 BROADCAST",
                     (ox, oy, oz + spar_len + 2_000.0), size=2_000.0,
                     material=mats["Platinum_Pearl"])
    return dict(spars=config.BROADCAST_SPARS, dishes=config.BROADCAST_DISHES,
                array_span_m=config.BROADCAST_ANTENNA_LENGTH)


# --------------------------------------------------------------------------
# The Ark — Viola's SR-72 stealth craft (hidden by default)
# --------------------------------------------------------------------------


def build_ark(scene_root: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection("CIVITAS_ARK", scene_root)
    profile, power = config.PROFILES["stealth"]
    verts, faces = util.hull(config.ARK_LENGTH, config.ARK_BEAM, profile,
                             power=power, segments=20, depth_factor=0.30)
    hull = util.ensure_mesh_object("ARK_Hull", coll, verts, faces,
                                   material=mats["FYNYGRYF_Hull"],
                                   location=config.ARK_POSITION,
                                   shade_smooth=True)

    v, f = util.icosphere(config.ARK_CORE_DIAMETER / 2.0, subdivisions=2)
    core = util.ensure_mesh_object("ARK_AmberBackupCore", coll, v, f,
                                   material=mats["FYNYGRYF_AmberCore"],
                                   location=config.ARK_POSITION,
                                   shade_smooth=True)

    v, f = util.icosphere(config.ARK_LENGTH / 2.0 * config.ARK_STEALTH_MARGIN,
                          subdivisions=2)
    stealth_mat = materials.ensure_glass("FYNYGRYF_StealthEnvelope",
                                         color=(0.02, 0.02, 0.03),
                                         alpha=0.05, emission=0.0)
    envelope = util.ensure_mesh_object("ARK_StealthEnvelope", coll, v, f,
                                       material=stealth_mat,
                                       location=config.ARK_POSITION,
                                       shade_smooth=True)

    root = bpy.data.objects.get(materials.ROOT_EMPTY)
    drivers = 0
    for obj in (hull, core, envelope):
        obj.hide_render = True
        obj.hide_viewport = True
        if root is not None:
            drivers += materials.drive_hidden_unless(obj, root, "ark-visible")
    return dict(objects=3, visible=False, drivers=drivers)


def build(scene_root: bpy.types.Collection) -> dict:
    mats = materials.all_materials()
    return {
        "school": build_school(scene_root, mats),
        "broadcast": build_broadcast(scene_root, mats),
        "ark": build_ark(scene_root, mats),
    }
