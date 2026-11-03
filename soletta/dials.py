"""Place the printed ratchet dial mechanism (housing + spool + knob, see
mechanism.py) on each dial pod of the shoe body."""
import numpy as np
from OCP.gp import gp_Trsf, gp_Ax3, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
import cadquery as cq

from .mechanism import make_housing, make_spool, make_knob, check_mechanism
from .sdf import Frame


def place(shape, origin, ez, ex):
    ax = gp_Ax3(gp_Pnt(*map(float, origin)), gp_Dir(*map(float, ez)), gp_Dir(*map(float, ex)))
    tr = gp_Trsf()
    tr.SetTransformation(ax)
    tr = tr.Inverted()
    return cq.Shape.cast(BRepBuilderAPI_Transform(shape.wrapped, tr, True).Shape())


def build_dials(m, log=print):
    dp = m.prof.p["dials"]
    housing = make_housing(dp)
    spool = make_spool(dp)
    knob = make_knob(dp)
    checks = check_mechanism(housing, spool, knob, dp)
    log("dials: housing %.0f, spool %.0f, knob %.0f mm^3; checks %s"
        % (housing.Volume(), spool.Volume(), knob.Volume(), checks))
    out = []
    for d in m.dials:
        fr = d["frame"]
        th = d["theta"]
        ex = np.cos(th) * fr.ex + np.sin(th) * fr.ey      # housing +x -> cable ports
        o = fr.world(0, 0, d["seat"])
        hfr = Frame(o, fr.ez, ex_hint=ex)
        out.append(dict(name=d["name"], side=d["side"], frame=hfr, origin=o,
                        housing=place(housing, o, fr.ez, hfr.ex),
                        spool=place(spool, o, fr.ez, hfr.ex),
                        knob=place(knob, o, fr.ez, hfr.ex)))
    kit = dict(housing=housing, spool=spool, knob=knob, checks=checks)
    return kit, out


def tessellate(shape, tol=0.02, ang=0.15):
    verts, tris = shape.tessellate(tol, ang)
    V = np.array([(v.x, v.y, v.z) for v in verts], float)
    F = np.array(tris, np.int64)
    return V, F
