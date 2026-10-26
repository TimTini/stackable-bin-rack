import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "StackableBinRack"))
import Contract


class ContractTests(unittest.TestCase):
    def test_source_defaults_to_one_assembled_unit(self):
        source = (Path(__file__).resolve().parents[2] / "stackable-bin-rack.scad").read_text(encoding="utf-8")
        self.assertIn('part = "assembly"', source)
        self.assertIn("asm_spec = [[size[0]]];", source)

    def test_one_cell_matches_scad_bounds(self):
        self.assertAlmostEqual(Contract.span(1), 120.0)
        self.assertAlmostEqual(Contract.pitch_y(), 119.93)
        self.assertEqual(Contract.bin_size(1), (100.0, 80.0, 135.0))
        self.assertEqual(Contract.expected_size("cap"), (124.0, 119.93, 8.0))
        self.assertAlmostEqual(Contract.expected_size("frame")[1], 124.93)
        self.assertEqual(Contract.expected_size("bin"), (100.0, 80.0, 135.0))

    def test_two_cell_frame_follows_doubled_bin(self):
        self.assertAlmostEqual(Contract.span(2), 220.0)
        self.assertAlmostEqual(Contract.bin_size(2)[0], 200.0)
        self.assertAlmostEqual(Contract.expected_size("cap", 2)[1], 219.93)

    def test_double_frames_register_on_successive_tiers(self):
        items = Contract.asm_items([[2], [2]])
        kinds = [(k, n, round(p[1], 2), p[2]) for k, n, p in items]
        self.assertEqual(kinds, [
            ("frame", 2, 0.0, 0.0),
            ("bin", 2, 0.0, 0.0),
            ("frame", 2, 0.0, 91.0),
            ("bin", 2, 0.0, 91.0),
            ("cap", 2, 0.0, 182.0),
        ])

    def test_assembly_rows_follow_global_stack_height(self):
        items = Contract.asm_items([[1, 2], [1, 2]], wid_n=2, hgt_n=2)
        self.assertEqual(
            [(k, n, round(p[1], 2), p[2]) for k, n, p in items],
            [
                ("frame", 1, 219.93, 0.0),
                ("bin", 1, 219.93, 0.0),
                ("frame", 2, 0.0, 0.0),
                ("bin", 2, 0.0, 0.0),
                ("frame", 1, 219.93, 171.0),
                ("bin", 1, 219.93, 171.0),
                ("frame", 2, 0.0, 171.0),
                ("bin", 2, 0.0, 171.0),
                ("cap", 1, 219.93, 342.0),
                ("cap", 2, 0.0, 342.0),
            ],
        )

    def test_bin_pose_maps_print_origin_to_rail(self):
        rot, t = Contract.part_pose("bin", 1)
        self.assertEqual(rot, ((0, -1, 0), (0, 0, 1), (-1, 0, 0)))
        self.assertAlmostEqual(t[0], 116.0)
        self.assertAlmostEqual(t[1], 110.0)
        self.assertAlmostEqual(t[2], 8.0)

    def test_assembly_pose_preserves_column_rotation_and_bounds(self):
        cap_rot, cap_t = Contract.assembly_pose("cap", 2, wid_n=2, hgt_n=2)
        self.assertEqual(cap_rot, ((1, 0, 0), (0, -1, 0), (0, 0, -1)))
        self.assertEqual(cap_t, (0.0, 220.0, 179.0))

        rot, t = Contract.assembly_pose("bin", 2, wid_n=2, hgt_n=2)
        self.assertEqual(rot, ((0, -1, 0), (0, 0, 1), (-1, 0, 0)))
        self.assertEqual(tuple(round(v, 2) for v in t), (216.0, 210.0, 8.0))

        size = Contract.bin_size(2, wid_n=2, hgt_n=2)

        def world_point(local):
            return tuple(
                t[i] + sum(rot[j][i] * local[j] for j in range(3))
                for i in range(3)
            )

        corners = [
            world_point((x, y, z))
            for x in (0.0, size[0])
            for y in (0.0, size[1])
            for z in (0.0, size[2])
        ]
        bounds = tuple(
            (round(min(p[i] for p in corners), 2), round(max(p[i] for p in corners), 2))
            for i in range(3)
        )
        self.assertEqual(bounds, ((-19.0, 216.0), (10.0, 210.0), (8.0, 168.0)))
        self.assertEqual(Contract.expected_size("frame", 2, 2, 2), (224.0, 224.93, 176.0))
        self.assertEqual(Contract.expected_size("bin", 2, 2, 2), (200.0, 160.0, 235.0))

    def test_rejects_mismatched_rows_and_clearance(self):
        with self.assertRaises(ValueError):
            Contract.asm_items([[2], [1]])
        with self.assertRaises(ValueError):
            Contract.validate(1, 1, 1, socket_r=1.9, tip_r=2.0)
        with self.assertRaises(ValueError):
            Contract.validate(0, 1, 1)


if __name__ == "__main__":
    unittest.main()
