import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "StackableBinRack" / "StackableBinRack.py"


class NativeSocketFlareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text, filename=str(SOURCE))
        helper = next(node for node in cls.tree.body
                      if isinstance(node, ast.FunctionDef)
                      and node.name == "cut_socket_flare")
        cls.helper = ast.get_source_segment(cls.text, helper)
        cls.cap = cls.text[cls.text.index('stage("cap: sockets")'):cls.text.index('return body', cls.text.index('stage("cap: sockets")'))]
        frame_start = cls.text.index('stage("frame: sockets")')
        cls.frame = cls.text[frame_start:cls.text.index('stage("frame: tips")', frame_start)]

    def test_helper_uses_four_aggregate_native_profiles_and_unique_pairing(self):
        self.assertIn('outer_sk = Sk(comp, outer_plane, "xy", name)', self.helper)
        self.assertIn('throat_sk = Sk(comp, throat_plane, "xy", f"{name} throat")', self.helper)
        self.assertIn('outer_sk.hull(loc, "socket_r + socket_chamfer")', self.helper)
        self.assertIn('throat_sk.hull(loc, "socket_r")', self.helper)
        self.assertIn('outer_profiles.count != 4 or throat_profiles.count != 4', self.helper)
        self.assertIn('profile.boundingBox', self.helper)
        self.assertIn('used_outer, used_throat, matched = set(), set(), []', self.helper)
        self.assertIn('inp.participantBodies = [body]', self.helper)
        self.assertIn('CutFeatureOperation', self.helper)

    def test_cap_and_frame_use_surface_to_throat_planes(self):
        self.assertIn('cut_socket_flare(comp, body, xy, "plate_t", "plate_t - socket_chamfer", "cap socket flare")', self.cap)
        self.assertIn('cut_socket_flare(comp, body, xy, "0 mm", "socket_chamfer", "frame socket flare")', self.frame)
        self.assertNotIn('extrude(comp, sk, sk.profiles(), "socket_chamfer"', self.cap + self.frame)


if __name__ == "__main__":
    unittest.main()
