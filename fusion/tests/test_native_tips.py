import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "StackableBinRack" / "StackableBinRack.py"


class NativeTipStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text, filename=str(SOURCE))

    def test_frame_tips_use_expression_lofts_instead_of_edge_chamfers(self):
        start = self.text.index('stage("frame: tips")')
        end = self.text.index('stage("frame: notch")', start)
        block = self.text[start:end]
        self.assertNotIn("loop_seeds", block)
        self.assertNotIn('"tip tops"', block)
        self.assertNotIn('"tip bases"', block)
        self.assertIn('"tip_h - tip_chamfer"', block)
        self.assertIn('"tip_r + tip_flare"', block)
        self.assertIn('"tip_r - tip_chamfer"', block)
        self.assertEqual(block.count("loft_hull("), 2)

    def test_loft_helper_is_native_solid_join_with_two_sections(self):
        helper = next(node for node in self.tree.body if isinstance(node, ast.FunctionDef) and node.name == "loft_hull")
        helper_text = ast.get_source_segment(self.text, helper)
        self.assertIsNotNone(helper_text)
        self.assertIn("comp.features.loftFeatures.createInput", helper_text)
        self.assertIn("JoinFeatureOperation", helper_text)
        self.assertIn("inp.loftSections.add(profile)", helper_text)
        self.assertIn("inp.isSolid = True", helper_text)

    def test_tip_lofts_are_per_locator_sketch_profiles_on_offset_planes(self):
        helper = next(node for node in self.tree.body if isinstance(node, ast.FunctionDef) and node.name == "loft_hull")
        helper_text = ast.get_source_segment(self.text, helper)
        self.assertIn('oplane(comp, base, z_expr, "z"', helper_text)
        self.assertIn('Sk(comp, plane, "xy"', helper_text)
        self.assertIn("sketch.hull(loc, radius_expr)", helper_text)


if __name__ == "__main__":
    unittest.main()
