"""Canonical materials, and the dazzle-state driver cascade."""

from __future__ import annotations

import bpy

from . import config

ROOT_EMPTY = "FYNYGRYF_Arcology_Root"
DAZZLE_PROP = "dazzle-state"


def _socket(node, *names):
    for name in names:
        if name in node.inputs:
            return node.inputs[name]
    return None


def ensure_material(name: str, spec: dict) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)

    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.name = "Principled BSDF"
    bsdf.location = (0, 0)
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    r, g, b = spec["color"]
    _socket(bsdf, "Base Color").default_value = (r, g, b, 1.0)
    _socket(bsdf, "Roughness").default_value = spec["roughness"]
    _socket(bsdf, "Metallic").default_value = spec["metallic"]
    spec_socket = _socket(bsdf, "Specular IOR Level", "Specular")
    if spec_socket is not None:
        spec_socket.default_value = spec["specular"]
    emission_color = _socket(bsdf, "Emission Color", "Emission")
    if emission_color is not None:
        emission_color.default_value = (r, g, b, 1.0)
    _socket(bsdf, "Emission Strength").default_value = spec["emission"]
    subsurface = _socket(bsdf, "Subsurface Weight", "Subsurface")
    if subsurface is not None and spec.get("subsurface"):
        subsurface.default_value = spec["subsurface"]

    mat.diffuse_color = (r, g, b, 1.0)
    mat.roughness = spec["roughness"]
    mat.metallic = spec["metallic"]
    if spec["emission"] > 0.0:
        mat.blend_method = "OPAQUE"
    return mat


def all_materials() -> dict[str, bpy.types.Material]:
    return {name: ensure_material(name, spec)
            for name, spec in config.MATERIALS.items()}


def ensure_glass(name="FYNYGRYF_WarpField", color=(0.957, 0.769, 0.188),
                 alpha=0.1, emission=1.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.name = "Principled BSDF"
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    r, g, b = color
    _socket(bsdf, "Base Color").default_value = (r, g, b, 1.0)
    _socket(bsdf, "Alpha").default_value = alpha
    _socket(bsdf, "Roughness").default_value = 0.1
    emission_color = _socket(bsdf, "Emission Color", "Emission")
    if emission_color is not None:
        emission_color.default_value = (r, g, b, 1.0)
    _socket(bsdf, "Emission Strength").default_value = emission
    mat.blend_method = "BLEND"
    mat.diffuse_color = (r, g, b, alpha)
    return mat


# --------------------------------------------------------------------------
# dazzle state
# --------------------------------------------------------------------------


def _emission_index(bsdf) -> int:
    for i, socket in enumerate(bsdf.inputs):
        if socket.name == "Emission Strength":
            return i
    raise RuntimeError("Principled BSDF has no Emission Strength socket")


def wire_dazzle(root: bpy.types.Object) -> list[str]:
    """Drive every FYNYGRYF emission strength from root["dazzle-state"].

    strength = base + (50 - base) * dazzle-state
    """
    driven = []
    for name in config.DAZZLE_MATERIALS:
        mat = bpy.data.materials.get(name)
        if mat is None or not mat.use_nodes:
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            continue
        index = _emission_index(bsdf)
        path = f'nodes["Principled BSDF"].inputs[{index}].default_value'
        mat.node_tree.animation_data_clear()
        fcurve = mat.node_tree.driver_add(path)
        base = config.MATERIALS[name]["emission"]
        drv = fcurve.driver
        drv.type = "SCRIPTED"
        for var in list(drv.variables):
            drv.variables.remove(var)
        var = drv.variables.new()
        var.name = "dazzle"
        var.type = "SINGLE_PROP"
        target = var.targets[0]
        target.id_type = "OBJECT"
        target.id = root
        target.data_path = f'["{DAZZLE_PROP}"]'
        drv.expression = f"{base} + ({config.DAZZLE_PEAK} - {base}) * dazzle"
        driven.append(name)
    return driven


def drive_hidden_unless(obj: bpy.types.Object, root: bpy.types.Object,
                        prop: str) -> int:
    """hide_viewport / hide_render = root[prop] < 0.5."""
    driven = 0
    for path in ("hide_viewport", "hide_render"):
        try:
            fcurve = obj.driver_add(path)
        except TypeError:
            continue
        drv = fcurve.driver
        drv.type = "SCRIPTED"
        for var in list(drv.variables):
            drv.variables.remove(var)
        var = drv.variables.new()
        var.name = "flag"
        var.type = "SINGLE_PROP"
        target = var.targets[0]
        target.id_type = "OBJECT"
        target.id = root
        target.data_path = f'["{prop}"]'
        drv.expression = "flag < 0.5"
        driven += 1
    return driven


def keyframe_dazzle_test(root: bpy.types.Object):
    """0 -> 1 over 48 frames (<2 s), decaying back over 120 frames (5 s)."""
    scene = bpy.context.scene
    scene.render.fps = config.FPS
    root.animation_data_clear()
    rise = config.DAZZLE_RISE_FRAMES
    decay = config.DAZZLE_DECAY_FRAMES
    keys = ((1, 0.0), (1 + rise, 1.0), (1 + rise + decay, 0.0))
    for frame, value in keys:
        root[DAZZLE_PROP] = value
        root.keyframe_insert(data_path=f'["{DAZZLE_PROP}"]', frame=frame)
    root[DAZZLE_PROP] = 0.0
    scene.frame_start = 1
    scene.frame_end = 1 + rise + decay
    for fcurve in _action_fcurves(root):
        for kp in fcurve.keyframe_points:
            kp.interpolation = "BEZIER"
    return keys


def _action_fcurves(obj: bpy.types.Object) -> list[bpy.types.FCurve]:
    """F-curves of an object's action (Blender 5.x slotted actions)."""
    anim = obj.animation_data
    action = anim.action if anim else None
    if action is None:
        return []
    curves: list[bpy.types.FCurve] = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                curves.extend(bag.fcurves)
    return curves
