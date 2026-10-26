"""Equal baseline coordinates with different expressions retain independent motion."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


class CoordinateDependencyTests(unittest.TestCase):
    def test_equal_values_with_distinct_expressions_are_independent(self):
        path=Path(__file__).resolve().parents[1]/'StackableBinRack/StackableBinRack.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Sk')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_align')
        namespace={}; exec(compile(ast.Module(body=[method],type_ignores=[]),str(path),'exec'),namespace)
        dimensions=[]; links=[]
        self_sk=SimpleNamespace(axis_pts={},sk=SimpleNamespace(geometricConstraints=SimpleNamespace(
            addVerticalPoints=lambda a,b:links.append((a,b)),addHorizontalPoints=lambda a,b:links.append((a,b)))),
            _dim=lambda *args:dimensions.append(args))
        align=namespace['_align']
        align(self_sk,'first','span - 2 mm',118,True)
        align(self_sk,'second','plate_w - 6 mm',118,True)
        align(self_sk,'same-dependency','span - 2 mm',118,True)
        self.assertEqual(len(dimensions),2)
        self.assertEqual(links,[('first','same-dependency')])


if __name__=='__main__': unittest.main()
