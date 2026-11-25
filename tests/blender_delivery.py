"""Run inside a fresh background Blender with --factory-startup --python-exit-code 1."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy

if not bpy.app.background:
    raise RuntimeError("Run this test in a separate background Blender instance")

scripts = Path(__file__).resolve().parents[1] / "skills/cad-creator-mac/scripts"
sys.path.insert(0, str(scripts))
import blender_render as renderer

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    obj = root / "triangle.obj"
    obj.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
    original = bpy.context.scene
    bpy.data.objects["Cube"].name = "Unsaved mesh"
    original.render.resolution_x = 1234
    camera = original.camera
    before = set(original.objects)
    local_info = renderer.run(info=True)
    assert local_info["resolution"][0] == 1234
    assert renderer.run(obj, info=True)["meshes"] == 1
    assert set(original.objects) == before and original.camera == camera

    blend = root / "scene.blend"
    renderer.run(obj, save_blend=blend)
    assert blend.is_file() and len(original.objects) == len(before) + 1
    assert before <= set(original.objects) and original.render.resolution_x == 1234
    try:
        renderer.run(blend)
    except ValueError as error:
        assert "replace_scene" in str(error)
    else:
        raise AssertionError("Live .blend replacement requires an explicit request")

    renderer.run(obj, replace_scene=True, save_blend=root / "replacement.blend")
    assert "Unsaved mesh" not in bpy.data.objects
    assert renderer.run(blend, info=True)["resolution"][0] == 1234
    assert "Unsaved mesh" not in bpy.data.objects

    cli = [sys.executable, str(scripts / "blender_render.py")]
    env = dict(os.environ, BLENDER_BIN=bpy.app.binary_path)
    missing = subprocess.run([*cli, str(root / "missing.obj"), "--info"], env=env,
                             capture_output=True, text=True)
    assert missing.returncode and "FileNotFoundError" in missing.stderr + missing.stdout
    png = root / "proof.png"
    subprocess.run([*cli, str(obj), "--no-sky", "--samples", "1", "--width", "64",
                    "--height", "48", "-o", str(png)], env=env, check=True)
    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
print("Blender delivery checks passed")
