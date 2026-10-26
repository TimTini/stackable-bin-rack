import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "StackableBinRack" / "StackableBinRack.py"


class NativePanelStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text, filename=str(SOURCE))
        start = cls.text.index('stage("bin: panels")')
        end = cls.text.index('return body', start)
        cls.panel_block = cls.text[start:end]

    def test_floor_and_back_use_deterministic_cut_lofts(self):
        self.assertIn('floor_inset = "2.5 * panel_depth"', self.panel_block)
        self.assertIn('fl = oplane(comp, xy, "bin_floor", "z", "bin floor surface")', self.panel_block)
        self.assertIn('bin_floor - panel_depth', self.panel_block)
        self.assertIn('back_surface = xz', self.panel_block)
        self.assertIn('panel_depth", "y", "back panel inset"', self.panel_block)
        self.assertNotIn('bin_floor + 1 mm', self.panel_block)
        self.assertNotIn('"-1 mm", "y", "back panel outer"', self.panel_block)
        self.assertEqual(self.panel_block.count("cut_panel_loft("), 2)
        self.assertNotIn("def panel_cut", self.panel_block)

    def test_side_panel_fallback_is_explicitly_separate(self):
        self.assertIn("def side_panel_cut", self.panel_block)
        self.assertIn("side_panel_cut(sk, wdir, 1.0, name)", self.panel_block)
        self.assertIn("separate follow-up", self.panel_block)

    def test_cut_panel_loft_is_native_cut_with_expression_sections(self):
        helper = next(node for node in self.tree.body if isinstance(node, ast.FunctionDef) and node.name == "cut_panel_loft")
        helper_text = ast.get_source_segment(self.text, helper)
        self.assertIn("comp.features.loftFeatures.createInput", helper_text)
        self.assertIn("CutFeatureOperation", helper_text)
        self.assertIn("inp.loftSections.add(profile)", helper_text)
        self.assertIn("inp.participantBodies = [body]", helper_text)
        self.assertIn("sketch.sk.isVisible = False", helper_text)

    def test_locator_loft_wrapper_hides_native_sketch(self):
        helper = next(node for node in self.tree.body if isinstance(node, ast.FunctionDef) and node.name == "loft_hull")
        helper_text = ast.get_source_segment(self.text, helper)
        self.assertIn("sketch.sk.isVisible = False", helper_text)
        self.assertNotIn("sketch.isVisible = False", helper_text)


if __name__ == "__main__":
    unittest.main()
