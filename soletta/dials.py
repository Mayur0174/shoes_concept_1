"""Rotary tension dials as true B-rep solids (CadQuery): knurled grip ring,
recessed centre cap with hex drive and position notch, radial top grooves,
snap socket for the bracket peg and an underside relief."""
import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf, gp_Ax3, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform


def make_dial(dp):
    R = dp["diameter"] / 2
    T = dp["thickness"]
    n_fl = dp["knurl_count"]
    sock_r = dp["peg_diameter"] / 2 + dp["peg_clearance"]
    sock_d = dp["socket_depth"]

    dial = cq.Workplane("XY").circle(R).extrude(T)
    dial = dial.faces(">Z").edges().chamfer(1.2)
    dial = dial.faces("<Z").edges().fillet(0.6)

    # fine radial knurling on the grip ring
    flutes = (cq.Workplane("XY").workplane(offset=1.0)
              .polarArray(R + 0.15, 0, 360, n_fl).circle(0.55).extrude(T - 2.6))
    dial = dial.cut(flutes)

    # centre cap seated in a recess with a 0.3 mm shadow gap
    cap_r = dp["cap_diameter"] / 2
    dial = dial.cut(cq.Workplane("XY").workplane(offset=T - 1.0).circle(cap_r + 0.3).extrude(1.5))
    cap = cq.Workplane("XY").workplane(offset=T - 1.0).circle(cap_r).extrude(1.0)
    cap = cap.faces(">Z").edges().fillet(0.6)
    dial = dial.union(cap)
    dial = dial.cut(cq.Workplane("XY").workplane(offset=T - 0.7).polygon(6, 4.4).extrude(1.0))
    dial = dial.cut(cq.Workplane("XY").workplane(offset=T - 0.5)
                    .center(cap_r * 0.55, 0).rect(cap_r * 0.55, 1.0).extrude(1.0))

    # radial grip grooves on the top ring
    ring_mid = (cap_r + 0.3 + R - 1.2) / 2
    grooves = (cq.Workplane("XY").workplane(offset=T - 0.5)
               .polarArray(ring_mid, 0, 360, dp["top_groove_count"])
               .rect(R - 1.2 - cap_r - 1.4, 0.9).extrude(1.0))
    dial = dial.cut(grooves)

    # underside: peg socket with lead-in chamfer + relief ring
    dial = dial.cut(cq.Workplane("XY").circle(sock_r).extrude(sock_d))
    dial = dial.cut(cq.Workplane("XY").circle(sock_r + 0.5).workplane(offset=0.5).circle(sock_r).loft())
    dial = dial.cut(cq.Workplane("XY").circle(R - 3.0).circle(sock_r + 2.5).extrude(1.0))
    return dial.val()


def place(shape, origin, ez, ex):
    ax = gp_Ax3(gp_Pnt(*map(float, origin)), gp_Dir(*map(float, ez)), gp_Dir(*map(float, ex)))
    tr = gp_Trsf()
    tr.SetTransformation(ax)
    tr = tr.Inverted()
    return cq.Shape.cast(BRepBuilderAPI_Transform(shape.wrapped, tr, True).Shape())


def build_dials(m, log=print):
    dp = m.prof.p["dials"]
    base = make_dial(dp)
    out = []
    for d in m.dials:
        fr = d["frame"]
        placed = place(base, d["origin"], fr.ez, fr.ex)
        out.append(dict(name=d["name"], side=d["side"], shape=placed, frame=fr, origin=d["origin"]))
    log("dials: %d B-rep dials, volume each %.0f mm^3" % (len(out), base.Volume()))
    return base, out


def tessellate(shape, tol=0.02, ang=0.15):
    verts, tris = shape.tessellate(tol, ang)
    V = np.array([(v.x, v.y, v.z) for v in verts], float)
    F = np.array(tris, np.int64)
    return V, F
