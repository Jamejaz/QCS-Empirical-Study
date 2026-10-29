"""Seed robustness: mean and SD of c_v over 5 random seeds for k = 6..24 (step 2), both variants."""
import pandas as pd, sys
from lda_grid import load, boost, fit, coh
tag = sys.argv[1] if len(sys.argv) > 1 else "full"
subset = set(pd.read_csv(sys.argv[2]).post_id) if len(sys.argv) > 2 else None
d, docs = load(subset); rows = []
for variant, texts in [("no_boost", docs), ("boost3x", boost(docs))]:
    for k in range(6, 25, 2):
        for seed in [100, 1, 2, 3, 4]:
            m, dic, bow = fit(texts, k, seed); cv, um = coh(m, texts, dic, bow)
            rows.append(dict(variant=variant, k=k, seed=seed, c_v=cv, u_mass=um))
            pd.DataFrame(rows).to_csv(f"coherence_seeds_{tag}.csv", index=False)
        print(variant, k, flush=True)
