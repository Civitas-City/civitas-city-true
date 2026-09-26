"""Collection hierarchy, legacy quarantine, and the in-file documentation
text block."""

from __future__ import annotations

import bpy

from . import config, materials, util

CORE = "CIVITAS_CORE_DISKS"
HELIX = "CIVITAS_HELIX_TOWER"
DIAMONDS = "CIVITAS_DIAMONDS"
LEGACY = "CIVITAS_LEGACY_QUARANTINE"
DOC_TEXT = "CIVITAS_DOCUMENTATION"


def organise(scene_root: bpy.types.Collection) -> dict:
    core = util.ensure_collection(CORE, scene_root)
    helix = util.ensure_collection(HELIX, scene_root)
    diamonds = util.ensure_collection(DIAMONDS, scene_root)
    legacy = util.ensure_collection(LEGACY, scene_root)
    legacy.hide_render = True
    legacy.hide_viewport = True

    stats = {"legacy": 0, "helix": 0, "diamonds": 0, "disks": {}}

    for coll_name, prefixes in config.DISK_COLLECTIONS:
        disk_coll = util.ensure_collection(coll_name, core)
        n = 0
        for obj in list(bpy.data.objects):
            if obj.type not in ("MESH", "EMPTY", "FONT"):
                continue
            if obj.name.startswith(config.LEGACY_PREFIXES):
                continue
            if obj.name in config.LEGACY_OBJECTS:
                continue
            if obj.name.startswith(tuple(prefixes)):
                util.move_to_collection(obj, disk_coll)
                n += 1
        stats["disks"][coll_name] = n

    for obj in list(bpy.data.objects):
        if obj.name.startswith(config.LEGACY_PREFIXES) or \
                obj.name in config.LEGACY_OBJECTS:
            util.move_to_collection(obj, legacy)
            obj.hide_render = True
            stats["legacy"] += 1
        elif obj.name.startswith(config.HELIX_PREFIXES):
            util.move_to_collection(obj, helix)
            stats["helix"] += 1
        elif obj.name in config.DIAMOND_OBJECTS or \
                obj.name.endswith(config.DIAMOND_RING_SUFFIXES):
            util.move_to_collection(obj, diamonds)
            stats["diamonds"] += 1

    # anything left in the original catch-all collection stays put but is
    # reported so nothing is silently lost
    stray = []
    for obj in bpy.data.objects:
        if not obj.users_collection:
            util.move_to_collection(obj, scene_root)
            stray.append(obj.name)
    stats["stray"] = stray
    return stats


DOCUMENTATION = """CIVITAS CITY / FYNYGRYF ARCOLOGY — BUILD DOCUMENTATION
=======================================================

CUSTOM PROPERTIES (on {root})
  dazzle-state        0.0 normal, 1.0 dazzle. Drives every FYNYGRYF
                      emission strength to {peak}.
  show-cross-sections 0.0 hidden, 1.0 visible. Drives hide_viewport /
                      hide_render on every object in the five
                      CrossSection_* collections (LayerCollection.exclude
                      carries no animation data and cannot be driven).
  ark-visible         0.0 hidden (default), 1.0 visible. Drives
                      hide_viewport / hide_render on the three ARK objects.
  arcology-extent-m   {extent} — canonical radial extent.
  junction-z-m        World Z of the Shaft_L2_L3 waist the Arcology grows
                      from. The source city is not translated; every
                      addition is anchored to this measured value.

ANIMATION ({controller})
  The canonical week is 168 hours = {frames} frames at {fps} fps. Blender's
  timeline stops at frame {maxframe}, so the week plays back time-compressed
  {compression:.1f}x: {playback} playback frames, one frame = 0.6 s of city
  time. Nothing is lost — every driver is a function of global-time, not of a
  real-time frame number, so the canonical clock is exact.
  global-time         driven from `frame`: (frame % {playback}) / {playback},
                      wrapping 1.0 -> 0.0 with no seam.
  threat-level        keyed at the canonical event hours. Drives Sen's
                      armour, weapons, Temporal Denial Zone, ARK-mode shape
                      key and hull material mix, and the dazzle cascade.
  commercial-activity driven: 0.55 + 0.45 sin(2 pi 14 t). Scales commercial
                      orbit speed and pulses the commercial running lights.
  diplomatic-status   keyed at the reception (hour 24) and salute (hour 126).
  Motion is procedural: every vessel carries driver expressions on its
  location / rotation (orbit, figure eight, lift, shuttle, streak, spin) with
  NOISE and STEPPED f-curve modifiers for patrol jitter, station-keeping
  drift and intercept-drill stepping. Nothing is baked.
  Preview: scene {preview} covers hours 0-{preview_hours} at frame_step
  {preview_step} — {preview_minutes} minutes of playback, sharing the
  master's objects, drivers and materials by collection link.
  Timeline markers name all {events} canonical events of the week.

SEN'S MAURADER (Fleet_Sen_Maurader, under Branch_Military)
  {sen_length:,.0f} m greeter, stationed above the Sovereignty Tower at a
  clearance of {sen_clearance:,.0f} m measured off the real tower / diamond
  bounds, presented {sen_yaw:.0f} degrees outward, riding Sen_Maurader_Pivot
  on a {sen_period:.0f}-hour figure-eight greeting orbit.
  Role: {sen_role}
  Commercial grey outside, void-black woven armour under it (deploys in
  0.14 s), concealed mass drivers / missile racks / prototype time-dilation
  emitters, warm-orange diplomatic decks forward and amber-on-void tactical
  decks aft, a {sen_tdz:,.0f} m Temporal Denial Zone ({sen_tdz_s:.0f} s
  active, {sen_tdz_cd:.0f} s cooldown), and ARK-mode: shape key
  "{sen_key}" plus the Sen_Hull_Transition mix factor, both driven by
  threat-level, so commercial grey becomes crystalline amber, emission falls
  to zero and the backup core pulses every 14 s. Reversible.
  Sen_Fast_Transport keeps its own cradle above the Tower and a 14-minute
  service route, so it stays available while Sen is deployed.

COMMERCIAL FLEET ({commercial})
  14 vessels: 4 bulk transports (20 km, 784,000 t), 4 luxury liners (8 km,
  38,416 passengers), 4 couriers (2 km, 10x transit speed) and 2 commerce
  stations (30 km, at 100 km and 150 km) with turning docking rings.

DRIVERS
  Material emission:  nodes["Principled BSDF"].inputs[Emission Strength]
                      = base + ({peak} - base) * dazzle-state
                      applied to FYNYGRYF_Hull, FYNYGRYF_Interior,
                      FYNYGRYF_AmberCore, FYNYGRYF_GoldenThread.
  Cross sections:     hide_viewport / hide_render = show-cross-sections < 0.5
  Ark:                hide_viewport / hide_render = ark-visible < 0.5
  Dazzle test anim:   frame 1 = 0.0, frame {rise} = 1.0,
                      frame {decay} = 0.0 at {fps} fps; the event hours of
                      the week are keyed into the same action after that.
  Sen ARK-mode:       key_blocks["{sen_key}"].value = threat-level, and the
                      Sen_Hull_Transition Mix Shader factor with it; armour,
                      weapon and TDZ visibility / scale follow the same
                      property, so the transformation reverses by itself.
  Thornwall mines:    2,744 instanced mines hidden until hour 112.

MATERIAL NETWORKS
  Every FYNYGRYF material is a single Principled BSDF -> Material Output.
  Base Color and Emission Color share the canonical hex; Emission Strength
  carries the driver. Warp / stealth volumes use an alpha-blended Principled
  BSDF (FYNYGRYF_TemporalDenial, FYNYGRYF_StealthEnvelope).
{material_table}

DDCC ANCHORS ({anchor_collection})
  Empties, dashes only, resolving the four registry fields:
    radialdisk-NN
    radialdisk-NN-spoke-NN            (14 spokes, Base-14)
    radialdisk-NN-level-NN            (one per source sub-disk mesh)
    radialdisk-NN-level-NN-sector-x   (14 sectors, a..n)
  Positions are derived from real world-space mesh bounds; each anchor
  carries radius-m / z-min-m / z-max-m custom properties.

DECIMATION NOTE
  Canonical counts are stored in config.py and on the objects themselves.
  Where the canonical pitch would produce millions of objects (Zone A
  corridors every 30 m at 12 km radius, 20,000 school decks), the geometry
  is sampled and the canonical total is recorded as a custom property or in
  the build report. No canonical dimension is altered.

THE WEEK IN REVIEW (timeline markers)
{event_table}

LEGACY
  The Old Arrivals Ring (L2_Airport_Ring) and Airport_Truss_00..13 are moved
  to {legacy}, hidden and excluded from render, not deleted.
"""


def write_documentation() -> bpy.types.Text:
    table = "\n".join(
        f"  {name:<24} {spec['hex']}  rough {spec['roughness']:<5}"
        f" metal {spec['metallic']:<4} emit {spec['emission']}"
        for name, spec in config.MATERIALS.items())
    events = "\n".join(
        f"  hour {hour:>6.2f}  {name:<26} {note}"
        for hour, name, note in config.ANIMATION_EVENTS)
    body = DOCUMENTATION.format(
        root=materials.ROOT_EMPTY, peak=config.DAZZLE_PEAK,
        controller=config.ANIMATION_CONTROLLER,
        frames=f"{config.ANIMATION_FRAMES:,}",
        playback=f"{config.PLAYBACK_FRAMES:,}",
        maxframe=f"{config.BLENDER_MAX_FRAME:,}",
        compression=config.TIME_COMPRESSION,
        preview=config.PREVIEW_SCENE, preview_hours=config.PREVIEW_HOURS,
        preview_step=config.PREVIEW_STEP,
        preview_minutes=config.PREVIEW_MINUTES,
        events=len(config.ANIMATION_EVENTS),
        commercial=config.COMMERCIAL_COLLECTION,
        sen_length=config.SEN_LENGTH,
        sen_clearance=config.SEN_TOWER_CLEARANCE,
        sen_yaw=config.SEN_PRESENTATION_YAW,
        sen_period=config.SEN_GREETING_PERIOD_H, sen_role=config.SEN_ROLE,
        sen_tdz=config.SEN_TDZ_RADIUS, sen_tdz_s=config.SEN_TDZ_DURATION_S,
        sen_tdz_cd=config.SEN_TDZ_COOLDOWN_S,
        sen_key=config.SEN_ARK_SHAPE_KEY,
        extent=f"{config.ARCOLOGY_EXTENT:,.0f} m",
        rise=1 + config.DAZZLE_RISE_FRAMES,
        decay=1 + config.DAZZLE_RISE_FRAMES + config.DAZZLE_DECAY_FRAMES,
        fps=config.FPS, material_table=table, event_table=events,
        legacy=LEGACY,
        anchor_collection="CIVITAS-ANCHORS",
    )
    text = bpy.data.texts.get(DOC_TEXT)
    if text is None:
        text = bpy.data.texts.new(DOC_TEXT)
    text.clear()
    text.write(body)
    return text
