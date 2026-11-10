import unittest
import numpy as np
import pandas as pd
from measure import sd_icc, project, read
class PrecisionTests(unittest.TestCase):
    def test_block_variation(self):
        f=pd.DataFrame({'block':['a','a','b','b'],'error':[1,1,3,3]})
        self.assertEqual(sd_icc(f)[1],1)
        f.error=[1,3,1,3]
        self.assertEqual(sd_icc(f)[1],0)
    def test_frozen_projection(self):
        w=read('manifests/g6h/qualified_weights.csv')
        geo=read('manifests/g6g/reserve8_roster.csv')[['geoid','block']]
        observed=pd.DataFrame(project(w.merge(geo,on='geoid',validate='many_to_one'),5,.25))
        frozen=read('manifests/g6h/qualified_precision.csv').query("scenario=='central'")
        p=observed.merge(frozen,on=['scope','contrast'],validate='one_to_one')
        self.assertEqual(len(p),4)
        np.testing.assert_allclose(p.halfwidth_pp_x,p.halfwidth_pp_y,rtol=1e-8)
if __name__=='__main__':unittest.main()
