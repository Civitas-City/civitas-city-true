# CIVITAS CITY — FYNYGRYF ARCOLOGY BUILD SYSTEM

Idempotent, headless Blender 5.1.1 build of Civitas City: the FYNYGRYF
Arcology (the Human Ring), the Sovereign Defense Fleet, the Commercial
Fleet, Sen's Maurader, SC-003 Boarding School, SC-002 Broadcast, the Ark,
cross-section bisection, the 168-hour perpetual-motion animation and the
DDCC coordinate anchors — plus per-component glTF Binary export.

## Requirements

- Blender 5.1.1 (`blender` on PATH or an absolute path to the executable)
- Montserrat: `./fetch-montserrat.sh` (installs to `~/.fonts`)

## Build

```bash
blender -b civitasdcity-pre.blend --python civitas-build-all.py -- \
  --out /path/to/out
```

Writes `CIVITAS_CITY_MASTER.blend`, `civitas-build-report.json` and
`civitas-anchor-manifest.txt`. The build is idempotent: running it against
its own output produces identical object, mesh, collection and anchor
counts, so it can be re-run after edits without duplicating geometry.

## Export

```bash
blender -b out/CIVITAS_CITY_MASTER.blend --python civitas-export-all.py -- \
  --out out/glb
```

One `.glb` per major component plus `civitas-glb-manifest.json`. Settings
are glTF Binary, +Y up, apply modifiers, Draco compression, materials,
normals and UVs; cameras and lights are excluded. Driver-hidden content
(cross sections, the Ark) is force-shown for export.

Animated components are detected per collection (a transform driver or
action on the object or any parent) and exported as a sampled clip, one
sample every `--anim-step` frames; static components carry no clip.

579,194 bots and 2,744 mines are vertex instances of a few prototype
meshes, and the glTF exporter realises every instance — 579,194 evaluated
meshes, which the kernel OOM-kills before a file is written. The exporter
instead suspends `instance_type` for the run, so each emitter exports as
its prototype plus a transform node, and writes the point sets to
`CIVITAS-INSTANCE-POINTS.json` in the `.glb`'s own +Y-up metres. Each
emitter node carries `instance-count`, `instance-prototype` and
`instance-points` extras pointing at its entry, which is the form a WebGL
viewer wants anyway: one `InstancedMesh` per emitter.

`--skip-existing` leaves already-written files alone and resumes an
interrupted export, but the point sidecar only covers the collections
exported in that run.

## The 168-hour animation

```text
canonical week   168 h = 604,800 s = 14,515,200 frames at 24 fps
playback         1,008,000 frames (Blender's timeline caps at 1,048,574)
compression      14.4x — one playback frame = 0.6 s of city time
```

The canonical clock is not approximated: `ANIMATION_CONTROLLER` publishes
`global-time` as `(frame % 1008000) / 1008000`, and every motion is a
function of that normalised 0..1 position in the week, not of a frame
number. `cycle-frames-canonical`, `cycle-frames-playback` and
`time-compression` are custom properties on the controller, so a viewer
(or the WebGL ambient build) can map UTC to `global-time` directly and get
the canonical 168-hour cycle back.

Motion is procedural — driver expressions on location/rotation plus NOISE,
STEPPED and CYCLES f-curve modifiers. Nothing is baked; the only keyframes
in the scene are the event curves on `threat-level`, `diplomatic-status`
and `dazzle-state`, and the timeline markers naming all 17 canonical
events of the week. `CIVITAS-PREVIEW-14MIN` links the same collections at
frame step 4 for a 14-minute review cut of hours 0-14.

| Controller property | Effect |
| --- | --- |
| `global-time` | 0..1 position in the week; drives every motion |
| `threat-level` | armour, weapon bays, TDZ, ARK-mode, dazzle cascade |
| `commercial-activity` | commercial orbit speed and running-light pulse |
| `diplomatic-status` | greeting protocols and reception postures |

Two events are carried by moving emissive bodies rather than by animated
emission, which glTF cannot express: `SC002_Pulse_01`-`14` run out along
the 56 km array, idling on a 14-hour breath and sprinting the full 28 km
half-span every 14 minutes through the hour-126 Broadcast test; and
`Haven_01_Warmup`/`Haven_02_Warmup` swell to 1.4x on each vessel's
7-hour engine spool at the school.

## DDCC coordinate contract

The registry resolves four spatial fields per artifact by named node, never
by hardcoded position. Anchors are empties (no geometry cost, movable
without touching a mesh) in the `CIVITAS-ANCHORS` collection, named with
dashes only:

```text
radialdisk-01
radialdisk-01-spoke-04
radialdisk-01-level-03
radialdisk-01-level-03-sector-b
```

Each radial disk has 14 spokes and 14 sectors per level (base-14), with
levels generated from measured 280 m modules (20 floors at 14 m pitch)
rather than a fixed level count. The top module absorbs any remainder, and
each level exports `module-floors`, `floor-first`, `floor-last`, `radius-m`,
`z-min-m`, `z-max-m` and `source-object` custom properties as glTF extras.
The `radialdisk-helix` ladder covers the Tower and Zenith segments
continuously as levels 01-186; the middle span between them is intentionally
not a module. The helix root has 14 spokes, and each helix level carries a
`segment` extra of `tower` or `zenith`.

## The Dragon's Protection (Arcology silhouette)

The old Arrivals Ring never cut Civitas City in half, because it was carried
on skinny pylons and you saw the city through it. `civitas/radials.py` keeps
that lesson and makes the pylons substantial and habitable instead of dainty —
the Arcology is a warship that can put itself between the city and an attack,
and the open sky between its pylons is the whole design:

```text
Arcology_Junction   lens -> +7,000 m. A solid disk exactly the height of the
                    existing connection (250 m): 11 full floors and one
                    three-quarter data & utility conduit. 14 tapered cutaways
                    point at the pylons, walled in glass and lipped in gold.
                    GRAND CENTRAL is the transit hall inside it: a ring of
                    platforms with one concourse per pylon bearing, so a
                    transport off the ring runs its pylon and arrives here
Arcology_Pylons     -> 42,000 m (14 x 3 km). 14 habitable pylons, each two of
                    the ring's window-bay modules wide (`PYLON_MODULES`) and
                    carrying the same 11 floors and three-quarter conduit as
                    the disk — one domain per RAD02-RAD04 entity, four transit
                    lanes running through to GRAND CENTRAL. They leave the disk
                    through a graceful arc, are clad in dragon scales, and
                    carry the private subway tubes top and bottom
Arcology_Ring       42,000 -> 56,000 m, the 14 km transformation zone at
                    double the pylon height (500 m). Inner half dragon scale,
                    outer half dazzle plate; 28 large and 84 small landing
                    zones split evenly between the reception face above and
                    the industrial face below; an arrivals ring on each face;
                    its own 14 cutaways; glazed window bays in the outer
                    rings; and the 14 diamonds resuming their vigil, each on
                    the measured bearing of the pillar cap it answers to
Arcology_Tendrils   56,000 m -> extent. 98 chains of structural boxes half a
                    pylon across, each one carried outward off a ring bay's own
                    rectangle, tapering and stepping through short collars as
                    it goes. Every second bay grows (twice: once off the upper
                    deck edge, once off the lower), and the bays left bare are
                    the room the ecosystem grows into later. They never
                    reconnect to the Arcology — they always reach outward —
                    every surface is dazzle coated, gold lines run the length
                    of every box, each tip is an automated defensive
                    emplacement, and no chain rises more than half the ring
                    height above the ring
Zone_C_Weave        the 128 canonical nodes, kept inside the silhouette
```

Disorder is a *rim* story: scale wobble, band curl and swirl all scale with
`_radial_t()` or the run fraction, so geometry leaving the junction is formal
and only breaks up as it travels out. Every random draw comes from
`RADIAL_SEED`, so a rebuild reproduces the same dragon. Each tendril carries
`dazzle-coated`, `tendril-width-m`, `tendril-modules` and a driven
`tendril-extend` property — the light defensive posture, where a chain reaches
out to meet an attack. Each pylon carries `habitable`, `pylon-domain`,
`domain-architecture`, `floors`, `conduit-decks`, `transit-lanes` and
`transit-terminus`.

On air, heat and water: the junction disk and the ring are closed solids,
overlapping the section inboard of them by `RADIAL_SEAL`, and every cutaway
and window is glazed rather than open, so the inhabited volume (1.59e12 m³,
recorded per deck as `atmosphere-m3`) is geometrically sealed. The pylon
gaps are open sky by design and the tendrils are external structure — the
pressure envelope is the disk plus the ring, not the whole Arcology. That is
mesh closure and canon, not a pressure, thermal or life-support
certification.

## Canonical values

All dimensions, counts and colours live in `civitas/config.py` — the single
source of truth. City 84,000 m tall x 84,000 m wide (base14 foundation), with 12.6 m floor height and 1.4 m substrate depth; Arcology
78,000 m across zones A/B/C; 56 sovereign vessels; 14 commercial vessels;
Sen's Maurader at 28,000 m, stationed 14,000 m above the measured tower
apex; 2,744 Thornwall mines and 579,194 autonomous bots (built as
instances, not one object per bot). The Helix Tower void is 2.8 km, and the
commons starts at 2.8 km from the void with each radial 2.8 km wide. The
Cathedral of Light is 28 km wide by 5.6 km tall (scaled to base14 multiples).

## Scene controls

`FYNYGRYF_Arcology_Root` carries the driven custom properties:

| Property | Effect |
| --- | --- |
| `dazzle-state` | 0 normal, 1 dazzle — drives emission to 50 |
| `show-cross-sections` | reveals the five cross-section collections |
| `ark-visible` | reveals the Ark |

In-scene documentation is written to the `CIVITAS_DOCUMENTATION` text
datablock by every build.
