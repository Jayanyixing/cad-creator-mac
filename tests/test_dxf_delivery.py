"""Conversion failure paths, without an AutoCAD installation."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/cad-creator-mac/scripts"))
import dxf_to_dwg as converter

READBACK = """__CAD_INSUNITS=4
__CAD_TOTAL=1
__CAD_MODEL=1
__CAD_LAYOUT=Model
__CAD_LAYOUT=图纸一
__CAD_LAYOUT_COUNT=2
"""


class DeliveryTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.src = self.folder / "project.dxf"
        self.dst = self.folder / "project.dwg"
        self.src.write_bytes(b"DXF source")
        self.dst.write_bytes(b"previous delivery")

    def convert(self, output_readback):
        def console(binary, drawing, script, folder, readonly, timeout):
            if readonly:
                return output_readback
            (folder / "out.dwg").write_bytes(b"AC1032test output")
            return READBACK

        with patch.object(converter, "find_accoreconsole", return_value="stub"), \
             patch.object(converter, "run_console", side_effect=console):
            return converter.dxf_to_dwg(self.src, self.dst)

    def test_invalid_destinations(self):
        hardlink = self.folder / "alias.dwg"
        os.link(self.src, hardlink)
        symlink = self.folder / "link.dwg"
        symlink.symlink_to(self.src)
        directory = self.folder / "dir.dwg"
        directory.mkdir()
        with patch.object(converter, "find_accoreconsole") as lookup:
            for dst in (self.src, hardlink, symlink, directory, self.folder / "bad.pdf"):
                with self.subTest(dst=dst), self.assertRaises((ValueError, IsADirectoryError)):
                    converter.dxf_to_dwg(self.src, dst)
            lookup.assert_not_called()
        self.assertEqual(self.src.read_bytes(), b"DXF source")

    def test_output_must_match_source(self):
        for result in ("", READBACK.replace("__CAD_LAYOUT=图纸一\n", ""),
                       READBACK.replace("INSUNITS=4", "INSUNITS=1"),
                       READBACK.replace("图纸一", "Other")):
            with self.subTest(result=result), self.assertRaises(RuntimeError):
                self.convert(result)
            self.assertEqual(self.dst.read_bytes(), b"previous delivery")
        self.assertEqual(self.convert(READBACK)["layouts"], ["Model", "图纸一"])
        self.assertEqual(self.dst.read_bytes(), b"AC1032test output")

    def test_interrupted_staging_preserves_last_delivery(self):
        def interrupted_copy(src, dst):
            Path(dst).write_bytes(b"partial")
            raise OSError("destination volume full")

        with patch.object(converter.shutil, "move", side_effect=interrupted_copy):
            with self.assertRaises(OSError):
                self.convert(READBACK)
        self.assertEqual(self.dst.read_bytes(), b"previous delivery")
        self.assertEqual(set(self.folder.iterdir()), {self.src, self.dst})


if __name__ == "__main__":
    unittest.main()
