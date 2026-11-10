"""Independent consistency checks on the release (no imagery, outcomes or cloud access)."""
import json,unittest
from pathlib import Path
import numpy as np,pandas as pd
from summarize import read,O
class Release(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=read(O/'coverage.csv')
    def test_frozen_denominators(self):
        r=read('manifests/g6g/reserve8_roster.csv').query('split!="excluded"')
        p=self.c.merge(r,on=['geoid','split','block','cell'],validate='one_to_one')
        self.assertEqual(len(p),483);self.assertEqual(len(self.c),483)
        self.assertEqual(self.c.groupby('split').size().to_dict(),{'train':163,'dev':53,'test':267})
        self.assertTrue((abs(self.c.paired_land_ft2*4-self.c.paired_land)<1e-6).all())
        self.assertTrue((self.c.eligible95==((self.c.paired/self.c.polygon>=.95)&(self.c.paired_land/self.c.land>=.95))).all())
    def test_file_support(self):
        x=read(O/'index_links.csv');files=read(O/'source_files.csv')
        self.assertTrue(files.image.is_unique);self.assertEqual(set(files.image),set(x.image))
        self.assertTrue(x.groupby('image').split.nunique().eq(1).all())
        self.assertTrue(files.sha256.str.fullmatch('[a-f0-9]{64}').all())
        self.assertTrue(((self.c.decoded-self.c.rgb)*.25==self.c.invalid_rgb_in_footprint_ft2).all())
    def test_projection(self):
        w=read(O/'qualified_weights.csv')
        self.assertTrue(np.allclose(w.groupby(['scope','cell']).weight.sum(),1))
        self.assertEqual(set(w.geoid),set(self.c.loc[self.c.eligible95&(self.c.split=='test'),'geoid']))
        p=read(O/'qualified_precision.csv').query('status=="PROJECTED"')
        self.assertTrue(np.allclose(p.halfwidth_pp*p.break_even_sd_pp,p.sd_pp*p.target_pp))
        self.assertFalse(p.halfwidth_pp.isna().any())
    def test_missing_area_attribution(self):
        c=self.c
        self.assertTrue(np.allclose(c.outside_index_ft2+c.invalid_rgb_in_footprint_ft2+c.valid_rgb_but_unmapped_ft2,.25*(c.polygon-c.paired)))
        self.assertTrue(np.allclose(c.filter(regex="^missing_land_ft2_").sum(axis=1),.25*(c.land-c.paired_land)))
    def test_frozen_sensitivity_matches_equal_tract_result(self):
        a=read(O/'qualified_precision.csv').query('scope=="all"')
        b=read(O/'original_weight_sensitivity.csv').query('scope=="all"')
        z=a.merge(b,on=['scope','scenario','contrast'],validate='one_to_one')
        self.assertEqual(len(z),6)
        self.assertTrue(np.allclose(z.halfwidth_pp,z.restricted_weight_halfwidth_pp))
        self.assertTrue(z.original_target_total_span_pp.ge(z.whole_exclusion_span_pp).all())
    def test_window_database(self):
        import gzip,hashlib
        receipt=json.loads((O/'execution_receipt.json').read_text())
        with gzip.open(O/'run'/'planned.sqlite.gz','rb') as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(),receipt['planned_sqlite_sha256'])
        self.assertEqual(sum(v[2] for v in receipt['windows']),483)
    def test_mask_closure(self):
        for gid in self.c.geoid:
            r=json.loads((O/'qualification'/(gid+'.json')).read_text())
            raw=np.array(r['reference_class_counts']);joint=np.array(r['paired_class_counts'])
            self.assertEqual(raw.sum(),r['polygon']);self.assertEqual(joint.sum(),r['paired'])
            self.assertEqual(joint.sum()-joint[4],r['paired_land'])
            self.assertTrue((joint<=raw).all())
if __name__=='__main__':unittest.main()
