# Soletta CAD build report (full quality)

Elapsed: 271.2 s. Grid resolution (mm): {'body': 0.35, 'outsole': 0.25, 'laces': 0.22}

| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |
|---|---|---|---|---|---|---|---|
| body | 4,172,720 | True | True | 1 | 1075.5 | 295.7 x 140.4 x 131.6 | 10.9% |
| outsole | 3,019,990 | True | True | 1 | 151.4 | 291.9 x 121.1 x 28.2 | 26.2% |
| tongue as fitted (separate part) | 981,068 | True | True | 1 | 33.1 | 126.7 x 51.2 x 66.9 | 39.5% |
| tongue, flat print | 620 | True | True | 1 | 33.7 | 178.6 x 52.0 x 5.0 | 0.0% |
| dial housing (each) | 8,790 | True | True | 1 | 2.7 | 30.6 x 33.4 x 11.0 | 0.3% |
| dial spool (each) | 6,560 | True | True | 1 | 1.6 | 21.6 x 21.6 x 10.7 | 4.7% |
| dial knob (each) | 14,088 | True | True | 1 | 2.2 | 26.0 x 26.0 x 4.9 | 6.3% |
| printable shoe (body+outsole), reloaded STL | 1,202,550 | True | True | 1 | 1168.8 | 295.7 x 140.4 x 138.1 | 17.2% |

## Body wall thickness (SDF ray sampling)

| samples | p01 | p05 | median | share < 2.5 mm |
|---|---|---|---|---|
| 3647 | 1.55 | 2.25 | 10.05 | 28.79% |

Thin samples are expected on the cable channel sheaths (4 mm tube, 1.6 mm bore), the inner tongue, guide clips and eyelet rims, which are features rather than walls.

## Function checks on the printable STL

| check | value |
|---|---|
| lacing guide bore 1 open, min clearance mm | 1.1 |
| lacing guide bore 2 open, min clearance mm | 1.1 |
| lacing guide bore 3 open, min clearance mm | 1.1 |
| lacing guide bore 4 open, min clearance mm | 1.1 |
| lacing guide bore 5 open, min clearance mm | 1.1 |
| lacing guide bore 6 open, min clearance mm | 1.1 |
| lacing guide bore 7 open, min clearance mm | 1.1 |
| lacing guide bore 8 open, min clearance mm | 1.1 |
| lacing guide bore 9 open, min clearance mm | 1.1 |
| lacing guide bore 10 open, min clearance mm | 1.1 |
| lacing guide bore 11 open, min clearance mm | 1.1 |
| lacing guide bore 12 open, min clearance mm | 1.1 |
| lacing guide bore 13 open, min clearance mm | 1.1 |
| lacing guide bore 14 open, min clearance mm | 1.1 |
| lacing guide bore 15 open, min clearance mm | 1.1 |
| dial L1 line length incl. guides mm | 230.0 |
| dial L2 line length incl. guides mm | 245.0 |
| dial L3 line length incl. guides mm | 262.0 |
| throat slot open from footbed to top, min clearance mm | 2.0 |
| tongue (sliding part) vs shoe min clearance mm | 0.56 |
| tongue glue flap distance to vamp, max mm | 0.0 |

## Dial mechanism checks (exact B-rep)

| check | value |
|---|---|
| spool_vs_knob_mm3 | 0.0 |
| engaged_rest_spool_vs_housing_mm3 | 0.0 |
| engaged_knob_vs_housing_mm3 | 0.0 |
| released_spin_max_interference_mm3 | 0.0 |
| engaged_turning_pawl_flex_overlap_mm3 | 1.115 |
| tooth_engagement_mm | 0.8 |
| clicks_per_turn | 24 |
| cable_per_turn_mm_each_end | 45.9 |
| release_lift_mm | 3.2 |
| stack_height_mm | 15.0 |

## Dial frames

| Dial | Origin (mm) | Axis | Seat height |
|---|---|---|---|
| L1 | [176.03, 76.94, 41.55] | [-0.042, 0.999, -0.02] | 7.0 |
| L2 | [121.63, 72.41, 51.35] | [-0.016, 0.999, -0.028] | 7.0 |
| L3 | [56.95, 76.7, 80.36] | [0.128, 0.86, 0.494] | 7.0 |

## Warnings

- body: removed 6 floating fragment(s)
- outsole: removed 16 floating fragment(s)
