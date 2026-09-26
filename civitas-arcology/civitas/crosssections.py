"""Cross-section bisection: three orthogonal boolean cutters plus five
precomputed cross-section collections with Montserrat floor labels."""

from __future__ import annotations

import bpy

from . import config, materials, util

CUTTERS = (
    # name, normal axis, rotation of the slab
    ("CrossSection_Cutter_X", (1.0, 0.0, 0.0)),
    ("CrossSection_Cutter_Y", (0.0, 1.0, 0.0)),
    ("CrossSection_Cutter_Z", (0.0, 0.0, 1.0)),
)


def build_cutters(parent: bpy.types.Collection) -> list[bpy.types.Object]:
    coll = util.ensure_collection("CrossSection_Cutters", parent)
    e = config.CUTTER_EXTENT
    out = []
    for name, axis in CUTTERS:
        # a half-space slab: the cutter removes everything on +axis
        dims = [e * 2.0, e * 2.0, e * 2.0]
        offset = [0.0, 0.0, 0.0]
        for i, a in enumerate(axis):
            if a:
                dims[i] = e
                offset[i] = e / 2.0
        verts, faces = util.box(*dims)
        obj = util.ensure_mesh_object(name, coll, verts, faces,
                                      location=tuple(offset))
        obj.display_type = "WIRE"
        obj.hide_render = True
        out.append(obj)
    return out


def _boolean(target: bpy.types.Object, cutter: bpy.types.Object, name: str):
    mod = target.modifiers.get(name)
    if mod is None:
        mod = target.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    # the Fast solver was renamed FLOAT in Blender 5.x
    for solver in ("FAST", "FLOAT"):
        try:
            mod.solver = solver
            break
        except TypeError:
            continue
    mod.object = cutter
    return mod


def build_sections(parent: bpy.types.Collection, mats: dict,
                   sources: dict[str, bpy.types.Collection],
                   max_objects: int = 240) -> dict:
    """Precomputed cross sections.

    `sources` maps section name -> collection whose objects are linked into
    the section collection with a boolean cutter applied.
    """
    cutters = {obj.name: obj for obj in build_cutters(parent)}
    stats = {}
    plan = (
        ("CrossSection_Axial", "CrossSection_Cutter_Y"),
        ("CrossSection_Radial", "CrossSection_Cutter_Z"),
        ("CrossSection_ZoneA", "CrossSection_Cutter_Y"),
        ("CrossSection_ZoneB", "CrossSection_Cutter_Y"),
        ("CrossSection_ZoneC", "CrossSection_Cutter_Y"),
    )
    for name, cutter_name in plan:
        coll = util.ensure_collection(name, parent)
        src = sources.get(name)
        n = 0
        if src is not None:
            meshes = [o for o in src.all_objects if o.type == "MESH"]
            step = max(1, len(meshes) // max_objects)
            for obj in meshes[::step]:
                copy_name = f"{name}_{obj.name}"
                copy = bpy.data.objects.get(copy_name)
                if copy is None:
                    copy = bpy.data.objects.new(copy_name, obj.data)
                    coll.objects.link(copy)
                elif copy.name not in coll.objects:
                    util.move_to_collection(copy, coll)
                copy.data = obj.data
                copy.matrix_world = obj.matrix_world.copy()
                _boolean(copy, cutters[cutter_name], "CrossSectionCut")
                n += 1
        stats[name] = n
        coll.hide_render = True
    stats["labels"] = build_floor_labels(
        util.ensure_collection("CrossSection_ZoneA", parent), mats)
    stats["drivers"] = wire_visibility(parent)
    return stats


def build_floor_labels(coll: bpy.types.Collection, mats: dict) -> int:
    """Montserrat labels every 100 m up the Zone A cross section."""
    labels = util.ensure_collection("CrossSection_ZoneA_Labels", coll)
    z0 = util.junction_z()
    spacing = config.FLOOR_LABEL_SPACING
    half = config.ZONE_A_DEPTH / 2.0
    x = config.ZONE_A_INNER + 200.0
    n = 0
    steps = int(config.ZONE_A_DEPTH / spacing)
    for i in range(steps + 1):
        z = z0 - half + i * spacing
        floor = int(round((z - (z0 - half)) / config.FLOOR_HEIGHT))
        util.ensure_text(f"FloorLabel_{i:04d}", labels,
                         f"FLOOR {floor:04d}", (x, 0.0, z),
                         size=40.0, material=mats["Platinum_Pearl"])
        n += 1
    return n


def wire_visibility(parent: bpy.types.Collection) -> int:
    """Drive every cross-section collection's visibility from the root.

    Neither LayerCollection.exclude nor Collection.hide_viewport carries
    animation data, so the drivers live on each section object.
    """
    root = bpy.data.objects.get(materials.ROOT_EMPTY)
    if root is None:
        return 0
    driven = 0
    for name in ("CrossSection_Axial", "CrossSection_Radial",
                 "CrossSection_ZoneA", "CrossSection_ZoneB",
                 "CrossSection_ZoneC"):
        coll = bpy.data.collections.get(name)
        if coll is None:
            continue
        coll.hide_viewport = True
        coll.hide_render = True
        # snapshot: adding drivers invalidates the lazy all_objects iterator
        for obj in list(coll.all_objects):
            obj.hide_viewport = True
            obj.hide_render = True
            driven += materials.drive_hidden_unless(
                obj, root, "show-cross-sections")
    return driven


def build(scene_root: bpy.types.Collection, mats: dict) -> dict:
    parent = util.ensure_collection(config.CROSS_SECTION_COLLECTION, scene_root)
    sources = {}
    mapping = (
        ("CrossSection_Axial", "CIVITAS_CORE_DISKS"),
        ("CrossSection_Radial", "CIVITAS_CORE_DISKS"),
        ("CrossSection_ZoneA", "Zone_A_Floors"),
        ("CrossSection_ZoneB", "Zone_B_LastNormalcy"),
        ("CrossSection_ZoneC", "Zone_C_Weave"),
    )
    for section, source in mapping:
        coll = bpy.data.collections.get(source)
        if coll is not None:
            sources[section] = coll
    return build_sections(parent, mats, sources)
