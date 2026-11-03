"""Printable ratcheting dial mechanism (exact B-rep, CadQuery).

Three printed parts per dial (PETG recommended, PLA+ works), no supports:

housing - screwed to the shoe's dial pod with 2 x M2 x 6 self-tapping
          screws.  Flange + cup with 24 sawtooth ratchet teeth on the floor
          ring, a slotted snap axle with a detent ridge, and two cable ports.
          Print flange-down.
spool   - three compliant pawls (printed flat on the bed so they flex
          freely), a 45 deg self-supporting flange, the cable groove with two
          knot pockets, and a hex key.  Print pawls-down.
knob    - knurled grip; its flat underside is the top wall of the cable
          groove.  Press onto the spool's hex and fix with a drop of CA glue.
          Print face-down.

Operation
  * push the knob down (click)  -> pawls sit in the teeth ring
  * turn clockwise (from above) -> pawls ride over the ramps; the spool winds
                                   both cable ends in; it clicks and holds
  * counter-clockwise           -> blocked by the radial tooth faces
  * pull the knob up (click)    -> pawls rise above the teeth, the spool spins
                                   free and the cable pays out

Dimensions are in the housing frame: z = 0 on the pod seat, +z out of the
shoe, +x towards the bisector of the two cable ports.
"""
import math

import numpy as np
import cadquery as cq

DEFAULTS = dict(
    # housing
    flange_r=18.0, flange_t=1.6, ear_r=20.6, ear_lobe_r=3.3, ear_angle=125.0,
    screw_hole_d=2.2,
    wall_ro=16.5, wall_ri=14.5, housing_top=11.0,
    teeth=24, tooth_tip_r=13.0, teeth_z=(1.6, 4.8),
    axle_r=3.0, axle_top=13.4, axle_slot_w=1.2, axle_slot_z=5.5,
    ridge_r=3.45, ridge_z=10.0, ridge_h=0.8,
    port_angle=24.0, port_w=1.8, port_z0=7.6,
    # spool
    clearance=0.2, spool_bottom=2.0,
    pawl_top=4.7, hub_r=9.6, pawl_arm=(10.6, 11.8), pawl_tip_r=13.8,
    pawl_span=75.0, pawl_count=3,
    pawl_gap=0.5, flange_rr=12.6, rim_t=0.4,
    drum_r=8.0, groove_top=11.6, hex_af=12.0, hex_h=3.0,
    knot_pocket_r=1.4, knot_pocket_at=5.5, anchor_hole_r=0.7,
    # knob
    knob_r=17.0, knob_t=8.0, hex_clearance=0.1,
    knurl_count=60, cap_d=18.0, top_groove_count=18,
    lift=3.2, cable_line_d=1.0,
)


def _p(dp):
    q = dict(DEFAULTS)
    q.update(dp.get("mechanism", {}))
    return q


def _polar(r, a_deg):
    a = math.radians(a_deg)
    return (r * math.cos(a), r * math.sin(a))


def _revolve(profile):
    return cq.Workplane("XZ").polyline(profile).close().revolve(360, (0, 0, 0), (0, 1, 0))


# ----------------------------------------------------------------------------
# Housing
# ----------------------------------------------------------------------------

def tooth_profile(q, n_sub=6):
    """Closed inner polyline of the ratchet ring (CCW).

    Within each tooth the radius ramps from the tip radius out to the wall
    going +theta, then drops back radially: a pawl moving -theta (clockwise,
    tightening) rides up the ramps; moving +theta it hits the radial faces."""
    n = q["teeth"]
    d = 360.0 / n
    r0, r1 = q["tooth_tip_r"], q["wall_ri"] + 0.05
    pts = []
    for k in range(n):
        for j in range(n_sub + 1):
            t = j / n_sub * 0.97
            pts.append(_polar(r0 + (r1 - r0) * t, k * d + t * d))
    return pts


def ear_positions(q):
    return [_polar(q["ear_r"], 180.0 + s * (180.0 - q["ear_angle"])) for s in (+1, -1)]


def make_housing(dp):
    q = _p(dp)
    ft, top = q["flange_t"], q["housing_top"]
    fl = cq.Workplane("XY").circle(q["flange_r"]).extrude(ft)
    for cx, cy in ear_positions(q):
        a = math.degrees(math.atan2(cy, cx))
        lobe = cq.Workplane("XY").center(cx, cy).circle(q["ear_lobe_r"]).extrude(ft)
        web = (cq.Workplane("XY").polyline([_polar(q["flange_r"] - 2, a - 12), (cx, cy),
                                             _polar(q["flange_r"] - 2, a + 12)]).close().extrude(ft))
        fl = fl.union(lobe).union(web)
        fl = fl.cut(cq.Workplane("XY").center(cx, cy).circle(q["screw_hole_d"] / 2).extrude(ft))
        fl = fl.cut(cq.Workplane("XY").workplane(offset=ft - 0.8).center(cx, cy)
                    .circle(q["screw_hole_d"] / 2 + 0.9).extrude(1.0))   # screw-head counterbore
    cup = cq.Workplane("XY").circle(q["wall_ro"]).extrude(top)
    cup = cup.faces(">Z").edges().fillet(0.5)
    h = fl.union(cup)
    h = h.cut(cq.Workplane("XY").workplane(offset=ft).circle(q["wall_ri"]).extrude(top))

    # ratchet ring on the floor
    z0, z1 = q["teeth_z"]
    ring = cq.Workplane("XY").workplane(offset=z0 - 0.01).circle(q["wall_ri"] + 0.3).extrude(z1 - z0 + 0.01)
    hole = (cq.Workplane("XY").workplane(offset=z0 - 0.2).polyline(tooth_profile(q)).close()
            .extrude(z1 - z0 + 0.4))
    ring = ring.cut(hole)
    h = h.union(ring)

    # slotted snap axle with a detent ridge and lead-in chamfer
    ar, rr, rz, rh = q["axle_r"], q["ridge_r"], q["ridge_z"], q["ridge_h"]
    axle = cq.Workplane("XY").workplane(offset=ft - 0.01).circle(ar).extrude(q["axle_top"] - ft)
    axle = axle.faces(">Z").edges().chamfer(0.6)
    ridge = _revolve([(ar - 0.2, rz - rh / 2 - (rr - ar)), (rr, rz - rh / 2 + 0.15),
                      (rr, rz + rh / 2 - 0.15), (ar - 0.2, rz + rh / 2 + (rr - ar))])
    axle = axle.union(ridge)
    axle = axle.cut(cq.Workplane("XY").workplane(offset=q["axle_slot_z"])
                    .rect(2 * rr + 2, q["axle_slot_w"]).extrude(q["axle_top"]))
    h = h.union(axle)

    # cable ports: slots through the wall, open at the top so the line can
    # follow the groove when the knob is lifted
    for s in (+1, -1):
        a = s * q["port_angle"]
        c = _polar((q["wall_ri"] + q["wall_ro"]) / 2, a)
        slot = (cq.Workplane("XY").workplane(offset=q["port_z0"]).center(*c)
                .rect(q["wall_ro"] - q["wall_ri"] + 3.0, q["port_w"]).extrude(top)
                .rotate((c[0], c[1], 0), (c[0], c[1], 1), a))
        h = h.cut(slot)
    return h.val()


# ----------------------------------------------------------------------------
# Spool
# ----------------------------------------------------------------------------

def pawl_layer(q):
    b, t = q["spool_bottom"], q["pawl_top"]
    hub = cq.Workplane("XY").workplane(offset=b).circle(q["hub_r"]).extrude(t - b)
    ri, ro = q["pawl_arm"]
    span = q["pawl_span"]
    d = 360.0 / q["teeth"]
    tip_end = 0.95 * d          # at rotor angle 0 the tips rest in the valleys
    for k in range(q["pawl_count"]):
        phi0 = tip_end - span + k * 360.0 / q["pawl_count"]
        arc_o = [_polar(ro, phi0 + span * 0.93 * j / 16) for j in range(17)]
        arc_i = [_polar(ri, phi0 + span * j / 16) for j in range(16, -1, -1)]
        poly = arc_o + [_polar(q["pawl_tip_r"], phi0 + span)] + arc_i
        arm = cq.Workplane("XY").workplane(offset=b).polyline(poly).close().extrude(t - b)
        web = (cq.Workplane("XY").workplane(offset=b)
               .polyline([_polar(q["hub_r"] - 0.3, phi0 - 7), _polar(ro, phi0 - 7),
                          _polar(ro, phi0 + 2), _polar(q["hub_r"] - 0.3, phi0 + 2)])
               .close().extrude(t - b))
        hub = hub.union(arm).union(web)
    return hub


def make_spool(dp):
    q = _p(dp)
    c = q["clearance"]
    b, t = q["spool_bottom"], q["pawl_top"]
    z_c0 = t + q["pawl_gap"]                       # flange cone starts above the arms
    rf, hr, rd = q["flange_rr"], q["hub_r"], q["drum_r"]
    z_c1 = z_c0 + (rf - hr)                        # 45 deg cone
    z_rim = z_c1 + q["rim_t"]
    gt = q["groove_top"]
    body = _revolve([(0.5, t - 0.01), (hr, t - 0.01), (hr, z_c0), (rf, z_c1), (rf, z_rim),
                     (rd, z_rim), (rd, gt - 0.05), (0.5, gt - 0.05)])
    s = pawl_layer(q).union(body)
    hexk = cq.Workplane("XY").workplane(offset=gt - 0.06).polygon(6, q["hex_af"] / math.cos(math.pi / 6)).extrude(q["hex_h"] + 0.06)
    hexk = hexk.faces(">Z").edges().chamfer(0.4)
    s = s.union(hexk)

    # blind axle bore (closed on top) with lead-in and two detent grooves
    br = q["axle_r"] + c
    s = s.cut(cq.Workplane("XY").workplane(offset=b - 0.1).circle(br)
              .extrude(q["axle_top"] + 0.6 - b + 0.1))
    s = s.cut(cq.Workplane("XY").workplane(offset=b - 0.1).circle(br + 0.6)
              .workplane(offset=0.8).circle(br).loft())
    gr = q["ridge_r"] + c
    hh = q["ridge_h"] / 2 + c
    for zc in (q["ridge_z"], q["ridge_z"] - q["lift"]):
        s = s.cut(_revolve([(br - 0.1, zc - hh - (gr - br)), (gr, zc - hh + 0.15),
                            (gr, zc + hh - 0.15), (br - 0.1, zc + hh + (gr - br))]))

    # cable anchors: radial hole from the groove into a knot pocket that is
    # open on the underside (thread in, pull out below, knot, pull back)
    zh = 0.5 * (z_rim + gt)
    for a in (90.0, 270.0):
        px, py = _polar(q["knot_pocket_at"], a)
        s = s.cut(cq.Workplane("XY").workplane(offset=b - 0.1).center(px, py)
                  .circle(q["knot_pocket_r"]).extrude(zh - b + 0.8))
        hole = (cq.Workplane("YZ").center(0, zh).circle(q["anchor_hole_r"]).extrude(rd + 1.0)
                .translate((q["knot_pocket_at"] - 0.5, 0, 0)).rotate((0, 0, 0), (0, 0, 1), a))
        s = s.cut(hole)
    return s.val()


# ----------------------------------------------------------------------------
# Knob
# ----------------------------------------------------------------------------

def make_knob(dp):
    q = _p(dp)
    R, T, z = q["knob_r"], q["knob_t"], q["groove_top"]
    k = cq.Workplane("XY").workplane(offset=z).circle(R).extrude(T)
    k = k.faces(">Z").edges().chamfer(1.2)
    k = k.faces("<Z").edges().chamfer(0.6)
    flutes = (cq.Workplane("XY").workplane(offset=z + 1.0)
              .polarArray(R + 0.15, 0, 360, q["knurl_count"]).circle(0.55).extrude(T - 2.6))
    k = k.cut(flutes)
    cap_r = q["cap_d"] / 2
    top = z + T
    k = k.cut(cq.Workplane("XY").workplane(offset=top - 1.0).circle(cap_r + 0.3).extrude(1.5))
    cap = cq.Workplane("XY").workplane(offset=top - 1.0).circle(cap_r).extrude(1.0)
    cap = cap.faces(">Z").edges().fillet(0.6)
    k = k.union(cap)
    k = k.cut(cq.Workplane("XY").workplane(offset=top - 0.5)
              .center(cap_r * 0.55, 0).rect(cap_r * 0.55, 1.0).extrude(1.0))      # index mark
    ring_mid = (cap_r + 0.3 + R - 1.2) / 2
    grooves = (cq.Workplane("XY").workplane(offset=top - 0.5)
               .polarArray(ring_mid, 0, 360, q["top_groove_count"])
               .rect(R - 1.2 - cap_r - 1.4, 0.9).extrude(1.0))
    k = k.cut(grooves)
    # hex socket for the spool key
    af = q["hex_af"] + 2 * q["hex_clearance"]
    k = k.cut(cq.Workplane("XY").workplane(offset=z - 0.1)
              .polygon(6, af / math.cos(math.pi / 6)).extrude(q["hex_h"] + 0.4))
    return k.val()


# ----------------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------------

def _inter_vol(a, b):
    try:
        return float(a.intersect(b).Volume())
    except Exception:  # noqa: BLE001
        return float("nan")


def _rot(s, ang):
    return s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), float(ang))


def check_mechanism(housing, spool, knob, dp):
    """Interference checks between the printed parts."""
    q = _p(dp)
    up = cq.Vector(0, 0, q["lift"])
    d = 360.0 / q["teeth"]
    out = {}
    out["spool_vs_knob_mm3"] = round(_inter_vol(spool, knob), 3)
    out["engaged_rest_spool_vs_housing_mm3"] = round(_inter_vol(housing, spool), 3)
    out["engaged_knob_vs_housing_mm3"] = round(_inter_vol(housing, knob), 3)
    free = [_inter_vol(housing, _rot(spool, a).translate(up)) for a in np.linspace(0, d, 6)]
    free.append(_inter_vol(housing, knob.translate(up)))
    out["released_spin_max_interference_mm3"] = round(max(free), 3)
    tight = [_inter_vol(housing, _rot(spool, -a)) for a in np.linspace(0, d, 7)[1:-1]]
    out["engaged_turning_pawl_flex_overlap_mm3"] = round(max(tight), 3)
    out["tooth_engagement_mm"] = round(q["pawl_tip_r"] - q["tooth_tip_r"], 2)
    out["clicks_per_turn"] = q["teeth"]
    out["cable_per_turn_mm_each_end"] = round(2 * math.pi * (q["drum_r"] + 0.5 * q["cable_line_d"]), 1)
    out["release_lift_mm"] = q["lift"]
    out["stack_height_mm"] = round(q["groove_top"] + q["knob_t"], 1)
    return out


def seat_info(dp):
    """Numbers the shoe body needs to build the pod for this housing."""
    q = _p(dp)
    return dict(flange_r=q["flange_r"], ear_r=q["ear_r"], ear_lobe_r=q["ear_lobe_r"], ears=ear_positions(q),
                port_angle=q["port_angle"], port_z=0.5 * (q["groove_top"] + q["port_z0"]) + 0.4,
                wall_ro=q["wall_ro"], knob_r=q["knob_r"], stack=q["groove_top"] + q["knob_t"],
                knob_z=q["groove_top"], knob_t=q["knob_t"], cap_r=q["cap_d"] / 2,
                screw_pilot_d=1.6)
