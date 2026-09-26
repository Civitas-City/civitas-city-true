"""Export every CIVITAS component as an individual .glb.

    blender -b out/CIVITAS_CITY_MASTER.blend --python civitas-export-all.py \
        -- --out out/glb

glTF 2.0 binary, +Y up (exporter default — Blender is Z-up and the exporter
converts; never override it), modifiers applied, materials + UVs + normals,
Draco level 6, no cameras or lights (the viewer supplies its own).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from civitas import anchors, config, materials  # noqa: E402

EXTRA_EXPORTS = (
    ("CIVITAS_ANCHORS", anchors.ANCHOR_COLLECTION),
    ("CIVITAS_DIAMONDS", "CIVITAS_DIAMONDS"),
)

# The DDCC registry reads anchors as fixed coordinates: never animated.
STATIC_EXPORTS = {"CIVITAS_ANCHORS", "CIVITAS_CROSSSECTIONS"}

MOTION_PATHS = ("location", "rotation_euler", "rotation_quaternion", "scale")


def parse_args(argv):
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(HERE, "out", "glb"))
    p.add_argument("--no-draco", action="store_true")
    p.add_argument("--no-animations", action="store_true")
    p.add_argument("--anim-step", type=int, default=config.EXPORT_ANIM_STEP,
                   help="frames between animation samples; the master clip is "
                        "14,515,200 frames long, so it is sampled, never "
                        "baked frame by frame")
    p.add_argument("--skip-existing", action="store_true",
                   help="leave already-written .glb files alone; resumes an "
                        "interrupted export")
    p.add_argument("--only", nargs="*", default=None, metavar="STEM",
                   help="export just these .glb stems; the manifest and the "
                        "point sidecar are merged into the existing ones "
                        "rather than replacing them")
    p.add_argument("--whole-city", action="store_true",
                   help="also export the entire scene as one .glb")
    return p.parse_args(argv)


def collection_objects(coll: bpy.types.Collection):
    return [o for o in coll.all_objects
            if o.type in ("MESH", "EMPTY", "FONT", "CURVE")]


def moves(obj: bpy.types.Object) -> bool:
    """True if this object's transform is driven or keyed (parents included).

    Sampling a week of animation costs one depsgraph evaluation per object
    per sample, so a static component — the Arcology's five thousand floor
    plates, for instance — must not be exported as an animated clip.
    """
    node = obj
    while node is not None:
        anim = node.animation_data
        if anim is not None:
            for drv in anim.drivers:
                if drv.data_path in MOTION_PATHS:
                    return True
            if anim.action is not None:
                return True
        node = node.parent
    return False


POINTS_FILE = "CIVITAS-INSTANCE-POINTS.json"


class instancers_suspended:
    """Export instancers as prototype + point set, not as realised copies.

    579,194 bots and 2,744 mines are vertex instances of a handful of
    prototype meshes. The glTF exporter realises every instance, which is
    579,194 evaluated meshes: the export is OOM-killed long before it
    writes a file. Suspending `instance_type` exports the prototype mesh
    once and leaves the emitter as a transform node — glTF has no point
    primitive the exporter will write, so a vertex-only emitter mesh is
    dropped and the positions would be lost. They are written to
    CIVITAS-INSTANCE-POINTS.json instead, in the .glb's own +Y-up space,
    and each emitter node carries `instance-count`, `instance-prototype`
    and `instance-points` extras pointing at its entry there. That is the
    form a WebGL viewer wants anyway: one InstancedMesh per emitter.
    """

    def __init__(self, objects):
        self.saved = [(o, o.instance_type) for o in objects
                      if o.instance_type != "NONE"]
        self.points = {}

    @staticmethod
    def _prototype(obj):
        """The mesh each vertex instances: a child, or the collection's own.

        A swarm class shares one prototype between all of its emitters, so
        it sits beside them in the class collection rather than under each.
        """
        proto = next((c for c in obj.children if "Prototype" in c.name), None)
        if proto is not None:
            return proto.name
        for coll in obj.users_collection:
            proto = next((o for o in coll.objects
                          if "Prototype" in o.name), None)
            if proto is not None:
                return proto.name
        return None

    def __enter__(self):
        for obj, _ in self.saved:
            proto = self._prototype(obj)
            mesh = obj.data if obj.type == "MESH" else None
            verts = getattr(mesh, "vertices", ())
            matrix = obj.matrix_world
            # +Y up, matching the exporter's own axis conversion
            self.points[obj.name] = dict(
                prototype=proto,
                count=len(verts),
                positions=[round(c, 3) for v in verts
                           for c in _yup(matrix @ v.co)],
            )
            obj["instance-count"] = len(verts)
            obj["instance-prototype"] = proto or ""
            obj["instance-points"] = POINTS_FILE
            obj.instance_type = "NONE"
        if self.saved:
            bpy.context.view_layer.update()
        return self

    def __exit__(self, *exc):
        for obj, kind in self.saved:
            obj.instance_type = kind
        if self.saved:
            bpy.context.view_layer.update()
        return False


def _yup(v):
    return (v.x, v.z, -v.y)


def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    active = None
    for obj in objects:
        try:
            obj.select_set(True)
        except RuntimeError:
            continue
        active = obj
    if active is not None:
        bpy.context.view_layer.objects.active = active
    return active is not None


def export(path: str, draco: bool, animations: bool = True,
           step: int = config.EXPORT_ANIM_STEP) -> bool:
    kwargs = dict(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_materials="EXPORT",
        export_normals=True,
        export_texcoords=True,
        export_cameras=False,
        export_lights=False,
        export_extras=True,
        export_animations=animations,
    )
    if animations:
        # the week is 14,515,200 frames: sample it, never bake it
        kwargs.update(
            export_animation_mode="SCENE",
            export_frame_range=True,
            export_frame_step=step,
            export_optimize_animation_size=True,
            export_bake_animation=True,
        )
    if draco:
        kwargs.update(
            export_draco_mesh_compression_enable=True,
            export_draco_mesh_compression_level=config.DRACO_LEVEL,
        )
    try:
        bpy.ops.export_scene.gltf(**kwargs)
        return True
    except TypeError as exc:
        # older/newer exporter signatures: drop the unknown keyword and retry
        print(f"[civitas] gltf kwarg mismatch ({exc}); retrying minimal")
        bpy.ops.export_scene.gltf(
            filepath=path, export_format="GLB", use_selection=True,
            export_apply=True, export_cameras=False, export_lights=False)
        return True


def unhide_everything():
    """Hidden objects (cross sections, the Ark) are still exported.

    Their visibility is driver-controlled, so the root flags have to be
    raised first — clearing hide_viewport alone is undone on the next
    depsgraph evaluation.
    """
    root = bpy.data.objects.get(materials.ROOT_EMPTY)
    if root is not None:
        root["show-cross-sections"] = 1.0
        root["ark-visible"] = 1.0
    for view_layer in bpy.context.scene.view_layers:
        _unexclude(view_layer.layer_collection)
    for coll in bpy.data.collections:
        coll.hide_viewport = False
        coll.hide_render = False
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_render = False
    bpy.context.view_layer.update()


def _unexclude(layer):
    layer.exclude = False
    for child in layer.children:
        _unexclude(child)


def merged(path: str, key: str, fresh: dict) -> dict:
    """`fresh` on top of whatever a previous run left in `path`."""
    if not os.path.exists(path):
        return fresh
    with open(path) as fh:
        out = dict(json.load(fh).get(key, {}))
    out.update(fresh)
    return out


def merged_exports(path: str, fresh: list) -> list:
    """A partial run's entries replace their namesakes, order preserved."""
    by_stem = {e["glb"]: e for e in fresh}
    if not os.path.exists(path):
        return fresh
    with open(path) as fh:
        previous = json.load(fh).get("exports", [])
    out = [by_stem.pop(e["glb"], e) for e in previous]
    return out + [e for e in fresh if e["glb"] in by_stem]


def main():
    args = parse_args(sys.argv)
    os.makedirs(args.out, exist_ok=True)
    unhide_everything()
    # anchors and static geometry must not carry a sampled week each
    scene = bpy.context.scene
    print(f"[civitas] animation: frames {scene.frame_start}-"
          f"{scene.frame_end} step {args.anim_step} "
          f"({'off' if args.no_animations else 'on'})")

    manifest = []
    points = {}
    for stem, coll_name in tuple(config.EXPORTS) + EXTRA_EXPORTS:
        if args.only is not None and stem not in args.only:
            continue
        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            print(f"[civitas] MISSING collection {coll_name}; skipped")
            manifest.append(dict(glb=stem, collection=coll_name,
                                 status="missing"))
            continue
        objects = collection_objects(coll)
        if stem == "CIVITAS_ANCHORS":
            objects = [o for o in objects if anchors.is_anchor_name(o.name)]
        if not objects or not select_only(objects):
            manifest.append(dict(glb=stem, collection=coll_name,
                                 status="empty"))
            continue
        path = os.path.join(args.out, f"{stem}.glb")
        done = os.path.getsize(path) if os.path.exists(path) else 0
        if args.skip_existing and done:
            size = done
            manifest.append(dict(glb=f"{stem}.glb", collection=coll_name,
                                 objects=len(objects), bytes=size,
                                 status="ok", skipped=True))
            print(f"[civitas] {stem}.glb  kept  {size:,} bytes")
            continue
        animated = (not args.no_animations and stem not in STATIC_EXPORTS
                    and any(moves(o) for o in objects))
        with instancers_suspended(objects) as instances:
            export(path, not args.no_draco, animated, args.anim_step)
            points.update(instances.points)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        manifest.append(dict(glb=f"{stem}.glb", collection=coll_name,
                             objects=len(objects), bytes=size,
                             status="ok" if size else "failed"))
        manifest[-1]["animated"] = animated
        print(f"[civitas] {stem}.glb  {len(objects)} objects  {size:,} bytes"
              f"  {'animated' if animated else 'static'}")

    if args.whole_city:
        select_only([o for o in bpy.data.objects
                     if o.type in ("MESH", "EMPTY", "FONT", "CURVE")])
        path = os.path.join(args.out, "CIVITAS_CITY_MASTER.glb")
        export(path, not args.no_draco, not args.no_animations,
               args.anim_step)
        manifest.append(dict(glb="CIVITAS_CITY_MASTER.glb",
                             collection="<scene>",
                             bytes=os.path.getsize(path), status="ok"))

    points_path = os.path.join(args.out, POINTS_FILE)
    manifest_path = os.path.join(args.out, "civitas-glb-manifest.json")
    if args.only is not None:
        points = merged(points_path, "emitters", points)
        manifest = merged_exports(manifest_path, manifest)

    if points:
        total = sum(p["count"] for p in points.values())
        with open(points_path, "w") as fh:
            json.dump(dict(up="Y", units="m", emitters=points), fh)
        print(f"[civitas] {POINTS_FILE}  {len(points)} emitters  "
              f"{total:,} instances")

    with open(manifest_path, "w") as fh:
        json.dump(dict(anchors=anchors.manifest(), exports=manifest,
                       instances={k: v["count"] for k, v in points.items()}),
                  fh, indent=2)
    print(json.dumps(manifest, indent=2))


main()
