import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "StackableBinRack" / "StackableBinRack.py"


class NativeFrameLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text, filename=str(SOURCE))
        sk_class = next(
            node for node in cls.tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Sk"
        )
        cls.sk_loop = next(node for node in sk_class.body
                           if isinstance(node, ast.FunctionDef) and node.name == "loop")
        cls.loop_text = ast.get_source_segment(cls.text, cls.sk_loop)

    def test_loop_keeps_expression_vertices_as_construction_support(self):
        self.assertIn("support_pts = []", self.loop_text)
        self.assertIn("line.isConstruction = True", self.loop_text)
        self.assertIn("profile_pts = [sk.sketchPoints.add", self.loop_text)

    def test_fillet_is_applied_to_free_profile_lines_and_reanchored(self):
        self.assertIn(
            "prev, prev.endSketchPoint.geometry,\n                nxt, nxt.startSketchPoint.geometry",
            self.loop_text,
        )
        self.assertIn("gc.addCoincident(line.startSketchPoint, support[i])", self.loop_text)
        self.assertIn("gc.addCoincident(line.endSketchPoint, support[i])", self.loop_text)
        self.assertIn("def tangent_exists(one, two):", self.loop_text)
        self.assertIn('constraint.objectType != "adsk::fusion::TangentConstraint"', self.loop_text)
        self.assertIn("constraint.curveOne, constraint.curveTwo", self.loop_text)
        self.assertIn("gc.addTangent(one, two)", self.loop_text)
        self.assertNotIn("addFillet(prev, v, nxt, v", self.loop_text)
        self.assertNotIn("except RuntimeError", self.loop_text)

    def test_radial_dimension_is_reused_or_fails_explicitly(self):
        self.assertIn('dim.objectType == "adsk::fusion::SketchRadialDimension"', self.loop_text)
        self.assertIn("dim.entity == arc", self.loop_text)
        self.assertIn('raise RuntimeError(f"loop: radial dimension missing for fillet {i}")', self.loop_text)


if __name__ == "__main__":
    unittest.main()
