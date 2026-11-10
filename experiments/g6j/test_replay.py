"""Exercise the full reporting path on fabricated perfect predictions; no imagery needed."""
import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
from analyze import main as analyze, read
from distribution import main as distribution
from secondary import main as secondary
from summarize import main as summarize


class TestReplay(unittest.TestCase):
    def test_exact_reference(self):
        repo=Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            self.addCleanup(os.chdir,repo)
            manifests=Path('manifests')
            stage=manifests/'g6j'
            stage.mkdir(parents=True)
            Path('reports').mkdir()
            for prior in ('g6d','g6g','g6h'):
                (manifests/prior).symlink_to(repo/manifests/prior,target_is_directory=True)
            cohort=read(manifests/'g6h/coverage.csv').query("split=='test' and eligible95==True")
            self.assertEqual(len(cohort),265)
            families=['cnn','segformer','yolo','ijepa']
            (stage/'release.json').write_text(json.dumps({'families':dict.fromkeys(families,'synthetic')}))
            results=stage/'run/results'
            for family in families:
                folder=results/family
                folder.mkdir(parents=True)
                (stage/'run'/(family+'-receipt.json')).write_text(json.dumps({'checkpoint':'synthetic','tracts':265}))
                for record in cohort.itertuples(index=False):
                    matrix=np.diag(json.loads(record.paired_class_counts)[1:]).tolist()
                    (folder/(record.geoid+'.json')).write_text(json.dumps({'checkpoint':'synthetic','matrix':matrix}))
            analyze(results)
            distribution()
            secondary()
            screen=pd.read_csv(stage/'screening.csv')
            self.assertTrue((screen.omitted.eq(0) & screen.added.eq(0)).all())
            summarize()
            q=pd.read_csv(stage/'rq2_contrasts.csv')
            self.assertTrue(np.allclose(q.estimate,0))
            b=pd.read_csv(stage/'original267_bounds.csv')
            self.assertTrue(((b.lower<=1e-10)&(b.upper>=-1e-10)).all())
            s=pd.read_csv(stage/'rq1_native_scores.csv')
            self.assertTrue(np.allclose(s.f1,1))

if __name__=='__main__':unittest.main()
