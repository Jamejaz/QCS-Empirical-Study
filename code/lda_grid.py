"""LDA grid search k=2..30 on the cleaned corpus, with and without keyword boosting.
Settings identical to the original study (alpha=asymmetric, eta=0.01, seed=100, passes=10, iterations=100, chunksize=500).
Reports c_v and u_mass coherence. Usage: python3 lda_grid.py [subset_ids.csv]"""
import pandas as pd, json, sys, time, gensim, logging
from gensim import corpora
from gensim.models import CoherenceModel
logging.basicConfig(level=logging.WARNING)

BOOST = {  # security + integrity vocabulary only; tool names deliberately excluded (avoids RQ1 circularity)
 'qkd','bb84','eavesdropper','eavesdropping','eve','encryption','encrypt','decrypt','cryptography','cryptographic','crypto',
 'post_quantum','kyber','dilithium','ntru','lattice','rsa','aes','ecc','attack','attacker','adversary','security','secure',
 'side_channel','trojan','key_distribution','private_key','public_key','quantum_key','key_exchange',
 'error_correction','surface_code','stabilizer','fault_tolerant','decoherence','noise','syndrome','decoder','logical_qubit',
 'error_mitigation','error_rate','depolarize_channel','fidelity','calibration','noise_model','syndrome_measurement'}

def load(subset=None):
    d = pd.read_csv("corpus_clean.csv")
    d = d[(d.platform != "Other") & (d.tokens != "[]")]
    if subset is not None: d = d[d.post_id.isin(subset)]
    return d, [json.loads(t) for t in d.tokens]

def boost(docs, f=3): return [[w for t in x for w in ([t] * f if t in BOOST else [t])] for x in docs]

def fit(texts, k, seed=100):
    dic = corpora.Dictionary(texts); dic.filter_extremes(no_below=5, no_above=0.5)
    bow = [dic.doc2bow(x) for x in texts]
    m = gensim.models.LdaModel(bow, id2word=dic, num_topics=k, random_state=seed, chunksize=500, passes=10,
                               iterations=100, alpha="asymmetric", eta=0.01)
    return m, dic, bow

def coh(m, texts, dic, bow):
    cv = CoherenceModel(model=m, texts=texts, dictionary=dic, coherence="c_v", processes=1).get_coherence()
    um = CoherenceModel(model=m, corpus=bow, dictionary=dic, coherence="u_mass").get_coherence()
    return cv, um

if __name__ == "__main__":
    subset = set(pd.read_csv(sys.argv[1]).post_id) if len(sys.argv) > 1 else None
    tag = sys.argv[2] if len(sys.argv) > 2 else "full"
    d, docs = load(subset)
    rows = []
    for variant, texts in [("no_boost", docs), ("boost3x", boost(docs))]:
        for k in range(2, 31):
            t0 = time.time(); m, dic, bow = fit(texts, k); cv, um = coh(m, texts, dic, bow)
            rows.append(dict(variant=variant, k=k, c_v=round(cv, 4), u_mass=round(um, 4), vocab=len(dic), docs=len(texts)))
            print(variant, k, round(cv, 4), round(um, 3), f"{time.time()-t0:.0f}s", flush=True)
            pd.DataFrame(rows).to_csv(f"coherence_grid_{tag}.csv", index=False)
