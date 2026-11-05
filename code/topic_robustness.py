"""Topic models of the two layers and their robustness under reseeding.

Run after prepare_corpus.py (which writes corpus_clean.csv):
    python3 topic_robustness.py            # everything
    python3 topic_robustness.py --no-coherence

Settings are those of the paper: k = 7 per layer, alpha = asymmetric, eta = 0.01, passes = 10,
iterations = 100, chunksize = 500, dictionary filter no_below = 5, no_above = 0.5.
The reference fit uses seed 100; it reproduces the topic of every post in data/QCS_labels_5163.csv.
The four refits use seeds 1, 2, 3 and 4.

Outputs (written to ../topics/)
  coherence_by_k_seeds.csv  c_v and u_mass for every layer, k and seed (k 5-9 core security, 4-14 integrity)
  coherence_by_k.csv        mean and standard deviation of c_v across the five seeds
  topic_stability.csv       per topic, mean Jaccard overlap of the top ten words between the reference fit and
                            the best-matching topic of each refit
  topic_retention.csv       share of posts that keep their topic in each refit (topics matched by post overlap)
  table11_refits.csv        for each topic, whether the challenge category of Table 11 is still significantly
                            over-represented (BH-adjusted p < 0.05, lift > 1) in each refit; the rows with
                            seed 100 are Table 11 itself
  nonunderstanding_rank.csv rank of each topic by rate of stated non-understanding in each fit (1 = highest)
"""
import sys, json
import numpy as np, pandas as pd, gensim
from gensim import corpora
from gensim.models import CoherenceModel
from scipy.optimize import linear_sum_assignment
from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.multitest import multipletests

SEEDS = [100, 1, 2, 3, 4]
KRANGE = {'core security': range(5, 10), 'integrity': range(4, 15)}


def model(texts, k, seed):
    dic = corpora.Dictionary(texts); dic.filter_extremes(no_below=5, no_above=0.5)
    bow = [dic.doc2bow(x) for x in texts]
    m = gensim.models.LdaModel(bow, id2word=dic, num_topics=k, random_state=seed, chunksize=500, passes=10,
                               iterations=100, alpha='asymmetric', eta=0.01)
    return m, dic, bow


def dominant(m, bow):
    return np.array([max(m.get_document_topics(b, minimum_probability=0), key=lambda x: x[1])[0] for b in bow])


def pair_tests(df, col):
    """Every topic x category pair of a layer: chi-square, or Fisher's exact test when a cell holds fewer
    than five posts; Benjamini-Hochberg over all pairs of the layer."""
    rows = []
    for t, sub in df.groupby(col):
        rest = df[df[col] != t]
        for c in df.challenge.unique():
            a = int((sub.challenge == c).sum()); b = len(sub) - a
            cc = int((rest.challenge == c).sum()); dd = len(rest) - cc
            tab = [[a, b], [cc, dd]]
            p = fisher_exact(tab)[1] if min(a, b, cc, dd) < 5 else chi2_contingency(tab)[1]
            rows.append(dict(topic=t, category=c, n=len(sub), k=a,
                             lift=(a / len(sub)) / (df.challenge == c).mean(), p=p))
    r = pd.DataFrame(rows); r['p_adj'] = multipletests(r.p, method='fdr_bh')[1]
    return r


def main(coherence=True):
    corp = pd.read_csv('corpus_clean.csv', low_memory=False)
    lab = pd.read_csv('../data/QCS_labels_5163.csv')
    d = corp.merge(lab[['post_id', 'layer', 'topic', 'challenge', 'states_non_understanding']], on='post_id')
    coh, stab, ret, t11, nur = [], [], [], [], []
    for layer in ['core security', 'integrity']:
        s = d[d.layer == layer].reset_index(drop=True)
        texts = [json.loads(t) for t in s.tokens]
        if coherence:
            for k in KRANGE[layer]:
                for seed in SEEDS:
                    m, dic, bow = model(texts, k, seed)
                    coh.append(dict(layer=layer, k=k, seed=seed,
                                    c_v=CoherenceModel(model=m, texts=texts, dictionary=dic, coherence='c_v',
                                                       processes=1).get_coherence(),
                                    u_mass=CoherenceModel(model=m, corpus=bow, dictionary=dic,
                                                          coherence='u_mass').get_coherence()))
        fits = {}
        for seed in SEEDS:
            m, dic, bow = model(texts, 7, seed)
            fits[seed] = ([set(w for w, _ in m.show_topic(t, topn=10)) for t in range(7)], dominant(m, bow))
        names = sorted(s.topic.unique())
        ref_words, ref_dom = fits[100]
        ref_name = pd.crosstab(pd.Series(ref_dom, name='fit'), s.topic).idxmax(axis=1).to_dict()
        assert all((pd.Series(ref_dom).map(ref_name) == s.topic)), 'reference fit does not reproduce the labels'
        for t in range(7):
            j = [max(len(ref_words[t] & o) / len(ref_words[t] | o) for o in fits[sd][0]) for sd in SEEDS[1:]]
            stab.append(dict(layer=layer, topic=ref_name[t], top10_jaccard_stability=round(float(np.mean(j)), 2)))
        ref = pair_tests(s, 'topic')
        best = ref[ref.k >= 5].sort_values('lift', ascending=False).groupby('topic').head(1).set_index('topic')
        s['nu'] = s.states_non_understanding.eq('yes')
        for seed in SEEDS:
            dom = fits[seed][1]
            ct = pd.crosstab(s.topic, dom).reindex(index=names, columns=range(7), fill_value=0)
            ri, ci = linear_sum_assignment(-ct.values)
            s['m'] = pd.Series(dom).map({ci[i]: names[ri[i]] for i in range(len(ri))})
            ret.append(dict(layer=layer, seed=seed, share_keeping_topic=round(float((s.m == s.topic).mean()), 3)))
            r = pair_tests(s, 'm')
            for n in names:
                row = r[(r.topic == n) & (r.category == best.loc[n, 'category'])].iloc[0]
                t11.append(dict(layer=layer, topic=n, category=best.loc[n, 'category'], seed=seed,
                                n=int(row.n), lift=round(row.lift, 2), p_adj=round(row.p_adj, 4),
                                significant=bool(row.p_adj < 0.05 and row.lift > 1)))
            rank = s.groupby('m').nu.mean().rank(ascending=False, method='min')
            for n in names:
                nur.append(dict(layer=layer, topic=n, seed=seed, rank=int(rank[n])))
    if coherence:
        c = pd.DataFrame(coh); c.to_csv('../topics/coherence_by_k_seeds.csv', index=False)
        c.groupby(['layer', 'k']).c_v.agg(c_v_mean='mean', c_v_sd='std').reset_index().to_csv('../topics/coherence_by_k.csv', index=False)
    pd.DataFrame(stab).to_csv('../topics/topic_stability.csv', index=False)
    pd.DataFrame(ret).to_csv('../topics/topic_retention.csv', index=False)
    t = pd.DataFrame(t11); t.to_csv('../topics/table11_refits.csv', index=False)
    pd.DataFrame(nur).to_csv('../topics/nonunderstanding_rank.csv', index=False)
    summ = t[t.seed != 100].groupby(['layer', 'topic']).significant.sum()
    print('Table 11 associations significant in the reference fit and in n of the four refits:')
    print(summ.to_string())


if __name__ == '__main__':
    main(coherence='--no-coherence' not in sys.argv)
