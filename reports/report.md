# Soletta CAD build report (full quality)

Elapsed: 391.3 s. Grid resolution (mm): {'body': 0.35, 'outsole': 0.25, 'laces': 0.22}

| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |
|---|---|---|---|---|---|---|---|
| body | 3,292,324 | True | True | 1 | 938.3 | 298.4 x 123.7 x 106.9 | 12.8% |
| outsole | 2,522,666 | True | True | 1 | 120.9 | 291.8 x 106.4 x 22.8 | 25.9% |
| tongue as fitted (separate part) | 1,103,590 | True | True | 1 | 29.5 | 133.0 x 50.0 x 55.2 | 32.9% |
| tongue, flat print | 620 | True | True | 1 | 24.7 | 172.4 x 48.0 x 5.0 | 0.0% |
| dial housing (each) | 8,790 | True | True | 1 | 2.7 | 30.6 x 33.4 x 11.0 | 0.3% |
| dial spool (each) | 6,560 | True | True | 1 | 1.6 | 21.6 x 21.6 x 10.7 | 4.7% |
| dial knob (each) | 14,088 | True | True | 1 | 2.2 | 26.0 x 26.0 x 4.9 | 6.3% |
| printable shoe (body+outsole), reloaded STL | 1,231,344 | True | True | 1 | 1054.3 | 298.4 x 123.7 x 114.7 | 17.1% |

## Body wall thickness (SDF ray sampling)

| samples | p01 | p05 | median | share < 2.5 mm |
|---|---|---|---|---|
| 3442 | 1.55 | 2.15 | 4.55 | 38.03% |

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
| dial L1 line length incl. guides mm | 219.0 |
| dial L2 line length incl. guides mm | 218.0 |
| dial L3 line length incl. guides mm | 280.0 |
| throat slot open from footbed to top, min clearance mm | 2.0 |
| tongue (sliding part) vs shoe min clearance mm | 0.6 |
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
| L1 | [175.73, 70.01, 35.11] | [-0.055, 0.995, -0.082] | 6.99 |
| L2 | [127.96, 63.28, 40.98] | [-0.002, 1.0, -0.001] | 3.9 |
| L3 | [57.73, 62.2, 52.05] | [-0.012, 0.996, -0.085] | 7.0 |

## Warnings

- outsole: removed 7 floating fragment(s)
- tongue: removed 2 floating fragment(s)
