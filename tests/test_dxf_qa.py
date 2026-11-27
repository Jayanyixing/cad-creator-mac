"""CLI regression tests using synthetic drawings; no AutoCAD required."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import ezdxf
except ImportError:
    ezdxf = None

CLI = Path(__file__).resolve().parents[1] / "skills/cad-creator-mac/scripts/dxf_qa.py"


@unittest.skipIf(ezdxf is None, "DXF QA tests require ezdxf")
class DxfQaTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.before = self.root / "样图.dxf"
        self.after = self.root / "改后.dxf"
        self.doc = ezdxf.new("R2013")
        self.doc.units = 4
        self.doc.layers.new("墙线")
        msp = self.doc.modelspace()
        self.wall = msp.add_line((0, 0), (3000, 0), dxfattribs={"layer": "墙线"}).dxf.handle
        self.other = msp.add_line((0, 200), (500, 200)).dxf.handle
        self.dim = msp.add_linear_dim(base=(0, 100), p1=(0, 0), p2=(3000, 0), text="3000").dimension.dxf.handle
        self.outline = msp.add_lwpolyline([(0, 0), (20, 0), (20, 20)], close=True).dxf.handle
        self.block_line = self.doc.blocks.new("窗块").add_line((0, 0), (20, 0)).dxf.handle
        self.doc.saveas(self.before)
        self.rules = {"units": 4, "checks": [
            {"kind": "count", "type": "LINE", "layer": "墙线", "expected": 1},
            {"kind": "length", "handle": self.wall, "expected": 3000, "tolerance": 0.1},
            {"kind": "closed", "handle": self.outline, "expected": True},
            {"kind": "dimension", "handle": self.dim, "expected": 3000, "tolerance": 0.1},
        ]}

    def cli(self, status, *args):
        p = subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(p.returncode, {"passed": 0, "failed": 1, "pending": 2}[status], p.stdout + p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(result["status"], status)
        return result

    def test_rule_pass_and_inputs_unchanged(self):
        content = self.before.read_bytes()
        report = self.cli("passed", "check", self.before, "--rules", self.rules_file())
        self.assertEqual(report["inputs"]["drawing_sha256"], hashlib.sha256(content).hexdigest())
        self.assertEqual(self.before.read_bytes(), content)

    def rules_file(self):
        p = self.root / "rules.json"
        p.write_text(json.dumps(self.rules, ensure_ascii=False), encoding="utf-8")
        return p

    def test_dimension_override_catches_wrong_display(self):
        self.doc.entitydb[self.dim].dxf.text = "2980"
        self.doc.saveas(self.after)
        result = self.cli("failed", "check", self.after, "--rules", self.rules_file())
        self.assertFalse(result["findings"][-1]["manual_text_consistent"])

    def test_unsupported_dimension_format_is_pending(self):
        self.doc.entitydb[self.dim].dxf.text = "约 <> mm"
        self.doc.saveas(self.after)
        self.cli("pending", "check", self.after, "--rules", self.rules_file())

    def test_wrong_units_and_geometry(self):
        self.doc.units = 6
        self.doc.entitydb[self.wall].dxf.end = (2980, 0)
        self.doc.saveas(self.after)
        f = self.cli("failed", "check", self.after, "--rules", self.rules_file())["findings"]
        self.assertEqual([x["check"] for x in f if x["status"] == "failed"], ["INSUNITS", "length"])

    def test_invalid_rules_not_reported_as_pass(self):
        self.rules["checks"] = []
        self.cli("pending", "check", self.before, "--rules", self.rules_file())

    def diff(self, status, *allowed):
        p = self.root / "policy.json"
        p.write_text(json.dumps({"allow": [
            {"handle": h, "operation": op} for h, op in allowed
        ]}), encoding="utf-8")
        return self.cli(status, "diff", self.before, self.after, "--policy", p)

    def test_diff_accepts_only_intended_change(self):
        after = ezdxf.readfile(self.before)
        after.entitydb[self.wall].dxf.end = (3050, 0)
        after.saveas(self.after)
        result = self.diff("passed", (self.wall, "modified"))
        self.assertEqual([x["handle"] for x in result["findings"]], [self.wall])

    def test_diff_flags_add_remove_and_block_change(self):
        after = ezdxf.readfile(self.before)
        after.modelspace().delete_entity(after.entitydb[self.other])
        new = after.modelspace().add_line((0, 100), (100, 100)).dxf.handle
        after.entitydb[self.block_line].dxf.end = (35, 0)
        after.saveas(self.after)
        result = self.diff("failed", (new, "added"))
        unexpected = {(x["handle"], x["operation"]) for x in result["findings"] if x["status"] == "failed"}
        self.assertEqual(unexpected, {(self.other, "removed"), (self.block_line, "modified")})

    def test_unrelated_export_is_pending(self):
        ezdxf.new("R2013").saveas(self.after)
        self.assertEqual(self.diff("pending")["findings"][0]["check"], "lineage")


if __name__ == "__main__":
    unittest.main()
