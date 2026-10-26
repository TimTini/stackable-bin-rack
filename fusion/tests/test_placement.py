import ast
from pathlib import Path
import unittest


SOURCE=Path(__file__).resolve().parents[1]/'StackableBinRack'/'StackableBinRack.py'


class PlacementTests(unittest.TestCase):
    def plan(self, mode):
        tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='placement_plan')
        namespace={}
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE),'exec'),namespace)
        return namespace['placement_plan'](mode)

    def test_assembly_offsets_follow_actual_dimensions(self):
        plan=self.plan('assembly')
        self.assertEqual(plan['cap']['translation'],('0 mm','span','post_top + plate_t'))
        self.assertEqual(plan['bin']['translation'],('plate_w - side_rail_w','(span + bin_W) / 2','plate_t'))
        self.assertEqual(plan['cap']['rotation'],(180,(1,0,0)))
        self.assertEqual(plan['bin']['rotation'],(120,(1,-1,-1)))

    def test_layout_offsets_follow_growth(self):
        plan=self.plan('layout')
        self.assertEqual(plan['frame']['translation'][0],'plate_w + 5 mm')
        self.assertEqual(plan['bin']['translation'][1],'span + 31.465 mm')
        self.assertTrue(all(item['rotation'] is None for item in plan.values()))

    def test_mode_contract_rejects_unknown_pose(self):
        with self.assertRaises(ValueError): self.plan('other')


if __name__=='__main__': unittest.main()
