"""The perpetual motion animation (Part X).

168 hours = 14,515,200 frames at 24 fps, and not one baked keyframe: every
vessel is driven from four custom properties on ANIMATION_CONTROLLER, so the
whole week costs a few hundred drivers instead of tens of millions of keys.

    global-time         driven from `frame`, wraps 1.0 -> 0.0 seamlessly
    threat-level        keyed at the canonical event hours
    commercial-activity driven, a 14-cycle trade rhythm
    diplomatic-status   keyed at the reception and salute hours

Motion primitives, all driver expressions, all functions of global-time:

    orbit       rotation about the city axis at the vessel's own radius, so a
                multi-section hull or a bonded pair keeps its formation and
                sits exactly where the static build put it at global-time 0
    figure8     lemniscate (Mercy, and Sen's greeting orbit)
    lift        nadir-to-zenith continuous loop (Helix shuttles)
    shuttle     linear there-and-back between two points (School Bus)
    streak      one-way repeating transit (couriers)
    spin        yaw only (stations, TR-007, Titans, bot swarms)

NOISE and STEPPED modifiers on the driver curves supply patrol jitter,
station-keeping drift and intercept-drill stepping.
"""

from __future__ import annotations

import math

import bpy

from . import config, materials, util

CONTROLLER = config.ANIMATION_CONTROLLER
# Blender cannot hold 14,515,200 frames in a scene range (MAXFRAME is
# 1,048,574), so the canonical week plays back time-compressed. Every driver
# is a function of global-time, so the canonical 168-hour clock is intact.
TOTAL = config.PLAYBACK_FRAMES
HOURS = float(config.ANIMATION_HOURS)


def frames_of_hours(hours: float) -> float:
    """Playback frames spanning `hours` of city time."""
    return TOTAL * hours / HOURS


def frames_of_seconds(seconds: float) -> float:
    return frames_of_hours(seconds / 3_600.0)


# --------------------------------------------------------------------------
# drivers
# --------------------------------------------------------------------------


def clear_drivers(id_data):
    anim = id_data.animation_data
    if anim is not None:
        for drv in list(anim.drivers):
            anim.drivers.remove(drv)


def driver(id_data, path, index, expression, variables=()):
    """(Re)create one scripted driver. `variables` is (name, id, data_path)."""
    try:
        if index >= 0:
            id_data.driver_remove(path, index)
        else:
            id_data.driver_remove(path)
    except (TypeError, RuntimeError):
        pass
    fcurve = id_data.driver_add(path, index) if index >= 0 \
        else id_data.driver_add(path)
    drv = fcurve.driver
    drv.type = "SCRIPTED"
    for var in list(drv.variables):
        drv.variables.remove(var)
    for name, target_id, data_path in variables:
        var = drv.variables.new()
        var.name = name
        var.type = "SINGLE_PROP"
        target = var.targets[0]
        target.id_type = "OBJECT"
        target.id = target_id
        target.data_path = data_path
    drv.expression = expression
    return fcurve


def ensure_controller(scene_root: bpy.types.Collection) -> bpy.types.Object:
    coll = util.ensure_collection(CONTROLLER, scene_root)
    ctrl = util.ensure_empty(CONTROLLER, coll, (0.0, 0.0, util.junction_z()),
                             kind="SPHERE", size=2_800.0)
    for name, default, note in config.CONTROLLER_PROPS:
        util.custom_prop(ctrl, name, default)
        ctrl[f"{name}-note"] = note
    ctrl["cycle-hours"] = config.ANIMATION_HOURS
    ctrl["cycle-frames-canonical"] = config.ANIMATION_FRAMES
    ctrl["cycle-frames-playback"] = TOTAL
    ctrl["time-compression"] = config.TIME_COMPRESSION
    ctrl["fps"] = config.FPS

    clear_drivers(ctrl)
    ctrl.animation_data_clear()
    # global-time: frame -> [0, 1). Wraps exactly at the end of the week.
    driver(ctrl, '["global-time"]', -1, f"(frame % {TOTAL}) / {TOTAL}")
    # commercial-activity: 14 trade cycles a week, never fully idle.
    driver(ctrl, '["commercial-activity"]', -1,
           f"0.55 + 0.45 * sin(2 * pi * 14 * (frame % {TOTAL}) / {TOTAL})")
    return ctrl


def frame_of(hour: float) -> int:
    return max(1, int(round(frames_of_hours(hour))))


def _cyclic(fcurve):
    for mod in list(fcurve.modifiers):
        if mod.type == "CYCLES":
            fcurve.modifiers.remove(mod)
    fcurve.modifiers.new("CYCLES")


def key_events(ctrl: bpy.types.Object) -> dict:
    """Key threat-level and diplomatic-status at the canonical event hours."""
    for hour, value in config.THREAT_KEYS:
        ctrl["threat-level"] = value
        ctrl.keyframe_insert(data_path='["threat-level"]', frame=frame_of(hour))
    diplomatic = ((0.0, 0.5), (24.0, 1.0), (26.0, 0.5), (56.0, 0.8),
                  (58.0, 0.5), (126.0, 1.0), (128.0, 0.5), (168.0, 0.5))
    for hour, value in diplomatic:
        ctrl["diplomatic-status"] = value
        ctrl.keyframe_insert(data_path='["diplomatic-status"]',
                             frame=frame_of(hour))
    ctrl["threat-level"] = 0.0
    ctrl["diplomatic-status"] = 0.5

    for fcurve in materials._action_fcurves(ctrl):
        for kp in fcurve.keyframe_points:
            kp.interpolation = "BEZIER"
        _cyclic(fcurve)

    markers = bpy.context.scene.timeline_markers
    for hour, name, _note in config.ANIMATION_EVENTS:
        frame = frame_of(hour)
        existing = [m for m in markers if m.name == name]
        if existing:
            existing[0].frame = frame
        else:
            markers.new(name, frame=frame)
    return dict(threat_keys=len(config.THREAT_KEYS),
                diplomatic_keys=len(diplomatic),
                markers=len(config.ANIMATION_EVENTS))


# --------------------------------------------------------------------------
# motion primitives
# --------------------------------------------------------------------------


def _g(ctrl):
    return (("g", ctrl, '["global-time"]'),)


def _turns(period_hours: float) -> float:
    """Circuits completed in one 168-hour cycle."""
    return HOURS / period_hours


def _noise(fcurve, strength: float, scale_frames: float, phase: float):
    for mod in list(fcurve.modifiers):
        if mod.type == "NOISE":
            fcurve.modifiers.remove(mod)
    mod = fcurve.modifiers.new("NOISE")
    mod.strength = strength
    mod.scale = scale_frames
    mod.phase = phase
    mod.depth = 2


def _stepped(fcurve, step: float):
    for mod in list(fcurve.modifiers):
        if mod.type == "STEPPED":
            fcurve.modifiers.remove(mod)
    mod = fcurve.modifiers.new("STEPPED")
    mod.frame_step = step


def _polar(obj, fallback_radius: float):
    """The vessel's own radius / bearing, so nothing is teleported."""
    x, y = obj.location.x, obj.location.y
    radius = math.hypot(x, y)
    if radius < 1.0:
        return fallback_radius, 0.0
    return radius, math.atan2(y, x)


def orbit(obj, ctrl, period_hours, fallback_radius=40_000.0, jitter=0.0,
          eccentric=0.0, figure_eight=False, dash=False, drift=0.0,
          drift_period=2.0, speed_prop="", speed_form="0.5 + %s", seed=0):
    """Rotate about the city axis; global-time 0 is the static placement."""
    radius, bearing = _polar(obj, fallback_radius)
    z = obj.location.z
    yaw = obj.rotation_euler.z
    variables = _g(ctrl)
    turns = _turns(period_hours)
    if speed_prop:
        var_name = speed_prop.replace("-", "")
        variables = variables + ((var_name, ctrl, '["%s"]' % speed_prop),)
        sweep = "2 * pi * %f * g * (%s)" % (
            turns, speed_form.replace("%s", var_name))
    else:
        sweep = "2 * pi * %f * g" % turns
    angle = "(%s + %f)" % (sweep, bearing)

    if figure_eight:
        ex = "%f * sin(%s)" % (radius, angle)
        ey = "%f * sin(%s) * cos(%s)" % (radius * (1.0 - eccentric),
                                         angle, angle)
    else:
        ex = "%f * cos(%s)" % (radius, angle)
        ey = "%f * sin(%s)" % (radius * (1.0 - eccentric), angle)
    fx = driver(obj, "location", 0, ex, variables)
    fy = driver(obj, "location", 1, ey, variables)
    fz = driver(obj, "location", 2, "%f + 0.0 * g" % z, _g(ctrl))
    driver(obj, "rotation_euler", 2, "%s + %f" % (sweep, yaw), variables)

    if jitter:
        for i, fcurve in enumerate((fx, fy, fz)):
            _noise(fcurve, jitter, frames_of_hours(14.0 / 60.0), seed + i)
    if drift:
        for i, fcurve in enumerate((fx, fy, fz)):
            _noise(fcurve, drift, frames_of_hours(drift_period), seed + i)
    if dash:
        for fcurve in (fx, fy, fz):
            _stepped(fcurve, max(2.0, frames_of_seconds(14.0)))
    return 4


def spin(obj, ctrl, period_hours, seed=0):
    yaw = obj.rotation_euler.z
    driver(obj, "rotation_euler", 2,
           "2 * pi * %f * g + %f" % (_turns(period_hours), yaw), _g(ctrl))
    del seed
    return 1


def lift(obj, ctrl, z_low, z_high, period_hours, phase=0.0):
    """Continuous nadir-to-zenith loop: the Helix shuttles never stop."""
    frac = "((%f * g + %f) %% 1.0)" % (_turns(period_hours), phase)
    driver(obj, "location", 2,
           "%f + %f * %s" % (z_low, z_high - z_low, frac), _g(ctrl))
    return 1


def shuttle(obj, ctrl, start, end, period_hours, phase=0.0):
    """There-and-back along a straight line: one round trip per period.

    A cosine ease rather than a triangle wave: Blender's driver namespace has
    the math module but not abs(), and the docking ends want easing anyway.
    """
    t = "(0.5 - 0.5 * cos(2 * pi * (%f * g + %f)))" % (_turns(period_hours),
                                                       phase)
    for axis in range(3):
        a, b = start[axis], end[axis]
        driver(obj, "location", axis, "%f + %f * %s" % (a, b - a, t), _g(ctrl))
    return 3


def streak(obj, ctrl, start, end, period_hours, phase=0.0):
    """One-way repeating transit: couriers cross, reset, cross again."""
    t = "((%f * g + %f) %% 1.0)" % (_turns(period_hours), phase)
    for axis in range(3):
        a, b = start[axis], end[axis]
        driver(obj, "location", axis, "%f + %f * %s" % (a, b - a, t), _g(ctrl))
    heading = math.atan2(end[1] - start[1], end[0] - start[0])
    driver(obj, "rotation_euler", 2, "%f + 0.0 * g" % heading, _g(ctrl))
    return 4


# --------------------------------------------------------------------------
# the sovereign fleet
# --------------------------------------------------------------------------


def targets(name: str) -> list[bpy.types.Object]:
    """Objects for a fleet entry: the hull, its sections, or its copies."""
    obj = bpy.data.objects.get(name)
    if obj is not None:
        return [obj]
    coll = bpy.data.collections.get(name)
    if coll is not None:
        return [o for o in coll.all_objects if o.type in ("MESH", "EMPTY")]
    prefix = "%s_" % name
    return [o for o in bpy.data.objects if o.name.startswith(prefix)]


def animate_sovereign(ctrl) -> dict:
    stats = {"animated": 0, "drivers": 0, "missing": []}
    for name, spec in config.ORBITS.items():
        objs = targets(name)
        if not objs:
            stats["missing"].append(name)
            continue
        for i, obj in enumerate(objs):
            obj.animation_data_clear()
            clear_drivers(obj)
            if "spin" in spec:
                stats["drivers"] += spin(obj, ctrl, spec["spin"])
            elif "lift" in spec:
                low, high = spec["lift"]
                stats["drivers"] += lift(obj, ctrl, low, high, spec["period"],
                                         phase=i / max(1, len(objs)))
            elif "shuttle" in spec:
                stats["drivers"] += shuttle(obj, ctrl, spec["shuttle"],
                                            spec["shuttle_to"], spec["period"])
            else:
                stats["drivers"] += orbit(
                    obj, ctrl, spec["period"],
                    fallback_radius=spec.get("radius", 40_000.0),
                    jitter=spec.get("jitter", 0.0),
                    eccentric=spec.get("eccentric", 0.0),
                    figure_eight=spec.get("figure_eight", False),
                    dash=spec.get("dash", False),
                    drift=spec.get("drift", 0.0),
                    drift_period=spec.get("drift_period", 2.0),
                    seed=i * 14 + len(name))
            stats["animated"] += 1
    return stats


def animate_commercial(ctrl) -> dict:
    """Bulk and liner rings, courier streaks, station rotation."""
    stats = {"animated": 0, "drivers": 0}
    for cls, spec in config.COMMERCIAL_FLEET.items():
        motion = config.COMMERCIAL_ORBITS[cls]
        for i, name in enumerate(spec["names"]):
            if cls == "Station":
                # the trade floor holds station; its docking rings turn
                rings = [o for o in bpy.data.objects
                         if o.name.startswith("%s_DockRing_" % name)]
                for ring_obj in rings:
                    ring_obj.animation_data_clear()
                    clear_drivers(ring_obj)
                    stats["drivers"] += spin(ring_obj, ctrl, motion["spin"])
                stats["animated"] += 1
                continue
            obj = bpy.data.objects.get(name)
            if obj is None:
                continue
            obj.animation_data_clear()
            clear_drivers(obj)
            if cls == "Courier":
                stagger = motion["stagger"] * i / motion["period"]
                start = tuple(obj.location)
                end = (-start[0], -start[1], start[2])
                stats["drivers"] += streak(obj, ctrl, start, end,
                                           motion["period"], phase=stagger)
            else:
                stats["drivers"] += orbit(
                    obj, ctrl, motion["period"],
                    fallback_radius=spec["radius"],
                    speed_prop="commercial-activity", seed=i * 7 + 3)
            stats["animated"] += 1
    stats["light_pulse"] = pulse_commercial_lights(ctrl)
    return stats


def pulse_commercial_lights(ctrl) -> int:
    """Cargo and running lights breathe every 0.14 h (8.4 minutes)."""
    period = frames_of_hours(config.COMMERCIAL_ORBITS["Station"]["pulse"])
    pulsed = 0
    for name in ("Commercial_Lights", "Commercial_Courier_Lights"):
        mat = bpy.data.materials.get(name)
        if mat is None or not mat.use_nodes:
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            continue
        index = materials._emission_index(bsdf)
        path = 'nodes["Principled BSDF"].inputs[%d].default_value' % index
        base = config.MATERIALS[name]["emission"]
        mat.node_tree.animation_data_clear()
        driver(mat.node_tree, path, -1,
               "%f * (0.6 + 0.4 * sin(2 * pi * frame / %f)) * (0.4 + a)"
               % (base, period),
               (("a", ctrl, '["commercial-activity"]'),))
        pulsed += 1
    del ctrl
    return pulsed


# --------------------------------------------------------------------------
# event beacons: the hour-126 array pulse and the Haven warm-up
# --------------------------------------------------------------------------


def _beacon_mesh(name: str, radius: float, material) -> bpy.types.Mesh:
    mesh = bpy.data.meshes.get(name)
    if mesh is None:
        verts, faces = util.icosphere(radius, subdivisions=1)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], faces)
        mesh.validate()
        mesh.shade_smooth()
    mesh.materials.clear()
    mesh.materials.append(material)
    return mesh


def broadcast_pulse(ctrl) -> int:
    """A light runs out along each of the 14 spars, surging at hour 126.

    glTF has no way to animate emission, so the pulse is a moving emissive
    body rather than a material effect: it reads the same in Blender and in
    the viewer. It idles at a slow 14-hour breath and, in the hour around
    the Broadcast test, sprints the full 28 km half-span every 14 minutes.
    """
    array = bpy.data.collections.get("SC002_AntennaArray")
    mat = bpy.data.materials.get("FYNYGRYF_Dazzle")
    if array is None or mat is None:
        return 0
    ox, oy, oz = config.BROADCAST_POSITION
    span = config.BROADCAST_ANTENNA_LENGTH / 2.0
    mesh = _beacon_mesh("SC002_Pulse_Mesh", 420.0, mat)
    idle, test = _turns(14.0), _turns(14.0 / 60.0)
    window = config.BROADCAST_TEST_HOUR / HOURS
    made = 0
    for i in range(config.BROADCAST_SPARS):
        th = 2.0 * math.pi * i / config.BROADCAST_SPARS
        obj = util.ensure_instance(f"SC002_Pulse_{i + 1:02d}", array, mesh,
                                   (ox, oy, oz))
        obj.animation_data_clear()
        clear_drivers(obj)
        # a raised-cosine window centred on the test hour, 1 hour wide
        gate = ("(0.18 + 0.82 * exp(-pow((g - %f) * %f, 2)))"
                % (window, HOURS * 2.0))
        travel = ("((0.5 - 0.5 * cos(2 * pi * (%f * g + %f))) * %s)"
                  % (test, i / config.BROADCAST_SPARS, gate))
        idle_travel = "(0.5 - 0.5 * cos(2 * pi * %f * g))" % idle
        reach = "%f * (0.25 * %s + 0.75 * %s)" % (span, idle_travel, travel)
        for index, expr in enumerate((
                "%f + %s * %f" % (ox, reach, math.cos(th)),
                "%f" % oy,
                "%f + %s * %f" % (oz, reach, math.sin(th)))):
            driver(obj, "location", index, expr,
                   (("g", ctrl, '["global-time"]'),))
        made += 1
    return made


def haven_warmup(ctrl) -> int:
    """Both Haven vessels spool their engines every 7 hours, at the school.

    Scale, not emission: a halo that swells to 1.4x and settles, so the
    warm-up survives the .glb export the same way the pulse does.
    """
    mat = bpy.data.materials.get("FYNYGRYF_GoldenThread")
    if mat is None:
        return 0
    mesh = _beacon_mesh("Haven_Warmup_Mesh", 700.0, mat)
    period = _turns(config.HAVEN_WARMUP_HOURS)
    made = 0
    for i, name in enumerate(("Haven_01", "Haven_02")):
        haven = bpy.data.objects.get(name)
        if haven is None:
            continue
        coll = haven.users_collection[0] if haven.users_collection else None
        if coll is None:
            continue
        x, y, z = haven.location
        obj = util.ensure_instance(f"{name}_Warmup", coll, mesh,
                                   (x, y - 5_400.0, z))
        obj.animation_data_clear()
        clear_drivers(obj)
        swell = ("(0.35 + 1.05 * pow(0.5 - 0.5 * cos(2 * pi * (%f * g + %f)),"
                 " 6))" % (period, i * 0.5))
        for index in range(3):
            driver(obj, "scale", index, swell,
                   (("g", ctrl, '["global-time"]'),))
        made += 1
    return made


# --------------------------------------------------------------------------
# dazzle, and the preview cut
# --------------------------------------------------------------------------


def dazzle_cascade(root: bpy.types.Object) -> int:
    """dazzle-state follows the event threat curve after the 48/120 self test.

    The property carries keyframes rather than a driver so the dazzle test
    (0 -> 1 over 48 frames, back to 0 over 120) survives intact at the head
    of the week; the event hours are keyed into the same action.
    """
    keys = 0
    settle = 1 + config.DAZZLE_RISE_FRAMES + config.DAZZLE_DECAY_FRAMES
    for hour, value in config.THREAT_KEYS:
        frame = frame_of(hour)
        if frame <= settle:
            continue
        root[materials.DAZZLE_PROP] = value
        root.keyframe_insert(data_path='["%s"]' % materials.DAZZLE_PROP,
                             frame=frame)
        keys += 1
    root[materials.DAZZLE_PROP] = 0.0
    for fcurve in materials._action_fcurves(root):
        _cyclic(fcurve)
    return keys


def ensure_preview_scene(master: bpy.types.Scene) -> bpy.types.Scene:
    """A 14-minute review cut: hours 0-14, every 60th frame.

    The preview links the master collections rather than copying them, so it
    shares every object, driver and material with the master scene.
    """
    scene = bpy.data.scenes.get(config.PREVIEW_SCENE)
    if scene is None:
        scene = bpy.data.scenes.new(config.PREVIEW_SCENE)
    for child in list(scene.collection.children):
        scene.collection.children.unlink(child)
    for child in master.collection.children:
        scene.collection.children.link(child)
    scene.render.fps = config.FPS
    scene.frame_start = 1
    scene.frame_end = config.PREVIEW_FRAMES
    scene.frame_step = config.PREVIEW_STEP
    scene["preview-hours"] = config.PREVIEW_HOURS
    scene["preview-minutes"] = config.PREVIEW_MINUTES
    scene["rendered-frames"] = config.PREVIEW_FRAMES // config.PREVIEW_STEP
    return scene


def sample_global_time(ctrl: bpy.types.Object, frames) -> list:
    """Evaluate the global-time driver at given frames (loop verification)."""
    scene = bpy.context.scene
    original = scene.frame_current
    out = []
    for frame in frames:
        scene.frame_set(int(frame))
        out.append((int(frame), round(ctrl["global-time"], 9)))
    scene.frame_set(original)
    return out


def build(scene_root: bpy.types.Collection) -> dict:
    scene = bpy.context.scene
    scene.render.fps = config.FPS
    ctrl = ensure_controller(scene_root)
    events = key_events(ctrl)
    sovereign = animate_sovereign(ctrl)
    commercial = animate_commercial(ctrl)

    pulses = broadcast_pulse(ctrl)
    warmups = haven_warmup(ctrl)

    root = bpy.data.objects.get(materials.ROOT_EMPTY)
    dazzle_keys = dazzle_cascade(root) if root is not None else 0

    scene.frame_start = 1
    scene.frame_end = TOTAL
    preview = ensure_preview_scene(scene)
    loop = sample_global_time(ctrl, (1, TOTAL // 2, TOTAL, TOTAL + 1))
    return dict(controller=ctrl.name, frames_canonical=config.ANIMATION_FRAMES,
                frames_playback=TOTAL,
                time_compression=config.TIME_COMPRESSION,
                hours=config.ANIMATION_HOURS, events=events,
                sovereign=sovereign, commercial=commercial,
                broadcast_pulses=pulses, haven_warmups=warmups,
                dazzle_event_keys=dazzle_keys, preview=preview.name,
                preview_frames=preview["rendered-frames"], loop=loop)
