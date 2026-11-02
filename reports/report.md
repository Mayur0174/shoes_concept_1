# Soletta CAD build report (full quality)

Elapsed: 289.3 s. Grid resolution (mm): {'body': 0.35, 'outsole': 0.25, 'laces': 0.22}

| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |
|---|---|---|---|---|---|---|---|
| body | 2,856,768 | True | True | 1 | 1255.4 | 298.2 x 133.8 x 106.9 | 12.9% |
| outsole | 2,437,892 | True | True | 1 | 106.6 | 291.9 x 112.8 x 22.8 | 24.5% |
| laces | 932,248 | True | True | 1 | 19.8 | 96.3 x 80.1 x 55.0 | 15.3% |
| dial (each) | 18,948 | True | True | 1 | 5.6 | 32.0 x 32.0 x 8.0 | 16.6% |
| printable shoe (body+outsole) | 1,303,756 | True | True | 1 | 1362.0 | 298.2 x 133.8 x 114.9 | 19.0% |

## Body wall thickness (SDF ray sampling)

| samples | p01 | p05 | median | share < 2.5 mm |
|---|---|---|---|---|
| 2433 | 2.18 | 3.51 | 10.05 | 1.44% |

Thin samples are expected on the 1.5 mm cables, guide sleeves and eyelet rims, which are features rather than walls.

## Dial frames

| Dial | Origin (mm) | Axis | Seat height |
|---|---|---|---|
| L1 | [185.86, 54.75, 45.74] | [-0.015, 0.864, 0.504] | 9.0 |
| L2 | [132.03, 45.21, 51.76] | [0.003, 0.991, -0.132] | 9.0 |
| L3 | [69.02, 42.66, 63.87] | [0.004, 1.0, -0.029] | 3.99 |
| R1 | [185.66, -52.43, 45.73] | [-0.036, -0.863, 0.504] | 9.0 |
| R2 | [132.02, -39.21, 51.76] | [0.002, -0.991, -0.132] | 9.0 |
| R3 | [69.1, -41.24, 63.87] | [0.023, -0.999, -0.029] | 3.98 |

## Warnings

- outsole: removed 12 floating fragment(s)
- laces: removed 5 floating fragment(s)
