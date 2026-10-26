"""Render the six public catalogue images from the project SCAD source."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "stackable-bin-rack.scad"
OPENSCAD = os.environ.get("OPENSCAD_BIN", "openscad.com")
PARTS = ("cap", "frame", "bin", "stand", "stand_bin")


def public_path(path: Path) -> str:
    """Return a repository-relative path for reproducible manifest provenance."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return "<temporary>/bin-use.scad"


def manifest_command(command: list[str]) -> list[str]:
    return [
        "${OPENSCAD_BIN:-openscad.com}" if i == 0 else public_path(Path(item))
        if (item.startswith(str(ROOT)) or item.endswith("bin-use.scad"))
        else item
        for i, item in enumerate(command)
    ]


def render_command(part: str, image: Path, source: Path) -> list[str]:
    return [
        OPENSCAD,
        "--backend=manifold",
        "--hardwarnings",
        "-D",
        f'part="{part}"',
        "-D",
        "size=[1,1,1]",
        "--render",
        "--imgsize=1280,900",
        "--viewall",
        "--autocenter",
        "--projection=o",
        "--camera=0,0,0,65,0,35,400",
        "--colorscheme=Tomorrow",
        "-o",
        str(image),
        str(source),
    ]


def run_render(command: list[str], log: Path, *, cwd: Path) -> None:
    result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0 or "ERROR:" in result.stderr:
        raise RuntimeError(f"OpenSCAD render failed; see {log}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "parts")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper()
    records = []
    for part in PARTS:
        image = output / f"{part}.png"
        command = render_command(part, image, SOURCE)
        run_render(command, output / f"{part}-render.log", cwd=ROOT)
        records.append(
            {
                "part": part,
                "selector": part,
                "image": image.name,
                "bytes": image.stat().st_size,
                "source_sha256": source_hash,
                "command": manifest_command(command),
            }
        )

    usage_image = output / "bin-use.png"
    usage_log = output / "bin-use-render.log"
    with tempfile.TemporaryDirectory(prefix="stackable-bin-rack-catalogue-") as temp_dir:
        wrapper = Path(temp_dir) / "bin-use.scad"
        wrapper.write_text(
            f'include <{SOURCE.as_posix()}>;\n' "bin_in_frame(1);\n", encoding="utf-8"
        )
        command = render_command("__catalogue_none__", usage_image, wrapper)
        run_render(command, usage_log, cwd=ROOT)
        records.append(
            {
                "part": "bin",
                "selector": "bin_in_frame",
                "image": usage_image.name,
                "bytes": usage_image.stat().st_size,
                "source_sha256": source_hash,
                "command": manifest_command(command),
            }
        )

    (output / "render-manifest.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
