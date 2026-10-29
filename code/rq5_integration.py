"""RQ5: integrated analysis of where practitioners state that they do not understand something.

Relates challenges to tools, algorithms and topics, using a measure
that survived validation: the manually coded, lexicon-detected statement of non-understanding.


For every cross-tabulation we report the rate, a chi-square test of independence against the rest of
the corpus, and the lift over the corpus base rate, so that the reader can see both whether a
difference is distinguishable from sampling noise and whether it is large enough to matter.
"""
import sys, json, pandas as pd, numpy as np
from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.multitest import multipletests

def bh(p):
    """Benjamini-Hochberg adjusted p-values, one test per group."""
    return multipletests(list(p), method='fdr_bh')[1]
sys.path.insert(0, 'conf')
from confusion_detector import detect

def rate_table(df, by, flag='confusion', min_n=10):
    base = df[flag].mean()
    rows = []
    for g, sub in df.groupby(by):
        if len(sub) < min_n:
            continue
        rest = df[df[by] != g]
        tab = [[sub[flag].sum(), len(sub) - sub[flag].sum()],
               [rest[flag].sum(), len(rest) - rest[flag].sum()]]
        if min(min(r) for r in tab) < 5:
            p = fisher_exact(tab)[1]; test = 'Fisher'
        else:
            p = chi2_contingency(tab)[1]; test = 'chi2'
        rows.append({by: g, 'n': len(sub), 'confusion_n': int(sub[flag].sum()),
                     'rate': sub[flag].mean(), 'lift': sub[flag].mean() / base if base else np.nan,
                     'p': p, 'test': test})
    out = pd.DataFrame(rows).sort_values('rate', ascending=False)
    # Benjamini-Hochberg correction, because one test is run per group
    if len(out):
        out['p_adj'] = bh(out['p'])
    return out, base

def main():
    corp = pd.read_csv('tm/corpus_clean.csv', low_memory=False)
    corp['text'] = corp['question_title'].fillna('') + ' ' + corp['clean_text'].fillna('')
    l1 = set(pd.read_csv('tm/subset_L1_final.csv').post_id)
    l2 = set(pd.read_csv('tm/subset_L2_provisional.csv').post_id)
    d = corp[corp.post_id.isin(l1 | l2)].copy()
    d['layer'] = np.where(d.post_id.isin(l1), 'L1 core security', 'L2 integrity')
    d['confusion'] = [detect(t)[0] for t in d.text]
    print(f"QCS posts: {len(d)}   confusion rate: {d.confusion.mean():.3f}\n")

    print("== By layer ==")
    print(d.groupby('layer').confusion.agg(['size', 'sum', 'mean']).round(3).to_string(), "\n")

    print("== By platform ==")
    t, base = rate_table(d, 'platform')
    print(f"corpus base rate {base:.3f}"); print(t.round(4).to_string(index=False), "\n")

    print("== By topic, core-security model k=7 ==")
    tp = pd.read_csv('tm/post_topic_k7_no_boost_L1final.csv')[['post_id', 'topic']]
    m = d.merge(tp, on='post_id')
    t, base = rate_table(m, 'topic', min_n=15)
    print(f"L1 base rate {base:.3f}"); print(t.round(4).to_string(index=False), "\n")

    print("== By topic, integrity model k=7 ==")
    tp2 = pd.read_csv('tm/post_topic_k7_no_boost_L2prov.csv')[['post_id', 'topic']]
    m2 = d.merge(tp2, on='post_id')
    t, base = rate_table(m2, 'topic', min_n=15)
    print(f"L2 base rate {base:.3f}"); print(t.round(4).to_string(index=False), "\n")

    print("== By tool ==")
    import re
    TOOLS = json.load(open('conf/tools.json'))
    rows = []
    base = d.confusion.mean()
    for name, pats in TOOLS.items():
        # word boundaries are mandatory: the original script used substring matching,
        # so "stim" matched "estimate". Alternations already carrying \\b are left alone.
        rx = re.compile("|".join(p if "\\b" in p or "|" in p else rf"\b{p}\b" for p in pats), re.I)
        hit = d[d.text.str.contains(rx)]
        if len(hit) < 20:
            continue
        rest = d[~d.index.isin(hit.index)]
        tab = [[hit.confusion.sum(), len(hit) - hit.confusion.sum()],
               [rest.confusion.sum(), len(rest) - rest.confusion.sum()]]
        p = chi2_contingency(tab)[1] if min(min(r) for r in tab) >= 5 else fisher_exact(tab)[1]
        rows.append({'tool': name, 'n': len(hit), 'rate': hit.confusion.mean(),
                     'lift': hit.confusion.mean() / base, 'p': p})
    tt = pd.DataFrame(rows).sort_values('rate', ascending=False)
    tt['p_adj'] = bh(tt['p'])
    print(f"corpus base rate {base:.3f}"); print(tt.round(4).to_string(index=False), "\n")

    d[['post_id', 'platform', 'layer', 'confusion']].to_csv('conf/confusion_all_qcs.csv', index=False)

if __name__ == '__main__':
    main()
