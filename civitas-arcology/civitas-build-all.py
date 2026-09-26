"""CIVITAS CITY master build — idempotent, headless.

    blender -b civitasdcity-pre.blend --python civitas-build-all.py -- \
        --out /path/to/out

Running it twice produces the same scene: every object, collection, mesh and
driver is looked up by name before it is created.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from civitas import (anchors, animation, arcology, commercial,  # noqa: E402
                     config, crosssections, fleet, hierarchy, materials, sen,
                     ships, util)


def parse_args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(HERE, "out"))
    p.add_argument("--skip", default="", help="comma separated phase names")
    return p.parse_args(argv)


def scene_root() -> bpy.types.Collection:
    return bpy.context.scene.collection


def main():
    args = parse_args(sys.argv)
    os.makedirs(args.out, exist_ok=True)
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    report = {"blender": bpy.app.version_string, "phases": {}}
    root = scene_root()
    t0 = time.time()

    def phase(name, fn):
        if name in skip:
            report["phases"][name] = "skipped"
            return None
        start = time.time()
        result = fn()
        report["phases"][name] = {"result": result,
                                  "seconds": round(time.time() - start, 1)}
        print(f"[civitas] {name}: {result} ({time.time() - start:.1f}s)")
        return result

    mats = phase("materials", lambda: sorted(materials.all_materials()))
    phase("hierarchy", lambda: hierarchy.organise(root))
    phase("arcology", lambda: arcology.build(root))
    # the controller exists before the fleets so their drivers can bind to it
    phase("controller", lambda: animation.ensure_controller(root).name)
    fleet_stats = phase("fleet", lambda: fleet.build(root))
    phase("ships", lambda: ships.build(root))
    commercial_stats = phase("commercial", lambda: commercial.build(root))
    sen_stats = phase("sen", lambda: sen.build(root))
    animation_stats = phase("animation", lambda: animation.build(root))
    phase("anchors", lambda: anchors.build(root))
    if "crosssections" not in skip:
        phase("crosssections",
              lambda: crosssections.build(root, materials.all_materials()))
    phase("documentation", lambda: hierarchy.write_documentation().name)
    # relink the preview after every collection exists
    phase("preview",
          lambda: animation.ensure_preview_scene(bpy.context.scene).name)
    del mats

    if isinstance(fleet_stats, dict):
        # 56 = 14 x 4: the three crewed branches (54 hulls) plus SC-002 and
        # SC-003, which are vessels in their own right. Sen's Maurader is the
        # greeter, counted separately from the 56 defence hulls.
        report["vessels"] = {
            "branch_hulls": fleet_stats["vessels"],
            "special_craft": ["SC-002 Broadcast", "SC-003 Boarding School"],
            "total": fleet_stats["vessels"] + 2,
            "canonical": 56,
            "bots": fleet_stats["bots"]["total"],
            "bots_canonical": 579_194,
            "thornwall_mines": fleet_stats["mines"],
        }
    if isinstance(commercial_stats, dict):
        report["commercial"] = {
            "vessels": commercial_stats["vessels"],
            "canonical": config.COMMERCIAL_TOTAL,
            "classes": commercial_stats["classes"],
        }
    if isinstance(sen_stats, dict):
        report["sen"] = sen_stats
    if isinstance(animation_stats, dict):
        report["animation"] = animation_stats

    report["objects"] = len(bpy.data.objects)
    report["meshes"] = len(bpy.data.meshes)
    report["collections"] = len(bpy.data.collections)
    report["junction_z"] = util.junction_z()
    report["anchor_count"] = len(anchors.manifest())
    report["scenes"] = [s.name for s in bpy.data.scenes]
    report["frame_end"] = bpy.context.scene.frame_end
    report["seconds"] = round(time.time() - t0, 1)

    master = os.path.join(args.out, config.MASTER_FILENAME)
    bpy.ops.wm.save_as_mainfile(filepath=master)
    report["master"] = master

    with open(os.path.join(args.out, "civitas-build-report.json"), "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    with open(os.path.join(args.out, "civitas-anchor-manifest.txt"), "w") as fh:
        fh.write("\n".join(anchors.manifest()) + "\n")
    print("[civitas] wrote", master)
    print(json.dumps(report, indent=2, default=str)[:4000])


main()
