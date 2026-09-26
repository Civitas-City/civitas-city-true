"""SEN'S MAURADER (Part VI) — the official greeter of Civitas City.

Sen holds VGM Community Affairs for ARGUS: community development, community
care and worship, with routine worship automated so Sen's own presence goes
where stewardship, escalation and human/VC contact are actually needed.

The vessel reads as a 28 km commercial cruiser in soft grey with white
running lights. Underneath: void-black woven armour that deploys in 0.14 s,
concealed mass drivers, missile racks and prototype time-dilation emitters, a
14 km portable Temporal Denial Zone, and ARK-mode — the commercial plates
eject, the armour closes, emission drops to nothing and a crystalline amber
shell takes over.

Station keeping is derived from the real Sovereignty Tower geometry at build
time (never a hard-coded altitude), 14 km clear of the tower apex and the
Haas Diamond, presented 45 degrees outward for arrivals.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Vector

from . import animation, config, hierarchy, materials, util
from .util import TAU

ROOT_COLLECTION = "Fleet_Sen_Maurader"
SUBCOLLECTIONS = (
    "Sen_Hull_Commercial", "Sen_Hull_Armor", "Sen_Weapons_Concealed",
    "Sen_Weapons_Deployed", "Sen_Diplomatic_Deck", "Sen_Tactical_Deck",
    "Sen_ARK_Mode", "Sen_Temporal_Denial_Zone", "Sen_Fast_Transport",
)
THREAT = '["threat-level"]'


# --------------------------------------------------------------------------
# station keeping, measured off the tower
# --------------------------------------------------------------------------


def tower_apex() -> float:
    """Highest point of the Sovereignty Tower / Zenith spire and its cap."""
    apex = util.junction_z()
    for coll_name in (hierarchy.HELIX, hierarchy.DIAMONDS):
        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            continue
        for obj in coll.all_objects:
            if obj.type != "MESH":
                continue
            apex = max(apex, util.world_bounds(obj)[1].z)
    return apex


def station() -> tuple:
    """(x, y, z) primary station above the tower, and the presentation yaw."""
    apex = tower_apex()
    yaw = math.radians(config.SEN_PRESENTATION_YAW)
    radius = config.SEN_TRANSPORT_CRADLE_OFFSET * 2.0
    return ((radius * math.cos(yaw), radius * math.sin(yaw),
             apex + config.SEN_TOWER_CLEARANCE), yaw + math.pi / 2.0)


# --------------------------------------------------------------------------
# materials unique to Sen
# --------------------------------------------------------------------------


def hull_transition_material(ctrl: bpy.types.Object) -> bpy.types.Material:
    """Commercial grey -> crystalline amber, mixed by threat-level.

    glTF cannot swap a material mid-clip, so the transformation lives in one
    material: two Principled BSDFs into a Mix Shader whose factor is driven.
    """
    name = "Sen_Hull_Transition"
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    grey = tree.nodes.new("ShaderNodeBsdfPrincipled")
    grey.name = "Commercial"
    grey.location = (-300, 200)
    amber = tree.nodes.new("ShaderNodeBsdfPrincipled")
    amber.name = "ARK"
    amber.location = (-300, -200)
    mix = tree.nodes.new("ShaderNodeMixShader")
    mix.name = "ARK Mix"
    mix.location = (0, 0)
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    out.location = (250, 0)
    tree.links.new(grey.outputs["BSDF"], mix.inputs[1])
    tree.links.new(amber.outputs["BSDF"], mix.inputs[2])
    tree.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    def apply(node, spec, emission):
        r, g, b = spec["color"]
        node.inputs["Base Color"].default_value = (r, g, b, 1.0)
        node.inputs["Roughness"].default_value = spec["roughness"]
        node.inputs["Metallic"].default_value = spec["metallic"]
        emit = materials._socket(node, "Emission Color", "Emission")
        if emit is not None:
            emit.default_value = (r, g, b, 1.0)
        node.inputs["Emission Strength"].default_value = emission
        transmission = materials._socket(node, "Transmission Weight",
                                         "Transmission")
        if transmission is not None and spec.get("transmission"):
            transmission.default_value = spec["transmission"]
        ior = materials._socket(node, "IOR")
        if ior is not None and spec.get("ior"):
            ior.default_value = spec["ior"]

    apply(grey, config.MATERIALS["Commercial_Hull"], 0.0)
    apply(amber, config.MATERIALS["ARK_Crystal"],
          config.MATERIALS["ARK_Crystal"]["emission"])

    tree.animation_data_clear()
    animation.driver(tree, 'nodes["ARK Mix"].inputs[0].default_value', -1,
                     "t", (("t", ctrl, THREAT),))
    return mat


def ark_core_material(ctrl: bpy.types.Object) -> bpy.types.Material:
    """The backup amber core: emission 20, pulsing every 14 seconds."""
    name = "Sen_ARK_BackupCore"
    mat = materials.ensure_material(name, dict(
        color=config.MATERIALS["ARK_Crystal"]["color"], roughness=0.2,
        metallic=0.0, specular=0.5, emission=20.0, hex="#F4C430"))
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    index = materials._emission_index(bsdf)
    path = 'nodes["Principled BSDF"].inputs[%d].default_value' % index
    mat.node_tree.animation_data_clear()
    period = animation.frames_of_seconds(14.0)
    animation.driver(
        mat.node_tree, path, -1,
        "20.0 * t * (0.55 + 0.45 * sin(2 * pi * frame / %f))" % period,
        (("t", ctrl, THREAT),))
    return mat


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------


def _visible_when(obj, ctrl, expression):
    for path in ("hide_viewport", "hide_render"):
        animation.driver(obj, path, -1, expression, (("t", ctrl, THREAT),))


def _scaled_by(obj, ctrl, expression, base=1.0):
    for axis in range(3):
        animation.driver(obj, "scale", axis,
                         "%f * (%s)" % (base, expression),
                         (("t", ctrl, THREAT),))


def build_hull(coll, origin, yaw, ctrl, mats) -> bpy.types.Object:
    profile, power = config.PROFILES["warship"]
    verts, faces = util.hull(config.SEN_LENGTH, config.SEN_BEAM, profile,
                             power=power, segments=config.HULL_SEGMENTS,
                             depth_factor=0.55)
    hull = util.ensure_mesh_object(
        "Sen_Maurader", coll, verts, faces,
        material=hull_transition_material(ctrl), location=origin,
        rotation=(0.0, 0.0, yaw), shade_smooth=True)
    hull["length-m"] = config.SEN_LENGTH
    hull["role"] = config.SEN_ROLE
    hull["greeting-period-h"] = config.SEN_GREETING_PERIOD_H
    hull["ark-rebuild-years"] = config.SEN_ARK_REBUILD_YEARS

    # ARK-mode shape key: the commercial plates retract and the hull draws
    # into the tighter crystalline silhouette. Rebuilt every run so the key
    # always matches the current vertex count.
    hull.shape_key_clear()
    basis = hull.shape_key_add(name="Basis", from_mix=False)
    ark = hull.shape_key_add(name=config.SEN_ARK_SHAPE_KEY, from_mix=False)
    scale = config.SEN_ARK_SHELL_SCALE
    half = config.SEN_LENGTH / 2.0
    for i, point in enumerate(basis.data):
        x, y, z = point.co
        taper = 1.0 - 0.35 * abs(x) / half  # bow and stern draw in hardest
        ark.data[i].co = (x * scale, y * scale * taper, z * scale * taper)
    ark.value = 0.0
    ark.slider_min = 0.0
    ark.slider_max = 1.0
    keys = hull.data.shape_keys
    keys.animation_data_clear()
    animation.driver(keys, 'key_blocks["%s"].value' % config.SEN_ARK_SHAPE_KEY,
                     -1, "t", (("t", ctrl, THREAT),))
    del mats
    return hull


def build_armor(coll, origin, yaw, ctrl, mats) -> int:
    """14 void-black woven plates, closed in 0.14 s once threatened."""
    mesh = bpy.data.meshes.get("Sen_ArmorPlate_Mesh")
    if mesh is None:
        verts, faces = util.box(config.SEN_LENGTH / 14.0,
                                config.SEN_BEAM * 0.30,
                                config.SEN_BEAM * 0.06)
        mesh = bpy.data.meshes.new("Sen_ArmorPlate_Mesh")
        mesh.from_pydata(verts, [], faces)
        mesh.validate()
    mesh.materials.clear()
    mesh.materials.append(mats["FYNYGRYF_Hull"])
    made = 0
    for i in range(config.SEN_ARMOR_SEGMENTS):
        t = (i / (config.SEN_ARMOR_SEGMENTS - 1.0) - 0.5) * config.SEN_LENGTH
        side = config.SEN_BEAM * 0.34 * (1.0 if i % 2 else -1.0)
        obj = util.ensure_instance(
            "Sen_Armor_Plate_%02d" % (i + 1), coll, mesh,
            (origin[0] + t * math.cos(yaw) - side * math.sin(yaw),
             origin[1] + t * math.sin(yaw) + side * math.cos(yaw),
             origin[2]), rotation=(0.0, 0.0, yaw))
        # deployment: 0 -> full over the first 0.14 s worth of threat rise
        _scaled_by(obj, ctrl, "min(1.0, t / %f)" % config.SEN_THREAT_ARMOR)
        obj["deploy-seconds"] = 0.14
        made += 1
    return made


def build_weapons(concealed, deployed, origin, yaw, ctrl, mats) -> dict:
    """Mass driver ports, missile racks, time-dilation emitters."""
    port_mesh = bpy.data.meshes.get("Sen_WeaponPort_Mesh")
    if port_mesh is None:
        verts, faces = util.cylinder(config.SEN_BEAM * 0.05,
                                     config.SEN_BEAM * 0.04, segments=12)
        port_mesh = bpy.data.meshes.new("Sen_WeaponPort_Mesh")
        port_mesh.from_pydata(verts, [], faces)
        port_mesh.validate()
    port_mesh.materials.clear()
    port_mesh.materials.append(mats["Commercial_Hull"])

    barrel_mesh = bpy.data.meshes.get("Sen_MassDriver_Mesh")
    if barrel_mesh is None:
        verts, faces = util.cylinder(config.SEN_BEAM * 0.045,
                                     config.SEN_LENGTH * 0.10, segments=12,
                                     radius_top=config.SEN_BEAM * 0.03)
        barrel_mesh = bpy.data.meshes.new("Sen_MassDriver_Mesh")
        barrel_mesh.from_pydata(verts, [], faces)
        barrel_mesh.validate()
    barrel_mesh.materials.clear()
    barrel_mesh.materials.append(mats["FYNYGRYF_Hull"])

    emitter_mesh = bpy.data.meshes.get("Sen_TimeDilationEmitter_Mesh")
    if emitter_mesh is None:
        verts, faces = util.icosphere(config.SEN_BEAM * 0.07, subdivisions=2)
        emitter_mesh = bpy.data.meshes.new("Sen_TimeDilationEmitter_Mesh")
        emitter_mesh.from_pydata(verts, [], faces)
        emitter_mesh.validate()
    emitter_mesh.materials.clear()
    emitter_mesh.materials.append(mats["FYNYGRYF_GoldenThread"])

    counts = {"ports": 0, "mass_drivers": 0, "missile_racks": 0,
              "emitters": 0}
    for i in range(config.SEN_WEAPON_BAYS):
        t = (i / (config.SEN_WEAPON_BAYS - 1.0) - 0.5) * config.SEN_LENGTH \
            * 0.86
        side = config.SEN_BEAM * 0.30 * (1.0 if i % 2 else -1.0)
        x = origin[0] + t * math.cos(yaw) - side * math.sin(yaw)
        y = origin[1] + t * math.sin(yaw) + side * math.cos(yaw)
        z = origin[2] - config.SEN_BEAM * 0.10

        port = util.ensure_instance("Sen_Weapon_Port_%02d" % (i + 1),
                                    concealed, port_mesh, (x, y, z),
                                    rotation=(math.pi / 2.0, 0.0, yaw))
        _visible_when(port, ctrl, "t >= %f" % config.SEN_THREAT_ARMOR)
        counts["ports"] += 1

        if i % 2 == 0:
            gun = util.ensure_instance(
                "Sen_MassDriver_%02d" % (i // 2 + 1), deployed, barrel_mesh,
                (x, y, z), rotation=(math.pi / 2.0, 0.0, yaw))
            _visible_when(gun, ctrl, "t < %f" % config.SEN_THREAT_ARMOR)
            counts["mass_drivers"] += 1
        else:
            rack = util.ensure_instance(
                "Sen_MissileRack_%02d" % (i // 2 + 1), deployed, port_mesh,
                (x, y, z - config.SEN_BEAM * 0.05),
                rotation=(math.pi / 2.0, 0.0, yaw), scale=(2.0, 2.0, 2.0))
            _visible_when(rack, ctrl, "t < %f" % config.SEN_THREAT_ARMOR)
            counts["missile_racks"] += 1

    for i in range(7):
        th = TAU * i / 7.0
        r = config.SEN_BEAM * 0.55
        emitter = util.ensure_instance(
            "Sen_TimeDilationEmitter_%02d" % (i + 1), deployed, emitter_mesh,
            (origin[0] + r * math.cos(th), origin[1] + r * math.sin(th),
             origin[2]))
        _visible_when(emitter, ctrl, "t < %f" % config.SEN_THREAT_ARMOR)
        counts["emitters"] += 1
    return counts


def build_decks(diplomatic, tactical, origin, yaw, mats) -> dict:
    """Warm orange diplomatic decks forward, void-black tactical decks aft."""
    made = {"diplomatic": 0, "tactical": 0}
    for i in range(config.SEN_DECK_COUNT):
        t = (i / (config.SEN_DECK_COUNT - 1.0) - 0.5) * config.SEN_LENGTH * 0.7
        forward = t >= 0.0
        coll = diplomatic if forward else tactical
        mat = mats["FYNYGRYF_Interior"] if forward else mats["FYNYGRYF_Hull"]
        radius = config.SEN_BEAM * 0.40
        verts, faces = util.annulus(radius * 0.25, radius,
                                    config.FLOOR_SLAB * 4.0, segments=32)
        obj = util.ensure_mesh_object(
            "Sen_%s_Deck_%02d" % ("Diplomatic" if forward else "Tactical",
                                  i + 1),
            coll, verts, faces, material=mat,
            location=(origin[0] + t * math.cos(yaw),
                      origin[1] + t * math.sin(yaw), origin[2]))
        obj["deck-lighting"] = "WARM ORANGE" if forward else "AMBER ON VOID"
        made["diplomatic" if forward else "tactical"] += 1
        if not forward:
            lamp_mesh = bpy.data.meshes.get("Sen_AmberLamp_Mesh")
            if lamp_mesh is None:
                v, f = util.icosphere(config.SEN_BEAM * 0.02, subdivisions=1)
                lamp_mesh = bpy.data.meshes.new("Sen_AmberLamp_Mesh")
                lamp_mesh.from_pydata(v, [], f)
                lamp_mesh.validate()
            lamp_mesh.materials.clear()
            lamp_mesh.materials.append(mats["FYNYGRYF_AmberCore"])
            util.ensure_instance(
                "Sen_Tactical_Lamp_%02d" % (i + 1), tactical, lamp_mesh,
                (origin[0] + t * math.cos(yaw), origin[1] + t * math.sin(yaw),
                 origin[2] + config.SEN_BEAM * 0.12))
    return made


def build_ark_mode(coll, origin, ctrl, mats) -> dict:
    """The crystalline amber shell and the amber backup core."""
    radius = config.SEN_BEAM * 0.62
    verts, faces = util.icosphere(radius, subdivisions=3)
    shell = util.ensure_mesh_object(
        "Sen_ARK_CrystalShell", coll, verts, faces,
        material=mats["ARK_Crystal"], location=origin, shade_smooth=True)
    _scaled_by(shell, ctrl, "max(0.001, t)")
    shell["transform-seconds"] = config.SEN_ARK_TRANSFORM_S
    shell["reverse-seconds"] = config.SEN_ARK_REVERSE_S

    verts, faces = util.icosphere(radius * 0.35, subdivisions=2)
    core = util.ensure_mesh_object(
        "Sen_ARK_AmberCore", coll, verts, faces,
        material=ark_core_material(ctrl), location=origin, shade_smooth=True)
    _scaled_by(core, ctrl, "max(0.001, t)")
    core["emission"] = 20.0
    return dict(objects=2, transform_s=config.SEN_ARK_TRANSFORM_S,
                reverse_s=config.SEN_ARK_REVERSE_S)


def build_tdz(coll, origin, ctrl) -> dict:
    """14 km Temporal Denial Zone: scales up in 1 s, 14 s hold, 196 s cool."""
    verts, faces = util.icosphere(config.SEN_TDZ_RADIUS, subdivisions=3)
    mat = materials.ensure_glass("Sen_TemporalDenial", alpha=0.08,
                                 emission=2.0)
    zone = util.ensure_mesh_object("Sen_TemporalDenialZone", coll, verts,
                                   faces, material=mat, location=origin,
                                   shade_smooth=True)
    zone.display_type = "TEXTURED"
    zone["radius-m"] = config.SEN_TDZ_RADIUS
    zone["duration-s"] = config.SEN_TDZ_DURATION_S
    zone["cooldown-s"] = config.SEN_TDZ_COOLDOWN_S
    _scaled_by(zone, ctrl,
               "max(0.001, min(1.0, (t - %f) / 0.05))" % config.SEN_THREAT_ARMOR)
    return dict(radius_m=config.SEN_TDZ_RADIUS,
                duration_s=config.SEN_TDZ_DURATION_S,
                cooldown_s=config.SEN_TDZ_COOLDOWN_S)


def build_fast_transport(coll, origin, yaw, ctrl, mats) -> dict:
    """Sen's own compact transport, cradled above the Tower beside Sen.

    It keeps a 14-minute service route to the Tower and back and stays
    available while the Maurader is deployed, so Sen is never stranded.
    """
    apex = tower_apex()
    cradle_pos = (origin[0] + config.SEN_TRANSPORT_CRADLE_OFFSET
                  * math.cos(yaw),
                  origin[1] + config.SEN_TRANSPORT_CRADLE_OFFSET
                  * math.sin(yaw),
                  origin[2] - config.SEN_BEAM * 0.7)
    verts, faces = util.annulus(config.SEN_TRANSPORT_LENGTH * 0.62,
                                config.SEN_TRANSPORT_LENGTH * 0.80,
                                config.SEN_TRANSPORT_BEAM * 0.5, segments=32)
    cradle = util.ensure_mesh_object(
        "Sen_Transport_Cradle", coll, verts, faces,
        material=mats["FYNYGRYF_Hull"], location=cradle_pos)
    cradle["protected"] = True

    profile, power = config.PROFILES["shuttle"]
    verts, faces = util.hull(config.SEN_TRANSPORT_LENGTH,
                             config.SEN_TRANSPORT_BEAM, profile, power=power,
                             segments=20)
    craft = util.ensure_mesh_object(
        "Sen_Fast_Transport", coll, verts, faces,
        material=mats["Commercial_Hull"], location=cradle_pos,
        rotation=(0.0, 0.0, yaw), shade_smooth=True)
    craft["route-minutes"] = config.SEN_TRANSPORT_ROUTE_MINUTES
    craft["return-target"] = "Sovereignty Tower apex"

    dock = (0.0, 0.0, apex + config.SEN_TRANSPORT_LENGTH)
    animation.shuttle(craft, ctrl, cradle_pos, dock,
                      config.SEN_TRANSPORT_ROUTE_MINUTES / 60.0)
    return dict(cradle=cradle.name, craft=craft.name,
                route_minutes=config.SEN_TRANSPORT_ROUTE_MINUTES,
                dock_z=round(dock[2], 1))


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------


def _parent_to(root_empty: bpy.types.Object, objects, origin) -> int:
    """Rigid assembly: the whole vessel rides one animated empty.

    The parent inverse is built from the known station rather than from
    matrix_world, which is still identity on a freshly created empty until
    the depsgraph catches up — and would silently double every coordinate.
    """
    inverse = Matrix.Translation(-Vector(origin))
    parented = 0
    for obj in objects:
        if obj is root_empty:
            continue
        obj.parent = root_empty
        obj.matrix_parent_inverse = inverse
        parented += 1
    return parented


def build(scene_root: bpy.types.Collection) -> dict:
    mats = materials.all_materials()
    ctrl = bpy.data.objects.get(config.ANIMATION_CONTROLLER)
    if ctrl is None:
        ctrl = animation.ensure_controller(scene_root)

    fleet_coll = util.ensure_collection(config.SOVEREIGN_FLEET_COLLECTION,
                                        scene_root)
    military = util.ensure_collection("Branch_Military", fleet_coll)
    root = util.ensure_collection(ROOT_COLLECTION, military)
    subs = {name: util.ensure_collection(name, root)
            for name in SUBCOLLECTIONS}

    origin, yaw = station()
    pivot = util.ensure_empty("Sen_Maurader_Pivot", root, origin,
                              kind="ARROWS", size=config.SEN_BEAM)
    hull = build_hull(subs["Sen_Hull_Commercial"], origin, yaw, ctrl, mats)
    stats = {
        "station": tuple(round(v, 1) for v in origin),
        "tower_apex_z": round(tower_apex(), 1),
        "presentation_yaw_deg": config.SEN_PRESENTATION_YAW,
        "armor_plates": build_armor(subs["Sen_Hull_Armor"], origin, yaw,
                                    ctrl, mats),
        "weapons": build_weapons(subs["Sen_Weapons_Concealed"],
                                 subs["Sen_Weapons_Deployed"], origin, yaw,
                                 ctrl, mats),
        "decks": build_decks(subs["Sen_Diplomatic_Deck"],
                             subs["Sen_Tactical_Deck"], origin, yaw, mats),
        "ark_mode": build_ark_mode(subs["Sen_ARK_Mode"], origin, ctrl, mats),
        "tdz": build_tdz(subs["Sen_Temporal_Denial_Zone"], origin, ctrl),
        "fast_transport": build_fast_transport(subs["Sen_Fast_Transport"],
                                               origin, yaw, ctrl, mats),
        "role": config.SEN_ROLE,
    }

    label = util.ensure_text(
        "Sen_Maurader_Label", root, "SEN'S MAURADER",
        (origin[0], origin[1], origin[2] + config.SEN_BEAM),
        size=1_400.0, material=mats["Platinum_Pearl"])

    # Everything except the fast transport rides the vessel: the transport
    # keeps its own cradle above the Tower so it stays available while the
    # Maurader is deployed.
    riders = [hull, label]
    for name, sub in subs.items():
        if name == "Sen_Fast_Transport":
            continue
        riders.extend(sub.all_objects)
    stats["parented"] = _parent_to(pivot, riders, origin)

    # The greeting orbit: a 7-hour figure eight above the Tower that speeds to
    # intercept as the threat rises and slows to a 0.1x ghost drift in
    # full ARK-mode.
    pivot.animation_data_clear()
    animation.clear_drivers(pivot)
    animation.orbit(pivot, ctrl, config.SEN_GREETING_PERIOD_H,
                    fallback_radius=config.SEN_TRANSPORT_CRADLE_OFFSET * 2.0,
                    figure_eight=True, speed_prop="threat-level",
                    speed_form="(1 + %s) * (1 - %s ** 24) + 0.1 * %s ** 24")
    stats["shape_key"] = config.SEN_ARK_SHAPE_KEY
    stats["pivot"] = pivot.name
    return stats
