"""Keyword-defined check of the surface-code and decoding result (Section 5.6.4 and Appendix A of the paper).

Run from code/:  python3 decoding_check.py
An integrity post counts as surface-code or decoding work if its title or body, in lower case,
contains any of the six terms below as a substring. The list does not use the topic model.
Reported: 428 posts, 109 stating non-understanding (25.5% against 20.2% for the layer),
lift 1.26 (95% CI 1.07 to 1.48, Wilson interval of the rate divided by the layer rate),
chi-square p = 0.002, and p_adj = 0.005 when the check is added to the family of the seven integrity topic tests of Table 12.
"""
import re
import numpy as np, pandas as pd
from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

TERMS = ['surface code', 'detector error model', 'threshold', 'decoding', 'decode', 'logical error rate']
NO_TITLE = '(no title, GitHub thread)'


def test(flag, mask):
    a = int(flag[mask].sum()); n = int(mask.sum()); c = int(flag[~mask].sum()); m = int((~mask).sum())
    tab = [[a, n - a], [c, m - c]]
    return fisher_exact(tab)[1] if min(min(r) for r in tab) < 5 else chi2_contingency(tab)[1]


d = pd.read_csv('../data/QCS_dataset_5163.csv', keep_default_na=False)
lab = pd.read_csv('../data/QCS_labels_5163.csv')
d = d.merge(lab[['post_id', 'layer', 'topic', 'states_non_understanding']], on='post_id')
d['title'] = d['title'].replace(NO_TITLE, '')
d['nu'] = d.states_non_understanding.eq('yes')

s = d[d.layer == 'integrity'].reset_index(drop=True)
raw = (s.title.astype(str) + ' ' + s.body.astype(str)).str.lower()
hit = np.logical_or.reduce([raw.str.contains(re.escape(t), regex=True).values for t in TERMS])
nu = s.nu.values
a, n, base = int(nu[hit].sum()), int(hit.sum()), nu.mean()
lo, hi = proportion_confint(a, n, method='wilson')
p_kw = test(nu, hit)
print(f'matched {n} posts, {a} state non-understanding: rate {a/n:.3f} against {base:.3f} for the layer')
print(f'lift {a/n/base:.2f} (95% CI {lo/base:.2f} to {hi/base:.2f}), p = {p_kw:.3f}')

t = d[d.layer == 'integrity'].reset_index(drop=True)
ps = [test(t.nu.values, (t.topic == topic).values) for topic in sorted(t.topic.unique())]
print(f'p_adj with the seven integrity topic tests: {multipletests(ps + [p_kw], method="fdr_bh")[1][-1]:.3f}')

# Stated non-understanding by challenge category (categories with at least ten posts),
# each tested against the rest of its layer, Benjamini-Hochberg within the layer.
lab['nu'] = lab.states_non_understanding.eq('yes')
for layer in ['integrity', 'core security']:
    t = lab[lab.layer == layer].reset_index(drop=True)
    cats = [c for c in sorted(t.challenge.unique()) if (t.challenge == c).sum() >= 10]
    pv = [test(t.nu.values, (t.challenge == c).values) for c in cats]
    for c, p, q in zip(cats, pv, multipletests(pv, method='fdr_bh')[1]):
        m = (t.challenge == c).values
        print(f'{layer} | {c}: {int(t.nu.values[m].sum())}/{int(m.sum())} = {t.nu.values[m].mean():.3f}, p = {p:.4f}, p_adj = {q:.3f}')
