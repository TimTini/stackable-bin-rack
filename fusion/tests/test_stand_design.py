"""Stand construction is independent of the full 3D frame, per design contract."""
from pathlib import Path
import re
import unittest


class StandDesignTests(unittest.TestCase):
    def test_stands_do_not_reach_complete_frame_geometry(self):
        source=(Path(__file__).resolve().parents[2]/'stackable-bin-rack.scad').read_text(encoding='utf-8')
        source=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/','',source)
        modules={}
        for match in re.finditer(r'\bmodule\s+(\w+)\s*\([^)]*\)\s*\{',source):
            start=match.end(); depth=1; end=start
            while depth:
                if source[end]=='{': depth+=1
                elif source[end]=='}': depth-=1
                end+=1
            modules[match.group(1)]=set(re.findall(r'\b(\w+)\s*\(',source[start:end-1]))
        for name in ('stand','stand_bin'):
            reached=set(); pending=[name]
            while pending:
                call=pending.pop()
                if call in reached: continue
                reached.add(call)
                pending.extend(modules.get(call,set())-reached)
            with self.subTest(part=name):
                self.assertFalse(reached&{'frame','frame_body','frame_half'},reached)


if __name__=='__main__': unittest.main()
