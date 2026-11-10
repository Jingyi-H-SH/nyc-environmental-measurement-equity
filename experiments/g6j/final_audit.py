"""Independent archive, geographic denominator and inferential consistency checks."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

root = Path("manifests/g6j")
load = lambda path: json.loads(path.read_text())


def audit(checkpoints=None):
    release = load(root / "release.json")
    common = None
    for family, fingerprint in release["families"].items():
        rows = {}
        windows = pixels = 0
        for path in sorted((root / "run/results" / family).glob("*.json")):
            record = load(path)
            assert record["checkpoint"] == fingerprint
            matrix = np.asarray(record["matrix"])
            assert matrix.shape == (8, 8) and np.all(matrix >= 0)
            rows[path.stem] = (record["input"], record["windows"], tuple(matrix.sum(axis=1)))
            windows += record["windows"]
            pixels += matrix.sum()
        assert (len(rows), windows, pixels) == (265, 17336, 3324001222)
        assert common is None or rows == common
        common = rows
    if checkpoints:
        with tarfile.open(checkpoints) as archive:
            for family, fingerprint in release["families"].items():
                f = archive.extractfile(f"runs/{family}/checkpoint.pt")
                assert hashlib.file_digest(f, "sha256").hexdigest() == fingerprint
    contrasts = pd.read_csv(root / "rq2_contrasts.csv")
    primary = contrasts[contrasts.family.isin(release["formal"]) & contrasts.holm_p.notna()]
    for _, group in primary.groupby(["scope", "family"]):
        g = group.sort_values("p")
        assert len(g) == 8
        p = 2 * t.sf(abs(g.estimate / g.se), g.df)
        np.testing.assert_allclose(g.p, p)
        np.testing.assert_allclose(g.holm_p, np.minimum(1, np.maximum.accumulate(np.arange(8, 0, -1) * p)))
        np.testing.assert_allclose(g.primary_hi - g.estimate, t.ppf(.975, g.df) * g.se)
    assert len(primary) == 48
    gaps = pd.read_csv(root / "rq3_gaps.csv")
    paired = gaps.merge(contrasts.query("metric == 'signed'"), on=["family","scope","outcome","contrast"],validate="one_to_one")
    assert len(paired) == len(gaps)
    np.testing.assert_allclose(paired.ai_gap - paired.reference_gap, paired.estimate, atol=1e-10)
    diag = pd.read_csv(root / "screen_diagnostics.csv").query("q == .25")
    for row in diag.itertuples():
        assert row.unfilled == max(0, row.capacity - row.joint_candidates)
    print(f"Verified {len(common)} common tracts, {pixels:,} pixels per family, 48 primary contrasts, {len(gaps)} gap identities.")
    print(primary.groupby("scope")[["min_effective_blocks", "holm_p"]].min())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoints", type=Path)
    audit(parser.parse_args().checkpoints)
