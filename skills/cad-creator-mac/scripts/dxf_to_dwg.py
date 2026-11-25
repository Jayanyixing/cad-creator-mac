#!/usr/bin/env python3
"""Headless DXF -> DWG converter for macOS via AutoCAD's AcCoreConsole."""

import argparse
import glob
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

DWG_VERSIONS = {"R14", "2000", "2004", "2007", "2010", "2013", "2018"}


def find_accoreconsole() -> str:
    """Return newest AutoCAD for Mac AcCoreConsole binary path."""
    pattern = "/Applications/Autodesk/AutoCAD */AutoCAD *.app/Contents/Helpers/AcCoreConsole.app/Contents/MacOS/AcCoreConsole"
    matches = sorted(glob.glob(pattern), reverse=True)
    if not matches:
        raise FileNotFoundError(
            "AcCoreConsole not found under /Applications/Autodesk/AutoCAD */"
        )
    return matches[0]


def run_console(console: str, drawing: Path, script: Path, workdir: Path, readonly: bool, timeout: int) -> str:
    """Execute AcCoreConsole in an isolated working directory and return stdout."""
    cmd = [console, "/i", str(drawing), "/s", str(script)]
    if readonly:
        cmd.append("/readonly")
    proc = subprocess.run(
        cmd,
        cwd=str(workdir),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if proc.returncode != 0:
        tail = proc.stdout[-800:] if proc.stdout else "(no output)"
        raise RuntimeError(f"AcCoreConsole failed (rc={proc.returncode}):\n{tail}")
    return proc.stdout


# Leading/trailing newlines separate values from the command echoed by AutoCAD.
READBACK = r"""(princ (strcat "\n__CAD_INSUNITS=" (itoa (getvar "INSUNITS")) "\n"))
(princ (strcat "\n__CAD_TOTAL=" (itoa (if (setq _ss (ssget "_X")) (sslength _ss) 0)) "\n"))
(princ (strcat "\n__CAD_MODEL=" (itoa (if (setq _ss (ssget "_X" '((410 . "Model")))) (sslength _ss) 0)) "\n"))
(setq _count 0)
(foreach _p (dictsearch (namedobjdict) "ACAD_LAYOUT") (if (= (car _p) 3) (progn (setq _count (1+ _count)) (princ (strcat "\n__CAD_LAYOUT=" (cdr _p) "\n")))))
(princ (strcat "\n__CAD_LAYOUT_COUNT=" (itoa _count) "\n"))
"""


def readback(output: str) -> dict:
    counts = {}
    for marker, key in (("INSUNITS", "insunits"), ("TOTAL", "total_entities"),
                        ("MODEL", "model_entities"), ("LAYOUT_COUNT", "layout_count")):
        match = re.search(rf"^__CAD_{marker}=([0-9]+)$", output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"Missing {marker} in AutoCAD readback")
        counts[key] = int(match[1])
    layouts = re.findall(r"^__CAD_LAYOUT=([^\r\n]+)$", output, re.MULTILINE)
    names = {name.casefold() for name in layouts}
    if "model" not in names or len(names) != counts.pop("layout_count"):
        raise RuntimeError(f"Incomplete AutoCAD layout readback: {layouts!r}")
    return dict(counts, layouts=layouts)


def dxf_to_dwg(src_dxf: Path, dst_dwg: Path, version: str = "2018", verify: bool = True, timeout: int = 120) -> dict:
    """Convert src_dxf to native DWG atomically using isolated temp staging."""
    if dst_dwg.suffix.lower() != ".dwg":
        raise ValueError(f"Expected a .dwg output path: {dst_dwg}")
    src_dxf = src_dxf.resolve()
    dst_dwg = dst_dwg.resolve()
    if not src_dxf.is_file():
        raise FileNotFoundError(f"Input DXF not found: {src_dxf}")
    if dst_dwg.exists() and src_dxf.samefile(dst_dwg):
        raise ValueError("DXF input and DWG output must be different files")
    if dst_dwg.suffix.lower() != ".dwg":
        raise ValueError(f"Resolved output must be a .dwg file: {dst_dwg}")
    if dst_dwg.is_dir():
        raise IsADirectoryError(dst_dwg)
    if version not in DWG_VERSIONS:
        raise ValueError(f"Unsupported DWG version {version!r}; expected one of {sorted(DWG_VERSIONS)}")

    console = find_accoreconsole()
    # Stage pure-ASCII paths inside TemporaryDirectory so CJK/spaces, existing targets,
    # and AcCoreConsole's working-dir *.log files never touch the project directory.
    with tempfile.TemporaryDirectory(prefix="cadmac_d2d_") as tmp:
        tmp_dir = Path(tmp)
        tmp_in = tmp_dir / "in.dxf"
        tmp_out = tmp_dir / "out.dwg"
        save_scr = tmp_dir / "save.scr"
        shutil.copy2(src_dxf, tmp_in)
        save_scr.write_text((READBACK if verify else "") + f'(command "_.SAVEAS" "{version}" "{tmp_out.as_posix()}")\n_.QUIT\n', encoding="utf-8")

        conv_out = run_console(console, tmp_in, save_scr, tmp_dir, readonly=False, timeout=timeout)
        if not tmp_out.is_file() or tmp_out.stat().st_size == 0:
            raise RuntimeError(f"SAVEAS did not produce DWG:\n{conv_out[-800:]}")
        with tmp_out.open("rb") as stream:
            magic = stream.read(6)
        if not magic.startswith(b"AC10"):
            raise RuntimeError(f"Invalid DWG header {magic!r}")

        summary = {"version_magic": magic.decode("ascii", "replace"), "bytes": tmp_out.stat().st_size}
        if verify:
            v_scr = tmp_dir / "verify.scr"
            source = readback(conv_out)
            v_scr.write_text(READBACK + "_.QUIT\n", encoding="utf-8")
            result = readback(run_console(console, tmp_out, v_scr, tmp_dir, readonly=True, timeout=timeout))
            if source["insunits"] != result["insunits"] or set(source["layouts"]) != set(result["layouts"]):
                raise RuntimeError(f"Units or layouts changed: DXF={source!r}, DWG={result!r}")
            summary.update(result)

        dst_dwg.parent.mkdir(parents=True, exist_ok=True)
        # Stage on the destination volume; a failed cross-volume copy leaves the old DWG intact.
        with tempfile.TemporaryDirectory(dir=dst_dwg.parent, prefix=".cadmac-") as staging:
            staged = Path(staging) / "delivery.dwg"
            shutil.move(str(tmp_out), str(staged))
            os.replace(staged, dst_dwg)

    summary["output"] = str(dst_dwg)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Headless DXF to DWG via macOS AutoCAD AcCoreConsole.")
    ap.add_argument("input_dxf", type=Path)
    ap.add_argument("output_dwg", type=Path, nargs="?")
    ap.add_argument("--version", default="2018", choices=sorted(DWG_VERSIONS))
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    out = args.output_dwg if args.output_dwg else args.input_dxf.with_suffix(".dwg")
    info = dxf_to_dwg(args.input_dxf, out, version=args.version, verify=not args.no_verify, timeout=args.timeout)
    print(
        f"OK: {info['output']} ({info['bytes']} B, {info['version_magic']})"
        + (
            f" | INSUNITS={info['insunits']} total={info['total_entities']} "
            f"model={info['model_entities']} layouts={info['layouts']}"
            if not args.no_verify
            else ""
        )
    )


if __name__ == "__main__":
    main()
