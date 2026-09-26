"""Sovereign Defense Fleet: 56 vessels + 579,194 autonomous bots."""

from __future__ import annotations

import math
import random

import bpy

from . import animation, config, materials, util
from .util import TAU


def _placement(spec: dict, index: int, count: int) -> tuple[tuple, float]:
    """Return (location, yaw) for vessel `index` of `count`."""
    yaw = math.radians(spec.get("yaw", 0.0))
    if "position" in spec:
        return tuple(spec["position"]), yaw
    z = spec.get("z", util.junction_z())
    radius = spec.get("radius", 40_000.0)
    if "angle" in spec:
        th = math.radians(spec["angle"])
    else:
        th = TAU * index / max(1, count)
    if spec.get("spread") == "helix":
        z = util.junction_z() + (index - (count - 1) / 2.0) * 4_000.0
    return ((radius * math.cos(th), radius * math.sin(th), z),
            yaw + th + math.pi / 2.0)


def _hull_mesh(name: str, spec: dict, mat: bpy.types.Material):
    mesh = bpy.data.meshes.get(name)
    profile, power = config.PROFILES[spec["profile"]]
    if mesh is None:
        verts, faces = util.hull(spec["length"], spec["beam"], profile,
                                 power=power, segments=config.HULL_SEGMENTS)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], faces)
        mesh.validate()
        mesh.shade_smooth()
    mesh.materials.clear()
    mesh.materials.append(mat)
    return mesh


def build_vessel(name: str, spec: dict, coll: bpy.types.Collection,
                 mats: dict) -> list[bpy.types.Object]:
    mat = mats[spec["material"]]
    count = spec.get("count", 1)
    objs = []
    if spec.get("sections"):
        # the 210 km flagship is built as named modular sections
        ship_coll = util.ensure_collection(name, coll)
        origin, yaw = _placement(spec, 0, 1)
        cursor = -spec["length"] / 2.0
        for sec_name, sec_len in spec["sections"]:
            profile, power = config.PROFILES[spec["profile"]]
            verts, faces = util.hull(sec_len, spec["beam"], profile,
                                     power=power,
                                     segments=config.HULL_SEGMENTS)
            centre = cursor + sec_len / 2.0
            obj = util.ensure_mesh_object(
                f"{name}_{sec_name}", ship_coll, verts, faces, material=mat,
                location=(origin[0] + centre * math.cos(yaw),
                          origin[1] + centre * math.sin(yaw), origin[2]),
                rotation=(0.0, 0.0, yaw), shade_smooth=True,
            )
            objs.append(obj)
            cursor += sec_len
        return objs

    mesh = _hull_mesh(f"{name}_Hull_Mesh", spec, mat)
    ship_coll = util.ensure_collection(name, coll)
    for i in range(count):
        loc, yaw = _placement(spec, i, count)
        obj_name = name if count == 1 else f"{name}_{i + 1:02d}"
        obj = util.ensure_instance(obj_name, ship_coll, mesh, loc,
                                   rotation=(0.0, 0.0, yaw))
        obj["note"] = spec.get("note", "")
        objs.append(obj)
    return objs


def _sovereign_collection(scene_root: bpy.types.Collection):
    """CIVITAS_FLEET was renamed CIVITAS_FLEET_SOVEREIGN in V3; a rebuild on
    a pre-V3 master renames the existing collection instead of orphaning it."""
    legacy = bpy.data.collections.get(config.LEGACY_FLEET_COLLECTION)
    if legacy is not None and \
            bpy.data.collections.get(config.SOVEREIGN_FLEET_COLLECTION) is None:
        legacy.name = config.SOVEREIGN_FLEET_COLLECTION
    return util.ensure_collection(config.SOVEREIGN_FLEET_COLLECTION,
                                  scene_root)


def build_fleet(scene_root: bpy.types.Collection, mats: dict) -> dict:
    fleet_coll = _sovereign_collection(scene_root)
    stats = {"vessels": 0, "branches": {}}
    hulls = []
    for branch, vessels in config.FLEET.items():
        branch_coll = util.ensure_collection(branch, fleet_coll)
        n = 0
        for name, spec in vessels.items():
            objs = build_vessel(name, spec, branch_coll, mats)
            hulls.extend(objs)
            n += spec.get("count", 1)
        stats["branches"][branch] = n
        stats["vessels"] += n

    # The V2 placeholder is retired: Sen's Maurader is a real vessel now,
    # built by civitas.sen into Branch_Military/Fleet_Sen_Maurader.
    stale = bpy.data.objects.get("Sens_Maurader_RESERVED")
    if stale is not None:
        bpy.data.objects.remove(stale, do_unlink=True)
    reserved = bpy.data.collections.get("Branch_Reserved")
    if reserved is not None and not reserved.all_objects:
        bpy.data.collections.remove(reserved)

    stats["mines"] = build_minefield(fleet_coll, mats)
    stats["bots"] = build_swarms(fleet_coll, mats, hulls)
    return stats


def build_minefield(fleet_coll: bpy.types.Collection, mats: dict) -> int:
    """Thornwall's 2,744 proximity mines, deployed at hour 112 of the week.

    One instancer, 2,744 vertices; hidden until the deployment hour by a
    driver on global-time so the field does not exist before it is laid.
    """
    coll = util.ensure_collection("Branch_TacticalReserve", fleet_coll)
    field = util.ensure_collection("Thornwall_Minefield", coll)
    mesh = bpy.data.meshes.get("Thornwall_Mine_Mesh")
    if mesh is None:
        verts, faces = util.icosphere(config.MINE_DIAMETER / 2.0,
                                      subdivisions=1)
        mesh = bpy.data.meshes.new("Thornwall_Mine_Mesh")
        mesh.from_pydata(verts, [], faces)
        mesh.validate()
    mesh.materials.clear()
    mesh.materials.append(mats["FYNYGRYF_Hull"])
    proto = util.ensure_instance("Thornwall_Mine_Prototype", field, mesh,
                                 (0.0, 0.0, 0.0))
    proto.hide_set(True)
    rng = random.Random(config.SWARM_SEED + 112)
    verts = []
    radius = 100_000.0
    for _ in range(config.THORNWALL_MINES):
        th = TAU * rng.random()
        r = radius * (0.98 + 0.04 * rng.random())
        verts.append((r * math.cos(th), r * math.sin(th),
                      util.junction_z() + (rng.random() - 0.5) * 8_000.0))
    emitter = util.ensure_mesh_object("Thornwall_Mines", field, verts, [])
    emitter.instance_type = "VERTS"
    emitter.show_instancer_for_render = True
    if proto.parent is not emitter:
        proto.parent = emitter
        proto.matrix_parent_inverse.identity()
    emitter["mine-count"] = config.THORNWALL_MINES
    emitter["deploy-hour"] = config.THORNWALL_DEPLOY_HOUR

    ctrl = bpy.data.objects.get(config.ANIMATION_CONTROLLER)
    if ctrl is not None:
        fraction = config.THORNWALL_DEPLOY_HOUR / config.ANIMATION_HOURS
        for path in ("hide_viewport", "hide_render"):
            animation.driver(emitter, path, -1, "g < %f" % fraction,
                             (("g", ctrl, '["global-time"]'),))
    return config.THORNWALL_MINES


# --------------------------------------------------------------------------
# autonomous ecology
# --------------------------------------------------------------------------


def _bot_mesh(name: str, diameter: float, mat: bpy.types.Material,
              subdivisions=1):
    mesh = bpy.data.meshes.get(name)
    if mesh is None:
        verts, faces = util.icosphere(diameter / 2.0,
                                      subdivisions=subdivisions)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], faces)
        mesh.validate()
    mesh.materials.clear()
    mesh.materials.append(mat)
    return mesh


def _emitter(name: str, coll: bpy.types.Collection, radius: float,
             count: int, instance: bpy.types.Object, seed: int,
             centre=(0.0, 0.0, 0.0)):
    """A vertex cloud whose vertices instance `instance` — one object,
    arbitrarily many bots."""
    rng = random.Random(seed)
    verts = []
    for _ in range(count):
        u, v = rng.random(), rng.random()
        theta = TAU * u
        phi = math.acos(2.0 * v - 1.0)
        r = radius * (0.85 + 0.15 * rng.random())
        verts.append((centre[0] + r * math.sin(phi) * math.cos(theta),
                      centre[1] + r * math.sin(phi) * math.sin(theta),
                      centre[2] + r * math.cos(phi)))
    obj = util.ensure_mesh_object(name, coll, verts, [])
    obj.instance_type = "VERTS"
    obj.show_instancer_for_render = True
    if instance.parent is not obj:
        instance.parent = obj
        instance.matrix_parent_inverse.identity()
    obj["bot_count"] = count
    return obj


def build_swarms(fleet_coll: bpy.types.Collection, mats: dict,
                 hulls: list) -> dict:
    coll = util.ensure_collection("Branch_AutonomousEcology", fleet_coll)
    total = 0
    per_class = {}
    for cls, diameter, count, host in config.BOT_CLASSES:
        cls_coll = util.ensure_collection(f"Bots_{cls}", coll)
        mat = mats["FYNYGRYF_Dazzle"] if cls in ("Mote", "Sprite") else \
            mats["FYNYGRYF_Hull"]
        mesh = _bot_mesh(f"Bot_{cls}_Mesh", diameter, mat,
                         subdivisions=1 if diameter < 100.0 else 2)
        proto = util.ensure_instance(f"Bot_{cls}_Prototype", cls_coll, mesh,
                                     (0.0, 0.0, 0.0))
        if cls == "Titan":
            # only 14: place them as real objects on the industrial ring
            for i in range(count):
                th = TAU * i / count
                r = 30_000.0
                util.ensure_instance(
                    f"Bot_Titan_{i + 1:02d}", cls_coll, mesh,
                    (r * math.cos(th), r * math.sin(th),
                     util.junction_z() - 12_000.0))
            proto.hide_set(True)
        else:
            # split the population across a handful of emitters so no single
            # instancer carries more than ~140k verts
            emitters = max(1, min(14, count // 40_000 + 1))
            base, extra = divmod(count, emitters)
            radius = {"Mote": 60_000.0, "Sprite": 90_000.0,
                      "Wisp": 140_000.0, "Guardian": 220_000.0}[cls]
            for e in range(emitters):
                n = base + (1 if e < extra else 0)
                _emitter(f"Bots_{cls}_Emitter_{e:02d}", cls_coll, radius, n,
                         proto, config.SWARM_SEED + e * 97 + len(cls),
                         centre=(0.0, 0.0, util.junction_z()))
        per_class[cls] = count
        total += count
    per_class["total"] = total
    per_class["host_hulls"] = len(hulls)
    return per_class


def build(scene_root: bpy.types.Collection) -> dict:
    mats = materials.all_materials()
    return build_fleet(scene_root, mats)
