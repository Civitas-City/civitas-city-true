"""The Commercial Fleet (Part V): 14 vessels of trade, transport and commerce.

    4 bulk transports    20 km, 784,000 t each
    4 luxury liners       8 km, 38,416 passengers each
    4 couriers            2 km, 10x bulk transit speed
    2 commerce stations  30 km, stationary trade floors at 100 / 150 km

Sovereignty pays for itself: the commercial fleet is a separate hierarchy
from CIVITAS_FLEET_SOVEREIGN, sharing the city but not the chain of command.
"""

from __future__ import annotations

import math

import bpy

from . import config, util
from .util import TAU


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


def _light_pods(name: str, coll: bpy.types.Collection, spec: dict,
                origin, yaw: float, mat: bpy.types.Material):
    """Running lights: one instanced pod mesh, 14 pods a hull."""
    mesh_name = "Commercial_LightPod_%s_Mesh" % spec["profile"]
    mesh = bpy.data.meshes.get(mesh_name)
    radius = max(30.0, spec["beam"] * 0.03)
    if mesh is None:
        verts, faces = util.icosphere(radius, subdivisions=1)
        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(verts, [], faces)
        mesh.validate()
        mesh.shade_smooth()
    mesh.materials.clear()
    mesh.materials.append(mat)
    pods = util.ensure_collection("%s_Lights" % name, coll)
    half = spec["length"] / 2.0
    made = 0
    for i in range(config.COMMERCIAL_LIGHT_PODS):
        t = -half + spec["length"] * i / (config.COMMERCIAL_LIGHT_PODS - 1.0)
        side = spec["beam"] * 0.42 * (1.0 if i % 2 else -1.0)
        x = origin[0] + t * math.cos(yaw) - side * math.sin(yaw)
        y = origin[1] + t * math.sin(yaw) + side * math.cos(yaw)
        util.ensure_instance("%s_Light_%02d" % (name, i + 1), pods, mesh,
                             (x, y, origin[2]))
        made += 1
    return made


def _station(name: str, coll: bpy.types.Collection, spec: dict, origin,
             hull_mat, light_mat) -> dict:
    """A stationary trade floor: core, docking rings, cargo bays."""
    ship = util.ensure_collection(name, coll)
    radius = spec["beam"] / 2.0
    verts, faces = util.icosphere(radius * 0.45, subdivisions=2)
    core = util.ensure_mesh_object("%s_Core" % name, ship, verts, faces,
                                   material=hull_mat, location=origin,
                                   shade_smooth=True)
    for i in range(config.COMMERCIAL_DOCK_RINGS):
        r_out = radius * (0.6 + 0.2 * i)
        verts, faces = util.annulus(r_out * 0.82, r_out, radius * 0.05,
                                    segments=64)
        util.ensure_mesh_object(
            "%s_DockRing_%02d" % (name, i + 1), ship, verts, faces,
            material=hull_mat,
            location=(origin[0], origin[1],
                      origin[2] + (i - 1) * radius * 0.35))
    bays = util.ensure_collection("%s_CargoBays" % name, ship)
    bay_mesh = bpy.data.meshes.get("Commercial_CargoBay_Mesh")
    if bay_mesh is None:
        verts, faces = util.box(radius * 0.30, radius * 0.14, radius * 0.14)
        bay_mesh = bpy.data.meshes.new("Commercial_CargoBay_Mesh")
        bay_mesh.from_pydata(verts, [], faces)
        bay_mesh.validate()
    bay_mesh.materials.clear()
    bay_mesh.materials.append(light_mat)
    for i in range(config.COMMERCIAL_CATEGORIES):
        th = TAU * i / config.COMMERCIAL_CATEGORIES
        r = radius * 0.82
        util.ensure_instance(
            "%s_CargoBay_%02d" % (name, i + 1), bays, bay_mesh,
            (origin[0] + r * math.cos(th), origin[1] + r * math.sin(th),
             origin[2]), rotation=(0.0, 0.0, th))
    core["cargo-bays"] = config.COMMERCIAL_CATEGORIES
    core["docking-rings"] = config.COMMERCIAL_DOCK_RINGS
    return dict(bays=config.COMMERCIAL_CATEGORIES)


def build_commercial(scene_root: bpy.types.Collection, mats: dict) -> dict:
    coll = util.ensure_collection(config.COMMERCIAL_COLLECTION, scene_root)
    stats = {"vessels": 0, "classes": {}, "lights": 0}
    z0 = util.junction_z()

    for cls, spec in config.COMMERCIAL_FLEET.items():
        cls_coll = util.ensure_collection("Fleet_Commercial_%s" % cls, coll)
        hull_mat = mats[spec["material"]]
        light_mat = mats[spec["lights"]]
        count = len(spec["names"])
        for i, name in enumerate(spec["names"]):
            if cls == "Station":
                radius = spec["station_ranges"][i]
                angle = math.radians(spec["station_angles"][i])
                origin = (radius * math.cos(angle), radius * math.sin(angle),
                          z0 + spec["z_offset"])
                _station(name, cls_coll, spec, origin, hull_mat, light_mat)
                obj = bpy.data.objects["%s_Core" % name]
                obj["station-range-m"] = radius
            else:
                angle = math.radians(spec["angle0"]) + TAU * i / count
                origin = (spec["radius"] * math.cos(angle),
                          spec["radius"] * math.sin(angle),
                          z0 + spec["z_offset"])
                yaw = angle + math.pi / 2.0
                mesh = _hull_mesh("%s_Hull_Mesh" % cls, spec, hull_mat)
                ship = util.ensure_collection(name, cls_coll)
                obj = util.ensure_instance(name, ship, mesh, origin,
                                           rotation=(0.0, 0.0, yaw))
                stats["lights"] += _light_pods(name, ship, spec, origin, yaw,
                                               light_mat)
            obj["class"] = cls
            obj["length-m"] = spec["length"]
            obj["note"] = spec["note"]
            if cls == "Bulk":
                obj["capacity-t"] = config.COMMERCIAL_BULK_CAPACITY_T
            elif cls == "Liner":
                obj["passengers"] = config.COMMERCIAL_LINER_PASSENGERS
            elif cls == "Courier":
                obj["speed-factor"] = config.COMMERCIAL_COURIER_SPEED_FACTOR
            stats["vessels"] += 1
        stats["classes"][cls] = count

    label = util.ensure_text(
        "CIVITAS_FLEET_COMMERCIAL_Label", coll, "COMMERCIAL FLEET",
        (0.0, config.COMMERCIAL_FLEET["Bulk"]["radius"], z0 + 14_000.0),
        size=4_200.0, material=mats["Platinum_Pearl"])
    label["vessels"] = stats["vessels"]
    stats["canonical"] = config.COMMERCIAL_TOTAL
    return stats


def build(scene_root: bpy.types.Collection) -> dict:
    from . import materials

    return build_commercial(scene_root, materials.all_materials())
