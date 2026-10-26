"""Offline-testable sizes, assembly placement and acceptance for Stackable Bin Rack.

Units: millimetres. Source: ../../stackable-bin-rack.scad
Current source identity is recorded in SOURCE_SHA256 below.
"""
from __future__ import annotations

SOURCE_SHA256 = "BCF8E5D5388478CD60DC3BD1944C13579CE0F58C3AAB314F0B9A3D16F40083A2"
CELL = (120.0, 124.0, 91.0)  # plate depth Y, plate width X, stack pitch Z
PLATE_TRIM = 0.07
PLATE_T = 8.0
SIDE_RAIL = 8.0
BIN1 = (100.0, 80.0, 135.0)
TIP_R, SOCKET_R = 2.0, 2.1
SOCKET_DEPTH, TIP_H = 6.0, 5.0

# mesh volumes from OpenSCAD Manifold export of the 1x1x1 rebuild (2026-10-25)
SCAD_VOL = {"cap": 66133.0, "frame": 165331.0, "bin": 128325.0}
SCAD_SIZE = {
    "cap": (124.0, 119.93, 8.0),
    "frame": (124.0, 124.93, 96.0),
    "bin": (100.0, 80.0, 135.0),
}


def validate(len_n: int, wid_n: int, hgt_n: int, socket_r: float = SOCKET_R, tip_r: float = TIP_R) -> None:
    for name, n in (("len_n", len_n), ("wid_n", wid_n), ("hgt_n", hgt_n)):
        if n < 1 or n != int(n):
            raise ValueError(f"{name} must be a whole number >= 1")
    if socket_r <= tip_r:
        raise ValueError("socket_r must be greater than tip_r")
    if SOCKET_DEPTH <= TIP_H:
        raise ValueError("socket_depth must be greater than tip_h")


def pitch_y() -> float:
    return CELL[0] - PLATE_TRIM


def span(n: int) -> float:
    return (n - 1) * BIN1[0] + CELL[0]


def plate_w(wid_n: int) -> float:
    return CELL[1] + (wid_n - 1) * 100.0


def post_top(hgt_n: int) -> float:
    return CELL[2] + (hgt_n - 1) * 80.0


def bin_size(n: int, wid_n: int = 1, hgt_n: int = 1) -> tuple[float, float, float]:
    return (BIN1[0] * n, BIN1[1] * hgt_n, BIN1[2] + (wid_n - 1) * 100.0)


def row_sum(row: list[int]) -> int:
    return sum(row)


def packed_span(row: list[int]) -> float:
    return sum(span(n) - PLATE_TRIM for n in row) + PLATE_TRIM


def packed_before(row: list[int], index: int) -> float:
    return sum(span(n) - PLATE_TRIM for n in row[:index])


def asm_items(
    spec: list[list[int]],
    bins: bool = True,
    wid_n: int = 1,
    hgt_n: int = 1,
) -> list[tuple[str, int, tuple[float, float, float]]]:
    """Return SCAD assembly entries, with optional rack width/height cell counts.

    Rows share a nonnegative rack datum. ``wid_n`` is carried by the part
    geometry; ``hgt_n`` changes the vertical pitch between rows.
    """
    if not spec:
        raise ValueError("asm_spec is empty")
    if any(not row for row in spec):
        raise ValueError("asm_spec rows must not be empty")
    for row in spec:
        for n in row:
            if n < 1 or n != int(n):
                raise ValueError("asm_spec cells must be positive whole numbers")
    validate(row_sum(spec[0]), wid_n, hgt_n)
    if any(row != spec[0] for row in spec):
        raise ValueError("every asm_spec row must use the same part partition")
    row_width = packed_span(spec[0])
    if any(abs(packed_span(row) - row_width) > 1e-9 for row in spec):
        raise ValueError("every asm_spec row must have the same physical span")
    items: list[tuple[str, int, tuple[float, float, float]]] = []
    z_pitch = post_top(hgt_n)
    for r, row in enumerate(spec):
        for i, n in enumerate(row):
            y = packed_span(row) - span(n) - packed_before(row, i)
            kinds = ("frame", "bin") if bins else ("frame",)
            for kind in kinds:
                items.append((kind, n, (0.0, y, r * z_pitch)))
    top = spec[-1]
    for i, n in enumerate(top):
        y = packed_span(top) - span(n) - packed_before(top, i)
        items.append(("cap", n, (0.0, y, len(spec) * z_pitch)))
    return items


def part_pose(kind: str, n: int, wid_n: int = 1) -> tuple[tuple[tuple[float, float, float], ...], tuple[float, float, float]]:
    """Rotation columns (images of +X,+Y,+Z) and translation of the print-pose part in the assembly slot."""
    if kind == "frame":
        return ((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0.0, 0.0, 0.0)
    if kind == "cap":
        return ((1, 0, 0), (0, -1, 0), (0, 0, -1)), (0.0, span(n), PLATE_T)
    if kind == "bin":
        W, D, H = bin_size(n, wid_n, 1)
        return ((0, -1, 0), (0, 0, 1), (-1, 0, 0)), (plate_w(wid_n) - SIDE_RAIL, (span(n) + W) / 2.0, PLATE_T)
    raise ValueError(kind)


def assembly_pose(
    kind: str,
    n: int,
    wid_n: int = 1,
    hgt_n: int = 1,
) -> tuple[tuple[tuple[float, float, float], ...], tuple[float, float, float]]:
    """Return the pose for one assembled rack unit.

    ``part_pose`` remains the relative slot pose used by the legacy mixed
    assembly contract.  This helper adds the global stack height needed to put
    a cap on top of one frame.  Rotation tuples retain the existing column
    convention: tuple item ``j`` is the world image of local axis ``j``.
    """
    rot, t = part_pose(kind, n, wid_n)
    if kind == "cap":
        t = (t[0], t[1], t[2] + post_top(hgt_n))
    return rot, t


def expected_size(kind: str, n: int = 1, wid_n: int = 1, hgt_n: int = 1) -> tuple[float, float, float]:
    if kind == "cap":
        return (plate_w(wid_n), span(n) - PLATE_TRIM, PLATE_T)
    if kind == "frame":
        return (plate_w(wid_n), span(n) + 4.93, post_top(hgt_n) + TIP_H)  # tab sticks 4.93 in -Y
    if kind == "bin":
        return bin_size(n, wid_n, hgt_n)
    raise ValueError(kind)
