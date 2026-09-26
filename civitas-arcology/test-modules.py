"""Offline checks for the pure DDCC module ladder math."""

from __future__ import annotations

from civitas.modules import module_slots


SPANS = {
    "RD01": (-11200.0, -8100.0, 11),   # 3100m span / 280m = 11 modules
    "RD02": (-7400.0, 2900.0, 36),     # 10300m span / 280m = 36 modules
    "RD03": (2900.0, 8306.0, 19),     # 5406m span / 280m = 19 modules
    "RD04": (8556.0, 15210.0, 23),    # 6654m span / 280m = 23 modules
    "RD05": (15460.0, 18560.0, 11),   # 3100m span / 280m = 11 modules
    "RD06": (18810.0, 22134.0, 11),   # 3324m span / 280m = 11 modules
    "RD07": (22384.0, 28036.0, 20),   # 5652m span / 280m = 20 modules
    "tower": (-27900.0, -7400.0, 13), # 3800m span / 280m = 13 modules (after exclusion)
    "zenith": (28036.0, 48536.0, 53),  # 20500m span / 280m = 73 modules, minus 20 for Cathedral exclusion (5600m / 280m = 20)
}


for name, (z_min, z_max, expected_count) in SPANS.items():
    # Apply floor exclusions for base14 alignment
    floor_exclusions = None
    if name == "tower":
        # No floors below RadialDisk01 in convergence tower
        floor_exclusions = [(-27_900.0, -11_200.0)]
    elif name == "zenith":
        # No floors above Cathedral of Light in Sovereignty tower
        # Cathedral sits on top of RD07 (28036-33636)
        floor_exclusions = [(28_036.0, 33_636.0)]
    
    slots = module_slots(z_min, z_max, floor_exclusions)
    # For tower and zenith, the expected count will be lower due to exclusions
    if name == "tower":
        # Tower has exclusions, so it will have fewer modules
        assert len(slots) == expected_count, (name, len(slots))
    elif name == "zenith":
        # Zenith has Cathedral exclusion (sits on top of RD07)
        assert len(slots) == expected_count, (name, len(slots))
    else:
        assert len(slots) == expected_count, (name, len(slots))
    
    assert all(slot["z_max"] <= z_max for slot in slots)
    if slots:
        assert slots[0]["floor_first"] == 1
        for previous, current in zip(slots, slots[1:]):
            assert current["floor_first"] == previous["floor_last"] + 1
        for slot in slots:
            assert slot["module_floors"] == (
                slot["floor_last"] - slot["floor_first"] + 1
            )
        assert all(slot["module_floors"] == 20 for slot in slots[:-1])
        assert slots[-1]["floor_last"] >= slots[-1]["floor_first"]
        assert all(
            slot["z_max"] - slot["z_min"] == 280.0
            for slot in slots[:-1]
        )
        assert slots[-1]["z_max"] - slots[-1]["z_min"] <= 560.0
        assert slots[-1]["z_max"] == z_max
    
    if name in ["tower", "zenith"]:
        print(f"{name}: {len(slots)} modules (with exclusions), floors 1-{slots[-1]['floor_last'] if slots else 0}")
    else:
        print(f"{name}: {len(slots)} modules, floors 1-{slots[-1]['floor_last']}")

print("module ladder checks passed")
