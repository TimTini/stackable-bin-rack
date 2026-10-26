"""The public size multiplier belongs to the bin, not the dovetail pitch."""
import sys
import ast
import operator
import re
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'StackableBinRack'))
import Contract


class BinMultiplierTests(unittest.TestCase):
    def test_native_parameter_expressions_match_public_dimensions(self):
        path=Path(__file__).resolve().parents[1]/'StackableBinRack/StackableBinRack.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        assignment=next(n for n in tree.body if isinstance(n,ast.Assign)
                        and any(isinstance(t,ast.Name) and t.id=='PARAMS' for t in n.targets))
        expressions={name:value for name,value,unit,comment in ast.literal_eval(assignment.value)}
        operations={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
        for length,depth,height in ((1,1,1),(2,1,1),(1,2,1),(1,1,2),(2,2,2),(3,1,1),(1,3,2)):
            overrides={'len_n':length,'wid_n':depth,'hgt_n':height}
            def number(node):
                if isinstance(node,ast.Constant): return float(node.value)
                if isinstance(node,ast.Name):
                    if node.id in overrides: return overrides[node.id]
                    return number(ast.parse(re.sub(r'\bmm\b','',expressions[node.id]),mode='eval').body)
                if isinstance(node,ast.BinOp): return operations[type(node.op)](number(node.left),number(node.right))
                if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub): return -number(node.operand)
                raise ValueError(ast.dump(node))
            expected={'bin_W':100*length,'bin_D':80*height,'bin_H':100*depth+35,
                      'span':100*length+20,'plate_w':100*depth+24,'post_top':80*height+11}
            for name,value in expected.items():
                with self.subTest(size=(length,depth,height),parameter=name):
                    self.assertAlmostEqual(number(ast.parse(expressions[name].replace(' mm',''),mode='eval').body),value)

    def test_length_is_a_multiple_of_original_bin(self):
        self.assertEqual(Contract.bin_size(1),(100.0,80.0,135.0))
        self.assertEqual(Contract.bin_size(2),(200.0,80.0,135.0))
        self.assertEqual(Contract.bin_size(3),(300.0,80.0,135.0))

    def test_frame_retains_bin_end_clearance(self):
        for length in (1,2,3):
            self.assertAlmostEqual(Contract.span(length)-Contract.bin_size(length)[0],20.0)

    def test_depth_extends_the_body_and_retains_35mm_nose(self):
        for depth in (1,2,3):
            self.assertEqual(Contract.bin_size(1,depth,1),(100.0,80.0,100.0*depth+35.0))
            self.assertAlmostEqual(Contract.plate_w(depth)-Contract.bin_size(1,depth,1)[2],-11.0)

    def test_height_is_a_multiple_of_80mm(self):
        for height in (1,2,3):
            self.assertEqual(Contract.bin_size(1,1,height),(100.0,80.0*height,135.0))
            self.assertAlmostEqual(Contract.post_top(height)-Contract.bin_size(1,1,height)[1],11.0)

    def test_mixed_columns_keep_their_same_partition_on_each_tier(self):
        items=Contract.asm_items([[1,2],[1,2]])
        self.assertEqual([(kind,n,round(xyz[1],2)) for kind,n,xyz in items[:4]],
                         [('frame',1,219.93),('bin',1,219.93),('frame',2,0.0),('bin',2,0.0)])
        with self.assertRaises(ValueError):
            Contract.asm_items([[2],[1,1]])
        with self.assertRaises(ValueError):
            Contract.asm_items([[1,2],[2,1]])


if __name__=='__main__':
    unittest.main()
