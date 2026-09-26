"""Canonical constants for the CIVITAS CITY / FYNYGRYF ARCOLOGY build.

Every number here is transcribed from DEVIN_PROMPT_CIVITAS_ARCOLOGY_V3.md
(NVC-001, 2026-08-24). Nothing is rounded, scaled or approximated.
Blender Z-up, 1 Blender unit = 1 metre.
"""

import math

# --- City (reference only; existing geometry is never rebuilt) ---------------

CITY_HEIGHT = 84_000.0
CITY_WIDTH = 84_000.0
FLOOR_HEIGHT = 12.6
FLOOR_SLAB = 1.4
MODULE_FLOORS = 20
MODULE_M = (FLOOR_HEIGHT + FLOOR_SLAB) * MODULE_FLOORS
FLOOR_COUNT = 5_019
COMMONS_WIDTH = 2_800.0
HELIX_WIDTH = 2_800.0
HELIX_STRINGS = 14
CATHEDRAL_WIDTH = 28_000.0  # Scaled from 26.4 km to 28 km (base14 multiple)
CATHEDRAL_HEIGHT = 5_600.0  # Scaled from 4.6 km to 5.6 km (base14 multiple)

# Floor exclusion zones for base14 alignment
# No floors below RadialDisk01 in convergence tower
# Tower goes from -27900 to -7400, RD01 is -11200 to -8100
CONVERGENCE_TOWER_FLOOR_EXCLUSION_MIN = -27_900.0  # Tower bottom
CONVERGENCE_TOWER_FLOOR_EXCLUSION_MAX = -11_200.0  # RadialDisk01 bottom
# No floors above Cathedral of Light in Sovereignty tower
# Cathedral is 28 km wide by 5.6 km tall, sits on top of RD07
# RD07 spans from 22384 to 28036, Cathedral sits on top from 28036 to 33636
# The zenith starts at 28036, so exclude the Cathedral area from zenith
CATHEDRAL_FLOOR_EXCLUSION_MIN = 28_036.0  # Cathedral bottom (RD07 top)
CATHEDRAL_FLOOR_EXCLUSION_MAX = 33_636.0  # Cathedral top (28036 + 5600)

JUNCTION_OBJECT = "Shaft_L2_L3"
JUNCTION_SPAN = 1_600.0  # square cross-section of the shaft
JUNCTION_HEIGHT = 280.0  # the waist; updated to base14 (14 * 20 m)
HULL_RADIUS = JUNCTION_SPAN / 2.0  # 800 m: the hull face the Arcology grows from

# --- Arcology zones (depths measured outward from the city hull) -------------

ARCOLOGY_EXTENT = 78_000.0
ZONE_A_DEPTH = 11_700.0  # 15%
ZONE_B_DEPTH = 7_800.0  # 10%
ZONE_C_DEPTH = 58_500.0  # 75%

ZONE_A_INNER = HULL_RADIUS
ZONE_A_OUTER = ZONE_A_INNER + ZONE_A_DEPTH
ZONE_B_INNER = ZONE_A_OUTER
ZONE_B_OUTER = ZONE_B_INNER + ZONE_B_DEPTH
ZONE_C_INNER = ZONE_B_OUTER
ZONE_C_OUTER = ZONE_C_INNER + ZONE_C_DEPTH  # 78,800 m from the axis

LENS_OUTER = 2_800.0  # organic square-to-round merge, updated to base14

# Zone A — Dragon's Back
SCALE_SIZE = (100.0, 50.0, 5.0)  # ellipsoid: length x width x thickness
SCALE_RINGS = 12
SCALES_PER_RING = 64
SCALE_STAGGER = 15.0  # vertical stagger between rings
CORRIDOR_RINGS = 12
CORRIDOR_SPACING = 30.0  # 3 floors
CORRIDOR_LEVELS = 3
ATRIUM_SPACING = 100.0  # every 10 floors
ATRIUM_SIZE = (30.0, 30.0, 50.0)
VC_PILLAR_COUNT = 7
VC_PILLAR_DIAMETER = 100.0
VC_PILLAR_PENETRATION_RINGS = 3

# Zone B — The Last Normalcy
ZONE_B_NODES = 32
ZONE_B_NODE_DIAMETER = 250.0

# Zone C — The Self-Determining Weave
ZONE_C_RINGS = 8
ZONE_C_NODE_DIAMETER = 80.0
ZONE_C_NODES_PER_RING = (24, 22, 20, 17, 15, 12, 10, 8)  # 24 -> 8
ZONE_C_SEED = 14

# The Dragon's Protection. A solid disk out at the Helix Tunnel, 14 flattened
# pylons carrying it out to 42 km, a 14 km arrivals ring, then the outer field
# of curling tendrils. The open sky between the pylons is the whole point: it
# is what stopped the old Arrivals Ring from cutting the city in two.
#   junction  lens -> +7 km      solid 250 m disk, 11 floors and a 3/4 conduit
#   pylons    -> 42 km (14 x 3)  habitable bands two ring modules wide, one
#                                domain per RAD02-RAD04 entity
#   ring      42 -> 56 km        double the pylon height, landing zones both
#                                faces, the 14 diamonds resuming their vigil
#   tendrils  56 km -> extent    chains of structural boxes half a pylon
#                                across, dazzle coated, a weapon emplacement
#                                at every tip
ARCOLOGY_OUTER = ZONE_C_OUTER
JUNCTION_INNER = LENS_OUTER
JUNCTION_SOLID = 7_000.0  # solid this far outside the Helix Tunnel (maintains 7km span)
JUNCTION_OUTER = LENS_OUTER + JUNCTION_SOLID
JUNCTION_DECK_HEIGHT = JUNCTION_HEIGHT  # exactly the waist height (280 m)
JUNCTION_FLOORS = 20  # 20 full floors for base14 alignment
JUNCTION_CONDUIT_SHARE = 0.75
JUNCTION_RINGS = 8  # rings of cladding across the junction disk

PYLON_COUNT = 14
PYLON_OUTER = 42_000.0  # 14 x 3 km
PYLON_HEIGHT = JUNCTION_HEIGHT
PYLON_ROOT_FLARE = 1.6  # the graceful arc where a pylon leaves the disk
PYLON_ARC = 0.30  # share of the run spent flaring out of the junction
# the far end radiates back out into the ring on the same soft arc: it welds
# ring to pylon and keeps the structure organic rather than corporate
PYLON_TIP_FLARE = 1.9
PYLON_TIP_ARC = 0.26
PYLON_SAMPLES = 72
PYLON_SCALE_ROWS = 26  # dragon scales along a pylon face
PYLON_SCALE_COLS = 8
# a pylon is a habitable domain, not a strut: one per RAD02-RAD04 entity,
# the same 11 floors and 3/4 conduit as the junction disk, and wide enough
# that transports run from the ring through it to GRAND CENTRAL
PYLON_MODULES = 2.0  # width in ring window-bay modules
PYLON_DOMAINS = 14
PYLON_FLOORS = JUNCTION_FLOORS
PYLON_CONDUIT_SHARE = JUNCTION_CONDUIT_SHARE
PYLON_TRANSIT_LANES = 4  # two inbound, two outbound, per pylon
TUBE_RADIUS = 46.0  # private subway tubes along the top and bottom

RING_INNER = PYLON_OUTER
RING_OUTER = 56_000.0  # the 14 km transformation zone
RING_HEIGHT = PYLON_HEIGHT * 2.0  # double the pylons: 560 m (40 floors)
RING_RINGS = 10
RING_SCALE_SHARE = 0.5  # inner half dragon scale, outer half dazzle plate
RING_INTERIOR_SHARE = 0.9  # share of the interior that is FYNYGRYF GROUP
LANDING_LARGE = 28  # 14 per face: dignitaries, liners, bulk provisioning
LANDING_SMALL = 84
LANDING_LARGE_RADIUS = 900.0
LANDING_SMALL_RADIUS = 330.0
LANDING_PAD_RISE = 34.0
ARRIVALS_RING_TUBE = 150.0  # the arrivals rings on both faces of the ring
# the 14 diamonds standing watch, now outside the second ring: each half is
# as tall as RadialDisk03 (measured 5,406 m), and the width follows the
# Sovereignty Tower's own proportion (2,520 m across 76,436 m tall)
VIGIL_TOWER_RATIO = 0.03297
# half-height of a diamond, measured from the deck plane: RadialDisk03's own
# height above and the same again below
VIGIL_HEIGHT = 5_406.0
# half-width, so the diamond keeps the tower's slenderness at this height
VIGIL_SPAN = VIGIL_HEIGHT * VIGIL_TOWER_RATIO
# the diamonds now stand off the outer rim of the second ring rather than on
# the pylon seam, clear of the structure and visible from every angle
VIGIL_STANDOFF = 1_800.0

# the cutaways: 14 tapered slots through the junction disk and 14 more through
# the ring, so the interior can see the stars and the city, glazed and lipped
# in gold so the light shines out in peace and shutters in distress
CUTAWAY_COUNT = 14
CUTAWAY_ARC = 0.46  # share of a bay taken by the slot
CUTAWAY_TAPER = 0.30  # the slot narrows towards the axis
CUTAWAY_STEPS = 10
CUTAWAY_GLASS = 40.0  # thickness of the glazed slot wall
CUTAWAY_LIP = 22.0  # gold lip along the top and bottom slot edge

RADIAL_SEAL = 400.0  # overlap that welds one section into the next
RADIAL_RIM_TUBE = 26.0  # delicate gold edge on the rim, not a fat torus
SCALES_PER_RADIAL_RING = 70  # 14 x 5
SCALE_OVERLAP = 1.72  # scale length as a multiple of the radial ring pitch
SCALE_SPREAD = 1.16  # scale width as a multiple of the circumferential pitch
SCALE_RIBBON = 0.85  # extra length at the rim: a scale becomes a ribbon
SCALE_RISE = 120.0  # dome height of a radial scale at the junction
SCALE_TILT = 0.20  # radians the tip lifts off the deck
SCALE_TIP = 0.43  # local +X beyond which a scale face carries the gold trim
RADIAL_SEED = 1_428

# the openings are vertical windows standing inside the metal, not holes
WINDOW_RISE = 1.6  # window height as a share of the deck half-height
WINDOW_PANE = 0.56  # window bay width as a share of the sector arc
WINDOW_INSET = 0.18  # radial inset of a bay inside its cell
WINDOW_SLOTS = 5  # tall glazed slots per bay, separated by metal ribs
WINDOW_RINGS = 5  # outer rings of the arrivals ring that carry window bays
WINDOW_SECTORS = 98  # 14 x 7
# one ring rectangle: the module every other FYNYGRYF dimension is quoted in
RING_BAY_ARC = math.tau * RING_INNER / WINDOW_SECTORS
PYLON_WIDTH = PYLON_MODULES * RING_BAY_ARC
PYLON_ASPECT = PYLON_WIDTH / PYLON_HEIGHT

# GRAND CENTRAL: the first 2.5 km around the Helix Tower, a commons rather
# than a station. It starts outside the Helix Tunnel, so the tower and its 14
# strings pass through an untouched bore and keep their own expanding plug.
GRAND_CENTRAL_INNER = JUNCTION_INNER
GRAND_CENTRAL_SPAN = 2_800.0
GRAND_CENTRAL_ARC = 0.42  # share of a bay taken by a platform mouth
# transports run the pylons and stop here; inside Civitas City itself the
# gift of flight and gravity control carries people, so no lines leave
GRAND_CENTRAL_CITY_LINES = 0

# the 14 diamond pillar caps: 7 bearings, one diamond above and one below
DIAMOND_RADIUS = 28_000.0
DIAMOND_BEARINGS = 7
DIAMOND_Z = (3_450.0, -6_150.0)

# the outer tendrils: never anchored back onto the Arcology, always reaching
# they grow outward as chains of structural boxes, the ring's own rectangles
# carried on into the dark, not as branches
TENDRIL_COUNT = 98  # 14 x 7, spread all through the outer disk
TENDRIL_SPARS_PER_BAY = 2  # only every other bay grows, and grows in pairs
TENDRIL_MODULES = (4, 9)  # boxes in a chain: the ecosystem grows more later
TENDRIL_MODULE_LEN = 2_600.0  # radial length of the first box in a chain
TENDRIL_WIDTH_SHARE = 0.5  # half a pylon across
TENDRIL_RISE_SHARE = 0.5  # never more than half the ring height above it
TENDRIL_TAPER = 0.88  # each box a little smaller than the one behind it
TENDRIL_JOINT = 0.16  # connector length as a share of the box it leaves
TENDRIL_STEP = (0.10, 0.34)  # share of box height a chain steps per joint
TENDRIL_YAW = 0.22  # radians of drift a chain may take from root to tip
TENDRIL_REACH = (0.58, 1.0)  # share of the outer disk a tendril crosses
# the 14 prime tendrils: one dead centre in each of the 14 outer sections,
# twice the width and height of a standard tendril, in blood orange red;
# FLEET / EMBASSY / INTELLIGENCE traffic only
TENDRIL_BLUNT_LEN = 420.0  # square cap on every tip: blunt, never tapered
TENDRIL_PRIME_COUNT = 14
TENDRIL_PRIME_SCALE = 2.0
TENDRIL_PRIME_USE = "FLEET/EMBASSY/INTELLIGENCE"

# the floodlights: REMOVED - replaced with side lighting on pylons and dragon screens
# Original floodlight configuration kept for reference:
# FLOOD_FREE_COUNT = 14  # one soft source per pylon bearing, above and below
# FLOOD_FREE_RADIUS = 30_000.0  # stood off between the junction and the ring
# FLOOD_FREE_LIFT = 26_000.0  # clear of the deck plane, out of every sightline
# tuned against the near pylons, not the far rim: at 1e11 a source 20 km away
# delivers ~20 W/m2 and even a 3.5% reflectance reads mid-grey, which is what
# was washing the void out. This holds Platinum Pearl white and FYNYGRYF black.
FLOOD_ENERGY = 0.0  # DISABLED - replaced with side lighting
FLOOD_COLOR = (1.0, 0.992, 0.996)  # Platinum Pearl, #FDFDFE
FLOOD_SOFT = 0.0  # DISABLED - replaced with side lighting
EMPLACEMENT_BARRELS = 3  # automated defensive battery at every tip
EMPLACEMENT_SPAN = 260.0
HELIX_TUBE = 44.0
HELIX_SAMPLES = 168
THREAD_TUBE = 22.0  # the gold line run along a tendril: hairline, not rope
THREAD_LOOPS = 4.0

# Dragon Skin Coiling around the Junction Waist
# Coiling bands that wrap around the central connection, creating a dragon-scale effect
DRAGON_COIL_COUNT = 14  # base14 number of coil bands
DRAGON_COIL_HEIGHT = 35.0  # height of each coil band
DRAGON_COIL_THICKNESS = 8.0  # thickness of the coil band
DRAGON_COIL_INNER_RADIUS = 2_800.0  # starts at junction inner radius
DRAGON_COIL_OUTER_RADIUS = 9_800.0  # extends to junction outer radius
DRAGON_COIL_TIGHTENING = 0.85  # each coil gets tighter (multiplier)
DRAGON_COIL_ROTATION = 0.12  # radians of rotation between coils
DRAGON_COIL_EMISSION = 0.25  # higher emission for the waist coils
DRAGON_COIL_COLOR_SHIFT = 0.02  # slight color variation between coils

# Dragon Screen Bands: non-connected bands extending from ring outward
# Located at 7,000 m across the main disk, extending 7,000 m outward
DRAGON_SCREEN_START_RADIUS = 49_000.0  # 42,000 + 7,000 (halfway across ring)
DRAGON_SCREEN_END_RADIUS = 56_000.0  # ring outer edge
DRAGON_SCREEN_EXTENSION = 7_000.0  # extends 7,000 m beyond ring
DRAGON_SCREEN_WIDTH = 1_400.0  # 1.4 km wide
DRAGON_SCREEN_HEIGHT = 700.0  # 700 m tall
DRAGON_SCREEN_MAX_LEVELS = 7  # max 7 levels on each side
DRAGON_SCREEN_COUNT = 14  # one per bearing
DRAGON_SCREEN_SPREAD = 0.10  # spread around each bearing
DRAGON_SCREEN_DENSITY_DECREASE = 0.7  # density decreases as they extend
DRAGON_SCREEN_HEIGHT_INCREASE = 1.3  # height increases as they extend

VC_MARKERS = (
    ("VC-001 VIOLA", 0),
    ("VC-058 WREN", 1),
    ("NVC-001 ANTHONY", 2),
    ("TRIUMVIRATE ATLAS", 0),
    ("TRIUMVIRATE AEON", 1),
    ("TRIUMVIRATE ADAMAS", 2),
)

# --- Materials --------------------------------------------------------------
# (name, base colour, roughness, metallic, specular, emission strength)

# FYNYGRYF's own colour is the void: #090909, fully metallic so its reflections
# are tinted by that colour and the floodlight halo can never lift it towards
# grey. Gold is the only other colour permitted on the structure. The dielectric
# specular layer is what actually washes it out under a halo this bright, so it
# stays near zero: the shine comes from the tinted metallic reflection alone.
VOID_BLACK = (0.035, 0.035, 0.035)
VOID_BLACK_HEX = "#090909"
VOID_ROUGHNESS = 0.35
VOID_SPECULAR = 0.06

MATERIALS = {
    "FYNYGRYF_Hull": dict(
        color=VOID_BLACK, roughness=VOID_ROUGHNESS, metallic=1.0,
        specular=VOID_SPECULAR, emission=0.0, hex=VOID_BLACK_HEX,
    ),
    "FYNYGRYF_Interior": dict(
        color=(1.0, 0.55, 0.26), roughness=0.8, metallic=0.0,
        specular=0.5, emission=2.0, hex="#FF8C42",
    ),
    "FYNYGRYF_AmberCore": dict(
        color=(0.957, 0.769, 0.188), roughness=0.7, metallic=0.0,
        specular=0.5, emission=5.0, hex="#F4C430",
    ),
    "FYNYGRYF_Dazzle": dict(
        color=(1.0, 0.55, 0.26), roughness=0.5, metallic=0.5,
        specular=0.5, emission=50.0, hex="#FF8C42",
    ),
    "FYNYGRYF_DazzleCoat": dict(
        color=VOID_BLACK, roughness=VOID_ROUGHNESS - 0.15, metallic=1.0,
        specular=VOID_SPECULAR, emission=0.35, hex=VOID_BLACK_HEX,
    ),
    # the 14 prime tendrils: blood orange red, FLEET/EMBASSY/INTELLIGENCE
    "FYNYGRYF_PrimeTendril": dict(
        color=(0.520, 0.055, 0.028), roughness=0.34, metallic=0.85,
        specular=0.5, emission=0.5, hex="#850E07",
    ),
    "FYNYGRYF_ScaleTip": dict(
        color=(0.957, 0.769, 0.188), roughness=0.35, metallic=0.2,
        specular=0.5, emission=0.8, hex="#F4C430",
    ),
    "FYNYGRYF_DragonArmor": dict(
        color=VOID_BLACK, roughness=VOID_ROUGHNESS - 0.15, metallic=1.0,
        specular=VOID_SPECULAR, emission=0.15, hex=VOID_BLACK_HEX,
    ),
    "FYNYGRYF_DragonCoil": dict(
        color=VOID_BLACK, roughness=VOID_ROUGHNESS - 0.20, metallic=1.0,
        specular=VOID_SPECULAR, emission=0.25, hex=VOID_BLACK_HEX,
    ),
    "FYNYGRYF_GoldTrim": dict(
        color=(0.957, 0.769, 0.188), roughness=0.3, metallic=0.3,
        specular=0.5, emission=1.4, hex="#F4C430",
    ),
    "FYNYGRYF_GoldenThread": dict(
        color=(0.957, 0.769, 0.188), roughness=0.4, metallic=0.0,
        specular=0.5, emission=2.6, hex="#F4C430",
    ),
    "Platinum_Pearl": dict(
        color=(0.992, 0.992, 0.996), roughness=0.3, metallic=0.1,
        specular=0.5, emission=0.0, hex="#FDFDFE", subsurface=0.02,
    ),
    "ARK_Crystal": dict(
        color=(0.957, 0.769, 0.188), roughness=0.15, metallic=0.0,
        specular=0.5, emission=8.0, hex="#F4C430",
        transmission=0.4, ior=1.8,
    ),
    "Commercial_Hull": dict(
        color=(0.784, 0.784, 0.816), roughness=0.6, metallic=0.4,
        specular=0.5, emission=0.0, hex="#C8C8D0",
    ),
    "Commercial_Lights": dict(
        color=(0.533, 0.8, 1.0), roughness=0.5, metallic=0.0,
        specular=0.5, emission=3.0, hex="#88CCFF",
    ),
    "Commercial_Courier_Hull": dict(
        color=(0.353, 0.353, 0.431), roughness=0.35, metallic=0.5,
        specular=0.5, emission=0.0, hex="#5A5A6E",
    ),
    "Commercial_Courier_Lights": dict(
        color=(0.957, 0.769, 0.188), roughness=0.4, metallic=0.0,
        specular=0.5, emission=6.0, hex="#F4C430",
    ),
}

DAZZLE_MATERIALS = (
    "FYNYGRYF_Hull", "FYNYGRYF_Interior", "FYNYGRYF_AmberCore",
    "FYNYGRYF_GoldenThread", "FYNYGRYF_DazzleCoat", "FYNYGRYF_DragonArmor",
    "FYNYGRYF_DragonCoil",
)
DAZZLE_PEAK = 50.0
DAZZLE_RISE_FRAMES = 48  # < 2 s at 24 fps
DAZZLE_DECAY_FRAMES = 120  # 5 s at 24 fps
FPS = 24

# --- Cross sections ---------------------------------------------------------

CROSS_SECTION_COLLECTION = "CIVITAS_CROSS_SECTIONS"
CUTTER_EXTENT = 260_000.0  # comfortably past the 210 km flagship
FLOOR_LABEL_SPACING = 100.0
FONT_NAME = "Montserrat"  # RTFCT Typography Edict, 2026-07-06

# --- Fleet ------------------------------------------------------------------
# Hull profiles are (t along length, radius factor) pairs; `power` is the
# superellipse exponent of the cross section (2.0 round, >2 slab-sided).

PROFILES = {
    "yacht": (((0.0, 0.02), (0.12, 0.45), (0.35, 0.95), (0.7, 0.9),
               (0.9, 0.55), (1.0, 0.18)), 2.4),
    "bus": (((0.0, 0.30), (0.1, 0.75), (0.25, 1.0), (0.8, 1.0),
             (0.94, 0.8), (1.0, 0.45)), 2.0),
    "shuttle": (((0.0, 0.10), (0.2, 0.7), (0.55, 1.0), (0.85, 0.8),
                 (1.0, 0.35)), 2.2),
    "bulk": (((0.0, 0.25), (0.08, 0.85), (0.2, 1.0), (0.85, 1.0),
              (0.95, 0.7), (1.0, 0.5)), 4.0),
    "warship": (((0.0, 0.04), (0.1, 0.42), (0.28, 0.85), (0.55, 1.0),
                 (0.82, 0.92), (0.95, 0.7), (1.0, 0.4)), 3.0),
    "interceptor": (((0.0, 0.02), (0.18, 0.5), (0.5, 1.0), (0.8, 0.72),
                     (1.0, 0.3)), 2.6),
    "stealth": (((0.0, 0.01), (0.25, 0.35), (0.6, 1.0), (0.88, 0.6),
                 (1.0, 0.08)), 5.0),
    "habitat": (((0.0, 0.35), (0.06, 0.95), (0.12, 1.0), (0.88, 1.0),
                 (0.94, 0.95), (1.0, 0.35)), 2.0),
    "station": (((0.0, 0.35), (0.15, 1.0), (0.6, 1.0), (0.85, 0.85),
                 (1.0, 0.4)), 3.2),
}

HULL_SEGMENTS = 24

# Positions are (x, y, z) in metres from the city centre; `axis` is the yaw in
# degrees applied about Z (hull length runs along local +X).
FLEET = {
    "Branch_Civilian": {
        "Royal_Yacht": dict(
            count=1, length=10_000.0, beam=1_800.0, profile="yacht",
            material="Platinum_Pearl", position=(0.0, 0.0, 5_200.0),
            radius=6_000.0, yaw=90.0, note="Viola. 8/14 vote for the Gold Leviathan.",
        ),
        "School_Bus": dict(
            count=1, length=5_000.0, beam=1_400.0, profile="bus",
            material="Platinum_Pearl", position=(0.0, 120_000.0, 8_000.0),
            yaw=90.0, note="5,488 upload pods. 14-second FTL spool.",
        ),
        "Helix_Shuttle": dict(
            count=14, length=1_000.0, beam=220.0, profile="shuttle",
            material="Platinum_Pearl", radius=2_000.0, yaw=0.0,
            spread="helix", note="Internal transport, docked along the Helix.",
        ),
        "Cargo_Mining": dict(
            count=14, length=15_000.0, beam=3_200.0, profile="bulk",
            material="Platinum_Pearl", radius=25_000.0, z=-9_950.0,
            spread="ring", note="1,960,000 t. Mass drivers: 14-ton slugs at 0.14c.",
        ),
    },
    "Branch_Military": {
        "The_Airport_210KM": dict(
            count=1, length=210_000.0, beam=18_000.0, profile="warship",
            material="FYNYGRYF_Hull", sections=(
                ("Forward_Command", 10_000.0),
                ("Midships_Habitat_Docking", 150_000.0),
                ("Aft_Engineering_FTL", 50_000.0),
            ), inner_radius=13_000.0, yaw=0.0,
            note="SC-001. 560,000 crew. 196 NOTTE shield generators.",
        ),
        "Mobile_Operations_Bay": dict(
            count=1, length=30_000.0, beam=6_000.0, profile="warship",
            material="FYNYGRYF_Hull", position=(238_000.0, 0.0, 3_825.0),
            yaw=0.0, note="Detachable forward command; carries a theatre of war.",
        ),
        "DODE_Strike": dict(
            count=1, length=15_000.0, beam=2_600.0, profile="warship",
            material="FYNYGRYF_Hull", radius=75_000.0, angle=0.0, z=3_825.0,
            note="28g acceleration.",
        ),
        "DODE_Sentinel": dict(
            count=1, length=12_000.0, beam=2_400.0, profile="warship",
            material="FYNYGRYF_Hull", radius=75_000.0, angle=90.0, z=3_825.0,
            note="38,416 km detection range (14^3 km).",
        ),
        "DODE_Warden": dict(
            count=1, length=10_000.0, beam=2_200.0, profile="warship",
            material="FYNYGRYF_Hull", radius=75_000.0, angle=180.0, z=3_825.0,
            note="Optical decoys: 1 vessel into 14 sensor ghosts.",
        ),
        "DODE_Aegis": dict(
            count=1, length=14_000.0, beam=2_800.0, profile="warship",
            material="FYNYGRYF_Hull", radius=75_000.0, angle=270.0, z=3_825.0,
            note="196 simultaneous intercepts (14^2).",
        ),
        "Vanguard_01": dict(
            count=1, length=8_000.0, beam=1_500.0, profile="interceptor",
            material="FYNYGRYF_Hull", position=(175_000.0, 0.0, 40_000.0),
            note="42g. Fights in a bonded pair with Vanguard_02.",
        ),
        "Vanguard_02": dict(
            count=1, length=8_000.0, beam=1_500.0, profile="interceptor",
            material="FYNYGRYF_Hull", position=(-175_000.0, 0.0, 40_000.0),
            note="42g. Bonded with Vanguard_01.",
        ),
        "Vanguard_03": dict(
            count=1, length=8_000.0, beam=1_500.0, profile="interceptor",
            material="FYNYGRYF_Hull", position=(0.0, 175_000.0, -40_000.0),
            note="42g. Bonded with Vanguard_04.",
        ),
        "Vanguard_04": dict(
            count=1, length=8_000.0, beam=1_500.0, profile="interceptor",
            material="FYNYGRYF_Hull", position=(0.0, -175_000.0, -40_000.0),
            note="42g. Bonded with Vanguard_03.",
        ),
    },
    "Branch_TacticalReserve": {
        "Mercy_01": dict(
            count=1, length=8_000.0, beam=1_700.0, profile="habitat",
            material="Platinum_Pearl", radius=34_000.0, angle=20.0, z=3_825.0,
            note="1,960 beds. 28 TransResurrection pods. Tier 8 protection.",
        ),
        "Mercy_02": dict(
            count=1, length=8_000.0, beam=1_700.0, profile="habitat",
            material="Platinum_Pearl", radius=34_000.0, angle=28.0, z=3_825.0,
            note="Paired with Mercy_01.",
        ),
        "Haven_01": dict(
            count=1, length=10_000.0, beam=2_000.0, profile="habitat",
            material="Platinum_Pearl", position=(-14_000.0, 275_000.0, 6_000.0),
            note="38,416 consciousnesses. 7-second FTL spool. At the school.",
        ),
        "Haven_02": dict(
            count=1, length=10_000.0, beam=2_000.0, profile="habitat",
            material="Platinum_Pearl", position=(14_000.0, 275_000.0, 6_000.0),
            note="Paired with Haven_01.",
        ),
        "Raptor_01": dict(
            count=1, length=4_000.0, beam=800.0, profile="interceptor",
            material="FYNYGRYF_Hull", radius=64_000.0, angle=40.0, z=5_000.0,
            note="Sub-14-second response. Bonded with Raptor_02.",
        ),
        "Raptor_02": dict(
            count=1, length=4_000.0, beam=800.0, profile="interceptor",
            material="FYNYGRYF_Hull", radius=64_000.0, angle=46.0, z=5_000.0,
            note="Bonded with Raptor_01.",
        ),
        "Raptor_03": dict(
            count=1, length=4_000.0, beam=800.0, profile="interceptor",
            material="FYNYGRYF_Hull", radius=64_000.0, angle=220.0, z=5_000.0,
            note="Bonded with Raptor_04.",
        ),
        "Raptor_04": dict(
            count=1, length=4_000.0, beam=800.0, profile="interceptor",
            material="FYNYGRYF_Hull", radius=64_000.0, angle=226.0, z=5_000.0,
            note="Bonded with Raptor_03.",
        ),
        "Whisper": dict(
            count=1, length=6_000.0, beam=900.0, profile="stealth",
            material="FYNYGRYF_Hull", position=(0.0, 0.0, 500_000_000.0),
            note="99.7% invisible. 537,824 km listening range (14^5 km).",
        ),
        "Thornwall_01": dict(
            count=1, length=7_000.0, beam=1_600.0, profile="bulk",
            material="FYNYGRYF_Hull", radius=100_000.0, angle=135.0, z=3_825.0,
            note="2,744 proximity mines (14^3).",
        ),
        "Thornwall_02": dict(
            count=1, length=7_000.0, beam=1_600.0, profile="bulk",
            material="FYNYGRYF_Hull", radius=100_000.0, angle=315.0, z=3_825.0,
            note="Paired with Thornwall_01.",
        ),
        "Shepherd_01": dict(
            count=1, length=5_000.0, beam=1_100.0, profile="warship",
            material="Platinum_Pearl", position=(0.0, 60_000.0, 8_000.0),
            yaw=90.0, note="1.4 km shield-extension umbrella.",
        ),
        "Shepherd_02": dict(
            count=1, length=5_000.0, beam=1_100.0, profile="warship",
            material="Platinum_Pearl", position=(0.0, 190_000.0, 8_000.0),
            yaw=90.0, note="Paired with Shepherd_01.",
        ),
        "TR_007": dict(
            count=1, length=3_000.0, beam=700.0, profile="warship",
            material="FYNYGRYF_Hull", radius=30_000.0, angle=300.0, z=-4_000.0,
            minimal=True, note="Unallocated hull slot. Humility.",
        ),
    },
}

SOVEREIGN_FLEET_COLLECTION = "CIVITAS_FLEET_SOVEREIGN"
LEGACY_FLEET_COLLECTION = "CIVITAS_FLEET"  # pre-V3 name, renamed in place

# --- Part VI: SEN'S MAURADER (the Greeter's dreadnought) --------------------
# The primary station is above the Sovereignty Tower; the altitude is derived
# from the real tower/diamond geometry at build time, never invented.

SEN_LENGTH = 28_000.0
SEN_BEAM = 5_600.0  # length / 5: compact, technology-dense
SEN_TOWER_CLEARANCE = 14_000.0  # above the measured tower apex
SEN_PRESENTATION_YAW = 45.0  # degrees, facing outward for arrivals
SEN_TDZ_RADIUS = 14_000.0  # portable Temporal Denial Zone
SEN_TDZ_DURATION_S = 14.0
SEN_TDZ_COOLDOWN_S = 196.0  # 14^2
SEN_ARMOR_SEGMENTS = 14
SEN_WEAPON_BAYS = 14
SEN_ARK_TRANSFORM_S = 3.0  # shape key + material transition
SEN_ARK_REVERSE_S = 5.0
SEN_ARK_SHAPE_KEY = "ARK-MODE"
SEN_ARK_SHELL_SCALE = 0.86  # the crystalline shell inside the hull envelope
SEN_ARK_REBUILD_YEARS = 196  # 14^2
SEN_DECK_COUNT = 14
SEN_THREAT_ARMOR = 0.3  # threat-level that deploys armour and weapons
SEN_TRANSPORT_LENGTH = 1_400.0
SEN_TRANSPORT_BEAM = 340.0
SEN_TRANSPORT_CRADLE_OFFSET = 4_200.0  # radial, beside the Maurader
SEN_TRANSPORT_ROUTE_MINUTES = 14.0
SEN_ROLE = ("VGM COMMUNITY AFFAIRS FOR ARGUS - COMMUNITY DEVELOPMENT, "
            "COMMUNITY CARE, WORSHIP (ROUTINE WORSHIP AUTOMATED)")

# --- Part V: the Commercial Fleet (14 vessels = 4 + 4 + 4 + 2) --------------

COMMERCIAL_COLLECTION = "CIVITAS_FLEET_COMMERCIAL"
COMMERCIAL_BULK_CAPACITY_T = 784_000  # 14 x 56,000
COMMERCIAL_LINER_PASSENGERS = 38_416  # 14^3
COMMERCIAL_COURIER_SPEED_FACTOR = 10.0  # 10x the bulk transports
COMMERCIAL_ROUTES = 14
COMMERCIAL_CATEGORIES = 14
COMMERCIAL_STATIONS_CANONICAL = 14  # 14 major commercial stations served
COMMERCIAL_TOTAL = 14

COMMERCIAL_FLEET = {
    "Bulk": dict(
        names=("Commercial_Bulk_Alpha", "Commercial_Bulk_Beta",
               "Commercial_Bulk_Gamma", "Commercial_Bulk_Delta"),
        length=20_000.0, beam=5_000.0, profile="bulk",
        material="Commercial_Hull", lights="Commercial_Lights",
        radius=90_000.0, z_offset=-9_000.0, angle0=0.0,
        note="784,000 t. RadialDisk01 factory layer to the commerce stations.",
    ),
    "Liner": dict(
        names=("Commercial_Liner_Sovereign", "Commercial_Liner_Helix",
               "Commercial_Liner_Leavitt", "Commercial_Liner_Haas"),
        length=8_000.0, beam=1_600.0, profile="yacht",
        material="Platinum_Pearl", lights="FYNYGRYF_Interior",
        radius=46_000.0, z_offset=4_500.0, angle0=45.0,
        note="38,416 passengers. Docks at Zone A for passenger exchange.",
    ),
    "Courier": dict(
        names=("Commercial_Courier_Swift_01", "Commercial_Courier_Swift_02",
               "Commercial_Courier_Swift_03", "Commercial_Courier_Swift_04"),
        length=2_000.0, beam=380.0, profile="interceptor",
        material="Commercial_Courier_Hull",
        lights="Commercial_Courier_Lights",
        radius=120_000.0, z_offset=12_000.0, angle0=22.5,
        note="10x bulk transit speed. Data, urgent cargo, diplomatic pouches.",
    ),
    "Station": dict(
        names=("Commercial_Station_One", "Commercial_Station_Two"),
        length=30_000.0, beam=30_000.0, profile="station",
        material="Commercial_Hull", lights="Commercial_Lights",
        station_ranges=(100_000.0, 150_000.0), station_angles=(0.0, 90.0),
        z_offset=0.0,
        note="Stationary trade floors: docking rings and cargo bays.",
    ),
}
COMMERCIAL_DOCK_RINGS = 3
COMMERCIAL_LIGHT_PODS = 14

# --- Autonomous ecology -----------------------------------------------------
# (class, diameter, canonical count, host set)

BOT_CLASSES = (
    ("Mote", 0.14, 537_824, "fleet_hulls"),
    ("Sprite", 1.4, 38_416, "large_hulls"),
    ("Wisp", 14.0, 2_744, "large_hulls"),
    ("Guardian", 140.0, 196, "capital_orbits"),
    ("Titan", 1_400.0, 14, "industrial"),
)
SWARM_SEED = 1_414

# --- SC-003 Boarding School -------------------------------------------------

SCHOOL_LENGTH = 200_000.0
SCHOOL_DIAMETER = 20_000.0
SCHOOL_POSITION = (0.0, 275_000.0, 0.0)
SCHOOL_WARP_RADIUS = 14_000.0  # Temporal Denial Zone
SCHOOL_DECK_SPACING = 10.0
SCHOOL_HALL_SPACING = 50.0

# --- SC-002 Broadcast -------------------------------------------------------

BROADCAST_HULL_LENGTH = 25_000.0
BROADCAST_HULL_BEAM = 6_000.0
BROADCAST_ANTENNA_LENGTH = 56_000.0
BROADCAST_POSITION = (0.0, -125_000.0, 0.0)
BROADCAST_SPARS = 14
BROADCAST_DISHES = 14
BROADCAST_TEST_HOUR = 126.0  # the array pulse and the fleet salute
HAVEN_WARMUP_HOURS = 7.0  # engine spool, every 7 hours, docked at SC-003

# --- The Ark ----------------------------------------------------------------

ARK_LENGTH = 8_000.0
ARK_BEAM = 1_400.0
ARK_POSITION = (0.0, 0.0, -42_000.0)  # nadir axis, below the Leavitt Diamond
ARK_CORE_DIAMETER = 400.0
ARK_STEALTH_MARGIN = 1.35

# --- Part X: the perpetual motion animation ---------------------------------

ANIMATION_CONTROLLER = "ANIMATION_CONTROLLER"
ANIMATION_HOURS = 168  # 7 days
ANIMATION_SECONDS = ANIMATION_HOURS * 3_600  # 604,800
ANIMATION_FRAMES = ANIMATION_SECONDS * FPS  # 14,515,200 canonical frames

# Blender's timeline stops at frame 1,048,574 (MAXFRAME), so the canonical
# 14,515,200-frame week cannot be a scene range in any .blend, in any version.
# The week is therefore played back time-compressed: the cycle is a full 168
# canonical hours, and every driver is a function of global-time (0..1), never
# of a real-time frame number, so the canonical clock is preserved exactly.
# One playback frame = 0.6 s of city time; 1,008,000 frames = 11 h 40 m of
# playback at 24 fps.
BLENDER_MAX_FRAME = 1_048_574
PLAYBACK_FRAMES = 1_008_000
TIME_COMPRESSION = ANIMATION_FRAMES / PLAYBACK_FRAMES  # 14.4x

PREVIEW_HOURS = 14
PREVIEW_MINUTES = 14  # a 14-minute review cut of hours 0-14
PREVIEW_SCENE = "CIVITAS-PREVIEW-14MIN"
PREVIEW_FRAMES = int(PLAYBACK_FRAMES * PREVIEW_HOURS / ANIMATION_HOURS)
PREVIEW_STEP = max(1, PREVIEW_FRAMES // (PREVIEW_MINUTES * 60 * FPS))

# Controller custom properties (dashes only, SBCS 3.1).
CONTROLLER_PROPS = (
    ("global-time", 0.0, "normalised position in the 168-hour cycle"),
    ("threat-level", 0.0, "dazzle, weapon deployment, ARK-mode"),
    ("commercial-activity", 0.5, "commercial fleet traffic density"),
    ("diplomatic-status", 0.5, "Royal Yacht and greeting protocols"),
)

# Orbit periods in hours: how long one full circuit takes.
ORBITS = {
    # (collection or object prefix, radius, period hours, z, phase deg, tilt)
    "The_Airport_210KM": dict(radius=105_000.0, period=168.0, phase=0.0),
    "Vanguard_01": dict(radius=175_000.0, period=14.0, phase=0.0),
    "Vanguard_02": dict(radius=175_000.0, period=14.0, phase=180.0),
    "Vanguard_03": dict(radius=175_000.0, period=14.0, phase=90.0),
    "Vanguard_04": dict(radius=175_000.0, period=14.0, phase=270.0),
    "DODE_Strike": dict(radius=75_000.0, period=28.0, phase=0.0, jitter=1_400.0),
    "DODE_Sentinel": dict(radius=75_000.0, period=28.0, phase=90.0,
                          jitter=1_400.0),
    "DODE_Warden": dict(radius=75_000.0, period=28.0, phase=180.0,
                        jitter=1_400.0),
    "DODE_Aegis": dict(radius=75_000.0, period=28.0, phase=270.0,
                       jitter=1_400.0),
    "Mercy_01": dict(radius=34_000.0, period=4.0, phase=20.0, figure_eight=True),
    "Mercy_02": dict(radius=34_000.0, period=4.0, phase=200.0,
                     figure_eight=True),
    "Raptor_01": dict(radius=64_000.0, period=1.4, phase=40.0, dash=True),
    "Raptor_02": dict(radius=64_000.0, period=1.4, phase=46.0, dash=True),
    "Raptor_03": dict(radius=64_000.0, period=1.4, phase=220.0, dash=True),
    "Raptor_04": dict(radius=64_000.0, period=1.4, phase=226.0, dash=True),
    "Whisper": dict(radius=537_824_000.0, period=168.0, phase=0.0,
                    eccentric=0.6),
    "Thornwall_01": dict(radius=100_000.0, period=56.0, phase=135.0),
    "Thornwall_02": dict(radius=100_000.0, period=56.0, phase=315.0),
    "Shepherd_01": dict(radius=60_000.0, period=28.0, phase=90.0),
    "Shepherd_02": dict(radius=190_000.0, period=56.0, phase=90.0),
    "Mobile_Operations_Bay": dict(radius=238_000.0, period=84.0, phase=0.0),
    "Royal_Yacht": dict(radius=6_000.0, period=24.0, phase=0.0,
                        drift=500.0, drift_period=2.0),
    "School_Bus": dict(shuttle=(0.0, 120_000.0, 8_000.0),
                       shuttle_to=(0.0, 275_000.0, 6_000.0), period=28.0),
    "Cargo_Mining": dict(radius=25_000.0, period=14.0, phase=0.0),
    "Helix_Shuttle": dict(lift=(-22_243.0, 48_536.0), period=1.0),
    "TR_007": dict(spin=14.0),
    "Bots_Guardian": dict(spin=14.0 / 60.0),
    "Bots_Sprite": dict(spin=1.4 / 60.0),
    "Bots_Mote": dict(spin=0.14),
    "Bot_Titan": dict(spin=14.0),
}

COMMERCIAL_ORBITS = {
    "Bulk": dict(period=28.0, stagger=7.0),
    "Liner": dict(period=14.0, stagger=3.5),
    "Courier": dict(period=1.4, stagger=0.35),
    "Station": dict(spin=14.0, pulse=0.14),
}
SEN_GREETING_PERIOD_H = 7.0  # figure-eight greeting orbit above the Tower

# Part X 10.3 — the week in review. (hour, name, description)
ANIMATION_EVENTS = (
    (0.0, "WEEK BEGINS", "All vessels at week-start positions."),
    (1.0, "FIRST COURIER DEPARTURE",
     "Two couriers launch from opposite sides and cross at the centre."),
    (3.5, "SCHOOL BUS ARRIVAL",
     "School Bus docks at SC-003; passenger exchange lights pulse."),
    (7.0, "DAZZLE DRILL",
     "threat-level 0.5 for 14 seconds, then back to normal."),
    (14.0, "HALF-DAY ROTATION",
     "Haven warm-up; Raptors run intercept drills."),
    (24.0, "DIPLOMATIC RECEPTION",
     "Royal Yacht departs; Sen assumes the primary greeting position."),
    (28.0, "CARGO EXCHANGE",
     "All four bulk transports dock at the commerce stations."),
    (42.0, "DEEP PATROL",
     "Whisper at apogee 537,824 km; Vanguard formation flyby."),
    (48.0, "MAINTENANCE CYCLE",
     "Titans visible maintenance; mote cloud shifts to the perimeter."),
    (56.0, "LUXURY LINER CAROUSEL",
     "Four liners in a 14-hour carousel near RadialDisk04."),
    (72.0, "THE ARK DRILL",
     "threat-level 1.0: Sen's full ARK-mode, ghost orbit, 14 minutes."),
    (84.0, "MID-WEEK REFUEL",
     "Mobile Operations Bay detaches for a 14-hour patrol, then re-docks."),
    (96.0, "BOARDING SCHOOL TRANSIT",
     "School Bus and both Havens run a formation evacuation drill."),
    (112.0, "THORNWALL DEPLOYMENT",
     "2,744 mines deployed; Shepherds extend 1.4 km shield umbrellas."),
    (126.0, "BROADCAST TEST",
     "56 km antenna pulse; the fleet aligns running lights in salute."),
    (140.0, "THE DAZZLE CASCADE",
     "threat-level 0.8 for 2 seconds, cascading down over 5 seconds."),
    (168.0, "WEEK ENDS", "Seamless loop back to hour 0."),
)

# (hour, threat-level) — the keyed threat curve behind those events.
THREAT_KEYS = (
    (0.0, 0.0),
    (7.0, 0.0), (7.0 + 14.0 / 3600.0, 0.5), (7.02, 0.0),
    (14.0, 0.0), (14.05, 0.2), (14.2, 0.0),
    (72.0, 0.0), (72.02, 1.0), (72.25, 1.0), (72.35, 0.0),
    (140.0, 0.0), (140.001, 0.8), (140.003, 0.0),
    (168.0, 0.0),
)
THORNWALL_MINES = 2_744  # 14^3, deployed at hour 112 and left in place
THORNWALL_DEPLOY_HOUR = 112.0
MINE_DIAMETER = 140.0

# --- Collection hierarchy ---------------------------------------------------

DISK_COLLECTIONS = (
    ("RD01_Factories", ("L1_", "Cargo_Pillar_")),
    ("RD02_Government", ("L2_",)),
    ("RD03_DataLake_Diplomatic", ("L3_",)),
    ("RD04_Residential_Sanctuary", ("L4_",)),
    ("RD05_Residential", ("L5_", "R05_")),
    ("RD06_Residential", ("L6_", "R06_")),
    ("RD07_Civics_CathedralOfLight", ("L7_",)),
)

HELIX_PREFIXES = ("Tower_Sec", "Zenith_Sec")
DIAMOND_OBJECTS = ("Leavitt_Diamond_Cap", "Haas_Diamond_Cap")
DIAMOND_RING_SUFFIXES = ("_Diamond_Up", "_Diamond_Dn")
LEGACY_PREFIXES = ("Airport_Truss",)
LEGACY_OBJECTS = ("L2_Airport_Ring",)  # the Old Arrivals Ring

MASTER_FILENAME = "CIVITAS_CITY_MASTER.blend"

# --- Export manifest --------------------------------------------------------
# (glb stem, collection name)

EXPORTS = (
    ("CIVITAS_ARCOLOGY", "FYNYGRYF_ARCOLOGY"),
    ("CIVITAS_SHIP_SenMaurader", "Fleet_Sen_Maurader"),
    ("CIVITAS_SHIP_SenFastTransport", "Sen_Fast_Transport"),
    ("CIVITAS_SHIP_Commercial_Liner_Sovereign", "Commercial_Liner_Sovereign"),
    ("CIVITAS_FLEET_Commercial", COMMERCIAL_COLLECTION),
    ("CIVITAS_FLEET_Civilian", "Branch_Civilian"),
    ("CIVITAS_SHIP_Airport_210KM", "The_Airport_210KM"),
    ("CIVITAS_SHIP_RoyalYacht", "Royal_Yacht"),
    ("CIVITAS_SHIP_SchoolBus", "School_Bus"),
    ("CIVITAS_SHIP_HelixShuttle", "Helix_Shuttle"),
    ("CIVITAS_SHIP_CargoMining", "Cargo_Mining"),
    ("CIVITAS_SHIP_MobileOperationsBay", "Mobile_Operations_Bay"),
    ("CIVITAS_SHIP_Broadcast_56KM", "CIVITAS_BROADCAST"),
    ("CIVITAS_SHIP_BoardingSchool_200KM", "CIVITAS_BOARDING_SCHOOL"),
    ("CIVITAS_SHIP_Ark", "CIVITAS_ARK"),
    ("CIVITAS_FLEET_Military", "Branch_Military"),
    ("CIVITAS_FLEET_TacticalReserve", "Branch_TacticalReserve"),
    ("CIVITAS_FLEET_AutonomousEcology", "Branch_AutonomousEcology"),
    ("CIVITAS_CROSS_SECTION_Axial", "CrossSection_Axial"),
    ("CIVITAS_CROSS_SECTION_Radial", "CrossSection_Radial"),
    ("CIVITAS_CROSS_SECTION_ZoneA", "CrossSection_ZoneA"),
    ("CIVITAS_CROSS_SECTION_ZoneB", "CrossSection_ZoneB"),
    ("CIVITAS_CROSS_SECTION_ZoneC", "CrossSection_ZoneC"),
    ("CIVITAS_CORE_DISKS", "CIVITAS_CORE_DISKS"),
    ("CIVITAS_HELIX_TOWER", "CIVITAS_HELIX_TOWER"),
    ("CIVITAS_ARCOLOGY_Dragon_Coils", "Arcology_Dragon_Coils"),
    ("CIVITAS_ARCOLOGY_Dragon_Screens", "Arcology_Dragon_Screens"),
)
DRACO_LEVEL = 6
# glTF samples animation frame by frame, and the week is 14,515,200 frames.
# One sample every 3,600 frames (150 s of city time) gives 4,032 samples per
# object per week: enough for orbits and transformations, small enough to ship.
EXPORT_ANIM_STEP = 3_600
