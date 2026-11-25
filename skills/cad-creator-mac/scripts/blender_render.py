#!/usr/bin/env python3
"""Headless SketchUp-export/scene importer and renderer for macOS Blender (Metal Cycles)."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
IMPORT_HANDLERS = {
    ".obj": "obj",
    ".glb": "gltf",
    ".gltf": "gltf",
    ".fbx": "fbx",
    ".usd": "usd",
    ".usdz": "usd",
    ".usda": "usd",
    ".usdc": "usd",
}


def find_blender() -> str:
    """Locate Blender binary via BLENDER_BIN, PATH, or standard macOS app bundle."""
    env_bin = os.environ.get("BLENDER_BIN")
    if env_bin and Path(env_bin).is_file():
        return env_bin
    on_path = shutil.which("blender")
    if on_path:
        return on_path
    if Path(DEFAULT_BLENDER).is_file():
        return DEFAULT_BLENDER
    raise FileNotFoundError(f"Blender binary not found on PATH or at {DEFAULT_BLENDER}")


def srgb_to_linear(c: float) -> float:
    """Convert single sRGB channel [0, 1] to linear light."""
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def parse_vec3(raw: str) -> tuple[float, float, float]:
    """Parse 'x,y,z' meter coordinates into a 3-float tuple."""
    parts = [float(p.strip()) for p in raw.split(",")]
    if len(parts) != 3:
        raise ValueError(f"Expected 'x,y,z' vector, got {raw!r}")
    return (parts[0], parts[1], parts[2])


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Import 3D export (.obj/.glb/.fbx/.usd/.blend) into macOS Blender and render.")
    ap.add_argument("input", nargs="?", type=Path, help="Input .obj/.glb/.gltf/.fbx/.usd/.usdz/.blend file")
    ap.add_argument("-o", "--output", type=Path, help="Render output PNG path")
    ap.add_argument("--save-blend", type=Path, help="Save configured Blender scene to .blend")
    ap.add_argument("--cameras", type=Path, help="Optional SketchUp cameras JSON (auto-detected for .obj)")
    ap.add_argument("--lights", type=Path, help="Optional SketchUp LT lights JSON (auto-detected for .obj)")
    ap.add_argument("--camera", default="auto", help="Camera name, 'auto' (first scene cam or birdseye), or 'birdseye'")
    ap.add_argument("--eye", help="Custom camera eye position in meters 'x,y,z'")
    ap.add_argument("--target", help="Custom camera target position in meters 'x,y,z'")
    ap.add_argument("--fov", type=float, default=38.0, help="Vertical FOV in degrees for custom camera (default: 38)")
    ap.add_argument("--engine", default="CYCLES", choices=("CYCLES", "BLENDER_EEVEE"))
    ap.add_argument("--samples", type=int, default=64, help="Render samples (default: 64)")
    ap.add_argument("--width", type=int, default=1600, help="Output width in pixels (default: 1600)")
    ap.add_argument("--height", type=int, help="Output height in pixels (default: derived from camera aspect or 16:9)")
    ap.add_argument("--sun-elevation", type=float, default=35.0, help="Physical sky sun elevation in degrees")
    ap.add_argument("--sun-rotation", type=float, default=35.0, help="Physical sky sun azimuth/rotation in degrees")
    ap.add_argument("--sky-strength", type=float, default=0.18, help="Sky world background strength (default: 0.18)")
    ap.add_argument("--exposure", type=float, default=0.0, help="Color management exposure")
    ap.add_argument("--no-sky", action="store_true", help="Skip adding physical sky (keep flat ambient or .blend world)")
    ap.add_argument("--info", action="store_true", help="Print scene summary JSON and exit without rendering")
    ap.add_argument("--self-test", action="store_true", help="Run built-in unit self-checks and exit")
    return ap.parse_args(argv)


def _self_test() -> None:
    assert abs(srgb_to_linear(0.0)) < 1e-9
    assert abs(srgb_to_linear(1.0) - 1.0) < 1e-6
    assert 0.21 < srgb_to_linear(0.5) < 0.22
    assert parse_vec3("1, -2.5, 3") == (1.0, -2.5, 3.0)
    ns = parse_args(["model.obj", "-o", "out.png", "--samples", "32", "--engine", "BLENDER_EEVEE", "--eye", "1,2,3", "--target", "4,5,6"])
    assert ns.input == Path("model.obj") and ns.output == Path("out.png") and ns.samples == 32
    assert ns.engine == "BLENDER_EEVEE" and parse_vec3(ns.eye) == (1.0, 2.0, 3.0)
    print("SELF_TEST_OK")


def _run_in_blender(args: argparse.Namespace, raw_argv: list[str], *, live=False, replace_scene=False) -> dict:
    import bpy
    from mathutils import Matrix, Vector

    src = args.input.resolve() if args.input else None
    if src is not None and not src.is_file():
        raise FileNotFoundError(f"Input file not found: {src}")
    if args.info and args.save_blend:
        raise ValueError("--info is read-only; run --save-blend separately")
    if src is not None and not live and not args.info and not args.output and not args.save_blend:
        raise ValueError("Specify at least one of --output, --save-blend, or --info")

    ext = src.suffix.lower() if src else ""
    is_blend = ext == ".blend"
    if live and src and args.info:
        # Inspect external files in their own process, without touching the artist's session.
        proc = subprocess.run(_blender_command(bpy.app.binary_path, [str(src), "--info"]),
                              capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError(f"Blender inspection failed: {proc.stderr[-1200:]}")
        for line in proc.stdout.splitlines():
            if line.startswith("BLENDER_OK: "):
                return json.loads(line.removeprefix("BLENDER_OK: "))
        raise RuntimeError("Blender inspection returned no scene summary")
    if is_blend:
        if live and not replace_scene:
            raise ValueError("Opening a .blend replaces the session; use replace_scene=True to open it")
        _require_finished(bpy.ops.wm.open_mainfile(filepath=str(src)), f"open {src}")
    elif src is not None:
        kind = IMPORT_HANDLERS.get(ext)
        if not kind:
            raise ValueError(f"Unsupported format {ext!r}; use .blend or {sorted(IMPORT_HANDLERS)}")
        if not live or replace_scene:
            bpy.ops.wm.read_factory_settings(use_empty=True)
        existing_materials = set(bpy.data.materials)
        if kind == "obj":
            status = bpy.ops.wm.obj_import(filepath=str(src))
        elif kind == "gltf":
            status = bpy.ops.import_scene.gltf(filepath=str(src))
        elif kind == "fbx":
            status = bpy.ops.import_scene.fbx(filepath=str(src))
        elif kind == "usd":
            status = bpy.ops.wm.usd_import(filepath=str(src))
        _require_finished(status, f"import {src}")

    sc = bpy.context.scene
    bounds = _scene_bounds(sc, Vector)
    if args.info:
        return _scene_summary(bpy, sc, src, args, bounds)
    if ext == ".obj":
        _tune_obj_materials(set(bpy.data.materials) - existing_materials)

    cams_path = args.cameras or (src.with_name(f"{src.stem}_cameras.json") if (src and ext == ".obj") else None)
    lights_path = args.lights or (src.with_name(f"{src.stem}_lights.json") if (src and ext == ".obj") else None)

    aspect = None
    if cams_path and cams_path.is_file():
        aspect = _load_cameras(bpy, sc, cams_path, Matrix, Vector)
    if lights_path and lights_path.is_file():
        _load_lights(bpy, sc, lights_path)

    # A plain Live import appends geometry without reconfiguring the existing camera or renderer.
    if live and src and not replace_scene and set(raw_argv) <= {"--save-blend", "--cameras", "--lights"}:
        if args.save_blend:
            _save_scene(bpy, args.save_blend)
        return _scene_summary(bpy, sc, src, args, bounds)

    bounds_min, bounds_max = bounds
    diag = (bounds_max - bounds_min).length if bounds_min is not None else 100.0
    _ensure_birdseye_camera(bpy, sc, bounds_min, bounds_max, Matrix, Vector)
    if args.eye and args.target:
        aspect = _set_custom_camera(bpy, sc, parse_vec3(args.eye), parse_vec3(args.target), args.fov, Matrix, Vector)
    elif args.eye or args.target:
        raise ValueError("Specify both --eye and --target together")
    else:
        aspect = _select_camera(bpy, sc, args.camera, aspect)
    _apply_camera_clipping(sc, diag)

    sky_flags = {"--sky-strength", "--sun-elevation", "--sun-rotation"}
    preserve_world = is_blend or (live and not replace_scene and sc.world is not None)
    if not args.no_sky and (not preserve_world or any(f in raw_argv for f in sky_flags)):
        _setup_sky_world(bpy, sc, args.sun_elevation, args.sun_rotation, args.sky_strength)
    elif not preserve_world and sc.world is None:
        w = bpy.data.worlds.new("World")
        if w.node_tree is None:
            w.use_nodes = True
        w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
        sc.world = w

    device_used = _configure_render(bpy, sc, args.engine, args.samples, args.width, args.height, aspect, args.exposure)

    if args.save_blend:
        _save_scene(bpy, args.save_blend)

    if args.output:
        png_out = args.output.resolve()
        png_out.parent.mkdir(parents=True, exist_ok=True)
        sc.render.image_settings.file_format = "PNG"
        sc.render.filepath = str(png_out)
        _require_finished(bpy.ops.render.render(write_still=True), f"render {png_out}")

    return _scene_summary(bpy, sc, src, args, bounds, device_used)


def _require_finished(status, operation):
    if "FINISHED" not in status:
        raise RuntimeError(f"Failed to {operation}: {status}")


def _save_scene(bpy, path):
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    _require_finished(bpy.ops.wm.save_as_mainfile(filepath=str(path)), f"save {path}")


def _scene_summary(bpy, sc, src, args, bounds, device=None):
    bounds_min, bounds_max = bounds
    cycles = sc.render.engine == "CYCLES"
    summary = {
        "input": str(src) if src else "(live scene)",
        "objects": len(sc.objects),
        "meshes": sum(1 for o in sc.objects if o.type == "MESH"),
        "materials": len(bpy.data.materials),
        "cameras": [o.name for o in sc.objects if o.type == "CAMERA"],
        "active_camera": sc.camera.name if sc.camera else None,
        "bounds_m": {
            "min": [round(v, 2) for v in bounds_min] if bounds_min else None,
            "max": [round(v, 2) for v in bounds_max] if bounds_max else None,
        },
        "engine": sc.render.engine,
        "device": device or (sc.cycles.device if cycles else None),
        "samples": sc.cycles.samples if cycles else None,
        "resolution": [sc.render.resolution_x, sc.render.resolution_y],
        "blend": str(args.save_blend.resolve()) if args.save_blend else None,
        "output": str(args.output.resolve()) if (not args.info and args.output) else None,
    }
    print("BLENDER_OK:", json.dumps(summary, ensure_ascii=False))
    return summary


def _tune_obj_materials(materials) -> None:
    """Fix SketchUp OBJ sRGB Kd colors, default 1.0 roughness, and architectural glass/water."""
    for m in materials:
        nt = getattr(m, "node_tree", None)
        if not nt:
            continue
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        bc = bsdf.inputs.get("Base Color")
        if bc and not bc.is_linked:
            r, g, b = bc.default_value[:3]
            bc.default_value = (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)
        alpha = bsdf.inputs["Alpha"].default_value if "Alpha" in bsdf.inputs else 1.0
        rough = bsdf.inputs.get("Roughness")
        if alpha < 0.99:
            if rough:
                rough.default_value = 0.06
            if "Thin Wall" in bsdf.inputs:
                bsdf.inputs["Thin Wall"].default_value = True
        elif rough and not rough.is_linked and abs(rough.default_value - 1.0) < 1e-4:
            rough.default_value = 0.72


def _look_at(obj, eye, target, up, Matrix, Vector) -> None:
    f = (target - eye).normalized()
    r = f.cross(up)
    if r.length < 1e-6:
        r = f.cross(Vector((0.0, 1.0, 0.0)))
    r.normalize()
    u = r.cross(f)
    obj.matrix_world = Matrix((
        (r.x, u.x, -f.x, eye.x),
        (r.y, u.y, -f.y, eye.y),
        (r.z, u.z, -f.z, eye.z),
        (0.0, 0.0, 0.0, 1.0),
    ))


def _load_cameras(bpy, sc, cams_path: Path, Matrix, Vector):
    cameras = json.loads(cams_path.read_text(encoding="utf-8"))
    first_aspect = None
    for c in cameras:
        name = c["name"]
        if name in bpy.data.objects:
            continue
        data = bpy.data.cameras.new(name)
        data.sensor_fit = "VERTICAL"
        if c.get("perspective", True) and c.get("fov"):
            data.angle_y = math.radians(c["fov"])
        else:
            data.type = "ORTHO"
            data.ortho_scale = (c.get("height_mm") or 10000.0) / 1000.0
        cam = bpy.data.objects.new(name, data)
        cam["_su_aspect"] = c.get("aspect") or 1.7778
        sc.collection.objects.link(cam)
        _look_at(
            cam,
            Vector(c["eye"]) / 1000.0,
            Vector(c["target"]) / 1000.0,
            Vector(c.get("up") or (0.0, 0.0, 1.0)),
            Matrix,
            Vector,
        )
        if first_aspect is None:
            first_aspect = cam["_su_aspect"]
    return first_aspect


def _load_lights(bpy, sc, lights_path: Path) -> None:
    lights = json.loads(lights_path.read_text(encoding="utf-8"))
    if not lights:
        return
    coll = bpy.data.collections.get("LT lights") or bpy.data.collections.new("LT lights")
    if coll.name not in sc.collection.children:
        sc.collection.children.link(coll)
    for i, lt in enumerate(lights):
        d = bpy.data.lights.new(f"{lt['tag']} {i + 1}", "AREA")
        d.shape = "RECTANGLE"
        d.size = max(lt["plan_size"][0] / 1000.0, 0.05)
        d.size_y = max(lt["plan_size"][1] / 1000.0, 0.05)
        d.energy = 20.0
        d.color = (1.0, 0.93, 0.84)
        ob = bpy.data.objects.new(d.name, d)
        ob.location = (lt["center"][0] / 1000.0, lt["center"][1] / 1000.0, lt["bottom"] / 1000.0 - 0.005)
        ob.rotation_euler = (0.0, 0.0, math.radians(lt.get("yaw", 0.0)))
        if hasattr(ob, "visible_camera"):
            ob.visible_camera = False
        coll.objects.link(ob)


def _scene_bounds(sc, Vector):
    xs, ys, zs = [], [], []
    for o in sc.objects:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            xs.append(p.x)
            ys.append(p.y)
            zs.append(p.z)
    if not xs:
        return None, None
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


def _ensure_birdseye_camera(bpy, sc, bmin, bmax, Matrix, Vector) -> None:
    if "Auto_Birdseye" in bpy.data.objects or bmin is None:
        return
    center = (bmin + bmax) * 0.5
    radius = max((bmax - bmin).length * 0.5, 1.0)
    data = bpy.data.cameras.new("Auto_Birdseye")
    data.sensor_fit = "VERTICAL"
    fov = math.radians(38.0)
    data.angle_y = fov
    cam = bpy.data.objects.new("Auto_Birdseye", data)
    cam["_su_aspect"] = 16.0 / 9.0
    sc.collection.objects.link(cam)
    direction = Vector((-1.0, -1.1, 0.72)).normalized()
    dist = radius / math.sin(fov * 0.5) * 0.65
    _look_at(cam, center + direction * dist, center, Vector((0.0, 0.0, 1.0)), Matrix, Vector)


def _set_custom_camera(bpy, sc, eye_xyz, target_xyz, fov_deg: float, Matrix, Vector) -> float:
    cam = bpy.data.objects.get("Custom_Camera")
    if cam is None or cam.type != "CAMERA":
        data = bpy.data.cameras.new("Custom_Camera")
        cam = bpy.data.objects.new("Custom_Camera", data)
        sc.collection.objects.link(cam)
    cam.data.type = "PERSP"
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle_y = math.radians(fov_deg)
    _look_at(cam, Vector(eye_xyz), Vector(target_xyz), Vector((0.0, 0.0, 1.0)), Matrix, Vector)
    sc.camera = cam
    return 16.0 / 9.0


def _select_camera(bpy, sc, requested: str, fallback_aspect):
    cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
    if not cams:
        return fallback_aspect
    target = None
    req = requested.strip().lower()
    if req == "birdseye":
        target = bpy.data.objects.get("Auto_Birdseye")
    elif req == "auto":
        non_auto = [c for c in cams if c.name != "Auto_Birdseye"]
        target = sc.camera if (sc.camera and sc.camera.name != "Auto_Birdseye") else (non_auto[0] if non_auto else cams[0])
    else:
        target = next((c for c in cams if c.name.lower() == req), None)
        if target is None:
            raise ValueError(f"Camera {requested!r} not found; available: {[c.name for c in cams]}")
    sc.camera = target
    return target.get("_su_aspect", fallback_aspect)


def _apply_camera_clipping(sc, diag: float) -> None:
    if sc.camera and sc.camera.data:
        sc.camera.data.clip_start = max(0.05, min(0.5, diag * 0.0005))
        sc.camera.data.clip_end = max(1000.0, diag * 10.0)


def _setup_sky_world(bpy, sc, elev_deg: float, rot_deg: float, strength: float) -> None:
    w = sc.world or bpy.data.worlds.new("SkyWorld")
    if w.node_tree is None:
        w.use_nodes = True
    sc.world = w
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg_sky = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    for st in ("SINGLE_SCATTERING", "MULTIPLE_SCATTERING", "NISHITA"):
        try:
            sky.sky_type = st
            break
        except TypeError:
            continue
    sky.sun_disc = True
    sky.sun_elevation = math.radians(elev_deg)
    sky.sun_rotation = math.radians(rot_deg)
    bg_sky.inputs["Strength"].default_value = strength
    nt.links.new(sky.outputs["Color"], bg_sky.inputs["Color"])

    # Physical sky returns black below the horizon; fill downward rays for clean bird's-eye views.
    bg_gnd = nt.nodes.new("ShaderNodeBackground")
    bg_gnd.inputs["Color"].default_value = (0.55, 0.56, 0.58, 1.0)
    bg_gnd.inputs["Strength"].default_value = max(0.15, min(0.8, strength * 3.0))
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    cmp = nt.nodes.new("ShaderNodeMath")
    cmp.operation = "LESS_THAN"
    cmp.inputs[1].default_value = 0.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geom.outputs["Incoming"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], cmp.inputs[0])
    nt.links.new(cmp.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(bg_gnd.outputs["Background"], mix.inputs[1])
    nt.links.new(bg_sky.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])


def _configure_render(bpy, sc, engine: str, samples: int, width: int, height: int | None, aspect, exposure: float) -> str:
    sc.render.engine = engine
    device_used = "CPU"
    if engine == "CYCLES":
        sc.cycles.samples = samples
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = 0.02 if samples >= 64 else 0.05
        sc.cycles.use_denoising = True
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "METAL"
            prefs.refresh_devices()
            metal_devs = [d for d in prefs.devices if d.type == "METAL"]
            for d in prefs.devices:
                d.use = d.type == "METAL"
            if metal_devs:
                sc.cycles.device = "GPU"
                device_used = f"METAL:{metal_devs[0].name}"
        except Exception:
            sc.cycles.device = "CPU"
    elif engine == "BLENDER_EEVEE" and hasattr(sc.eevee, "use_raytracing"):
        sc.eevee.use_raytracing = True
    for vt in ("AgX", "Filmic"):
        try:
            sc.view_settings.view_transform = vt
            break
        except TypeError:
            continue
    sc.view_settings.exposure = exposure
    sc.render.resolution_x = width
    sc.render.resolution_y = height if height else (int(round(width / aspect)) if aspect else int(round(width * 9 / 16)))
    return device_used


def run(input_path: str | Path | None = None, *, replace_scene=False, **kwargs) -> dict:
    """In-Blender entry point (for live blender-mcp execute_blender_code calls)."""
    ns = parse_args([])
    ns.input = Path(input_path) if input_path else None
    for path_key in ("output", "save_blend", "cameras", "lights"):
        if kwargs.get(path_key) is not None:
            kwargs[path_key] = Path(kwargs[path_key])
    raw_argv = []
    for k, v in kwargs.items():
        if not hasattr(ns, k):
            raise ValueError(f"Unknown option {k!r}")
        setattr(ns, k, v)
        raw_argv.append(f"--{k.replace('_', '-')}")
    return _run_in_blender(ns, raw_argv, live=True, replace_scene=replace_scene)


def _blender_command(binary, argv):
    return [binary, "-b", "--python-exit-code", "1", "--python", str(Path(__file__).resolve()), "--", *argv]


def main() -> None:
    if "bpy" not in sys.modules:
        args = parse_args(sys.argv[1:])
        if args.self_test:
            _self_test()
            return
        if args.input is None:
            raise SystemExit("error: input file is required when running from CLI")
        blender = find_blender()
        proc = subprocess.run(_blender_command(blender, sys.argv[1:]))
        sys.exit(proc.returncode)
    else:
        argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
        args = parse_args(argv)
        if args.self_test:
            _self_test()
            return
        _run_in_blender(args, argv)


if __name__ == "__main__":
    main()
