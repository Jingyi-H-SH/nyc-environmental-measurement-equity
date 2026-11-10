import unittest
import numpy as np
from scipy.stats import rankdata
from spatial import Design,CONTRASTS,bounds,holm
from distribution import midrank


class TestSpatial(unittest.TestCase):
    def test_pairing(self):
        cell=np.repeat(['00','01','10','11'],4)
        blocks=np.tile(['0,0','1,0','4,1','9,0'],4)
        d=Design(cell,blocks,np.ones(16))
        ref=np.arange(16.)
        e=np.array([0]*4+[1]*4+[2]*4+[6]*4,dtype=float)
        for co,expected in [(CONTRASTS['extreme'],6),(CONTRASTS['factorial'],3)]:
            result=d.contrast(e,co)
            self.assertAlmostEqual(result['estimate'],expected)
            self.assertAlmostEqual(co@(d.W@(ref+e))-co@(d.W@ref),expected)
            self.assertEqual(result['primary_hi'],result['primary_lo'])
            lo,hi=bounds(e-1,e+2,d,co)
            self.assertLess(lo,expected)
            self.assertGreater(hi,expected)

    def test_ranks_and_multiplicity(self):
        x=np.array([2.,1,2,7])
        np.testing.assert_allclose(midrank(x,np.ones(4)),(rankdata(x)-.5)/4)
        np.testing.assert_allclose(holm([.02,.9,.001]),[.04,.9,.003])

if __name__=='__main__':unittest.main()
