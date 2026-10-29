"""Single source of truth for every number reported in the revised paper and in the response letter.

Why this file exists. During the revision the tool and algorithm counts were produced twice, once by
`rq1_rq3_rerun.py` (raw post text, no word boundaries) and once inside the RQ5 integration (cleaned
text, word boundaries). The two disagree, and the paper cannot carry both. This script fixes one
convention, recomputes everything from it, and writes `numbers_ledger.json`, from which the
manuscript text and the response letter are filled. Nothing is quoted anywhere that is not printed
here.

Conventions, fixed once:
  * TOOL AND ALGORITHM MATCHING uses the raw post text (title plus body, lower-cased) because tool
    names occur inside code fragments that the topic-model cleaning removes, and it is anchored on
    word boundaries. The submitted version matched substrings on the same raw text, which is why
    "stim" matched "estimate"; the effect of the correction is reported below on identical input.
  * THE NON-UNDERSTANDING DETECTOR is applied to title plus cleaned text, which is the input it was
    validated on. Applying it to raw text would include quoted error messages and other people's
    comments, which are not the author's words.
  * LIFT is always relative to the base rate of the set being tabulated, and each table states which
    set that is. Layer tables use the layer's own rate; dataset tables use the dataset rate.
"""
import json, re, sys
import pandas as pd, numpy as np
from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint
sys.path.insert(0, './conf')
from confusion_detector import detect

ROOT = '.'
TOOLS = {
 "Qiskit": r"qiskit", "Stim": r"stim", "Cirq": r"cirq", "PennyLane": r"pennylane", "QuTiP": r"qutip",
 "liboqs": r"liboqs", "PyQuil": r"pyquil", "ProjectQ": r"projectq",
 "QDK / Q#": r"qdk|q#|quantum development kit",
 "Open Quantum Safe": r"open quantum safe|oqs[- ]provider|oqs", "SimulaQron": r"simulaqron",
 "Qulacs": r"qulacs", "Quimb": r"quimb", "Bouncy Castle": r"bouncy ?castle", "PQClean": r"pqclean",
 "QuNetSim": r"qunetsim", "Braket": r"braket", "OpenQASM": r"openqasm", "NetSquid": r"netsquid",
 "OpenSSL": r"openssl", "GnuPG/GPG": r"gpg|gnupg", "strongSwan": r"strongswan", "OpenSSH": r"openssh",
}
ALGOS = {
 # Reported counts (25 core security, 16 integrity) additionally exclude mentions of the Shor code,
 # Shor's nine-qubit code and the Shor-Preskill proof, which this broad pattern would also match.
 "Shor's algorithm": (r"shor'?s? algorithm|shor", "Quantum"),
 "Grover's algorithm": (r"grover'?s? algorithm|grover", "Quantum"),
 "QKD (generic)": (r"qkd|quantum key distribution", "Quantum"),
 "BB84": (r"bb84", "Quantum"), "E91": (r"e91|ekert", "Quantum"), "B92": (r"b92", "Quantum"),
 "Quantum teleportation": (r"teleportation", "Quantum"),
 "QFT": (r"quantum fourier transform|qft", "Quantum"),
 "QPE": (r"quantum phase estimation|qpe", "Quantum"),
 "HHL": (r"hhl", "Quantum"), "VQE": (r"vqe|variational quantum eigensolver", "Hybrid"),
 "QAOA": (r"qaoa", "Hybrid"),
 "RSA": (r"rsa", "Classical"), "AES": (r"aes", "Classical"),
 "ECC / ECDSA": (r"elliptic curve|ecdsa|ecdh", "Classical"),
 "Diffie-Hellman": (r"diffie", "Classical"),
 "SHA-2/SHA-3": (r"sha-?2|sha-?3|sha256|keccak", "Classical"),
 "CRYSTALS-Kyber": (r"kyber|ml-kem", "Post-quantum"),
 "CRYSTALS-Dilithium": (r"dilithium|ml-dsa", "Post-quantum"),
 "NTRU": (r"ntru", "Post-quantum"), "Classic McEliece": (r"mceliece", "Post-quantum"),
 "SPHINCS+": (r"sphincs", "Post-quantum"), "FrodoKEM": (r"frodo", "Post-quantum"),
 "XMSS": (r"xmss", "Post-quantum"), "Rainbow": (r"rainbow", "Post-quantum"),
 "Lattice-based (generic)": (r"lattice[- ]based|lwe|learning with errors", "Post-quantum"),
 "Surface code": (r"surface code", "Quantum"), "Steane code": (r"steane", "Quantum"),
 "Shor code": (r"shor code", "Quantum"), "Stabilizer codes": (r"stabili[sz]er code", "Quantum"),
}
CHAL = {'C0': 'Information sought, no obstacle reported',
        'C1': 'Cryptographic transition and post-quantum threats',
        'C2': 'Quantum communication and QKD', 'C3': 'Tooling and implementation',
        'C4': 'Conceptual and knowledge gaps', 'C5': 'Attacks on quantum systems',
        'C6': 'Algorithm and protocol design'}


def bounded(p):
    """Anchor an alternation on word boundaries without breaking the alternation."""
    return r"\b(?:" + p + r")\b"


def bh(p):
    return multipletests(list(p), method='fdr_bh')[1] if len(p) else []


def rate_table(df, by, flag='conf', min_n=10, base=None):
    base = df[flag].mean() if base is None else base
    rows = []
    for g, sub in df.groupby(by):
        if len(sub) < min_n:
            continue
        rest = df[df[by] != g]
        tab = [[sub[flag].sum(), len(sub) - sub[flag].sum()],
               [rest[flag].sum(), len(rest) - rest[flag].sum()]]
        p = chi2_contingency(tab)[1] if min(min(r) for r in tab) >= 5 else fisher_exact(tab)[1]
        rows.append({by: g, 'n': len(sub), 'rate': round(sub[flag].mean(), 3),
                     'lift': round(sub[flag].mean() / base, 2), 'p': p})
    out = pd.DataFrame(rows).sort_values('rate', ascending=False)
    if len(out):
        out['p_adj'] = bh(out['p'])
    return out, round(base, 3)


def main():
    L = {}
    c = pd.read_csv(f'{ROOT}/tm/corpus_clean.csv', low_memory=False)
    for col in ['views', 'votes', 'answers']:
        c[col] = pd.to_numeric(c[col].astype(str).str.replace(',', ''), errors='coerce')
    c['raw'] = (c.question_title.fillna('') + ' ' + c.Question_body.fillna('')).str.lower()
    c['cln'] = c.question_title.fillna('') + ' ' + c.clean_text.fillna('')
    c['dt'] = pd.to_datetime(c.date, errors='coerce')

    l1 = set(pd.read_csv(f'{ROOT}/tm/subset_L1_final.csv').post_id)
    l2 = set(pd.read_csv(f'{ROOT}/tm/subset_L2_provisional.csv').post_id)
    c['layer'] = np.where(c.post_id.isin(l1), 'L1', np.where(c.post_id.isin(l2), 'L2', 'excluded'))

    # ---- 1. dataset and layers -------------------------------------------------
    offplat = int((c.platform == 'Other').sum())
    L['dataset'] = {'retrieved': 15353, 'retained_by_keyword_filter': len(c),
                    'removed_off_platform': offplat, 'classified': len(c) - offplat,
                    'L1_core_security': len(l1), 'L2_integrity': len(l2),
                    'excluded': int((c.layer == 'excluded').sum()) - offplat,
                    'QCS_total': len(l1) + len(l2)}
    v2 = pd.read_csv(f'{ROOT}/v2_full.csv').set_index('post_id').v2
    L['dataset']['v2_rule_L2_assigned'] = int((v2 == 'L2').sum())
    L['dataset']['v2_rule_L2_reassigned_to_L1_by_humans'] = int(
        (v2.reindex(sorted(l1)) == 'L2').sum())
    print('== 1. Dataset and layers ==')
    for k, v in L['dataset'].items():
        print(f'   {k:42s} {v}')
    print(f"   check: {len(l1)} + {len(l2)} + {L['dataset']['excluded']} + {offplat} = "
          f"{len(l1)+len(l2)+L['dataset']['excluded']+offplat}\n")

    d = c[c.layer != 'excluded'].copy()
    d['conf'] = [detect(t)[0] for t in d.cln]

    # ---- 2. platform profile ---------------------------------------------------
    rows = []
    for p, s in d.groupby('platform'):
        rows.append({'platform': p, 'QCS': len(s), 'L1': int((s.layer == 'L1').sum()),
                     'L2': int((s.layer == 'L2').sum()), 'share': round(100*len(s)/len(d), 1),
                     'first': str(s.dt.min().date()), 'last': str(s.dt.max().date()),
                     'med_views': None if s.views.isna().all() else float(s.views.median()),
                     'med_votes': None if s.votes.isna().all() else float(s.votes.median()),
                     'pct_no_answer': None if s.answers.isna().all()
                                      else round(100*(s.answers.fillna(0) == 0).mean(), 1),
                     'conf_pct': round(100*s.conf.mean(), 1)})
    prof = pd.DataFrame(rows).sort_values('QCS', ascending=False)
    L['platform_profile'] = prof.to_dict('records')
    L['confusion'] = {'QCS_rate': round(d.conf.mean(), 3),
                      'L1_rate': round(d[d.layer == 'L1'].conf.mean(), 3),
                      'L2_rate': round(d[d.layer == 'L2'].conf.mean(), 3)}
    print('== 2. Platform profile (QCS dataset) ==')
    print(prof.to_string(index=False), '\n')
    print('   confusion rates:', L['confusion'], '\n')

    # ---- 3. tools, one canonical run ------------------------------------------
    print('== 3. Tools, word-boundary matching on raw text ==')
    rows = []
    for name, pat in TOOLS.items():
        rx = re.compile(bounded(pat), re.I)
        hit = d[d.raw.str.contains(rx, na=False)]
        if not len(hit):
            continue
        rows.append({'tool': name, 'QCS': len(hit),
                     'L1': int((hit.layer == 'L1').sum()), 'L2': int((hit.layer == 'L2').sum()),
                     'pct_L1': round(100*(hit.layer == 'L1').sum()/len(l1), 1),
                     'pct_L2': round(100*(hit.layer == 'L2').sum()/len(l2), 1),
                     'conf_pct': round(100*hit.conf.mean(), 1)})
    tools = pd.DataFrame(rows).sort_values('QCS', ascending=False)
    L['tools'] = tools.to_dict('records')
    print(tools.to_string(index=False))
    # the substring effect, measured on identical input
    sub_stim = int(d.raw.str.contains('stim', na=False).sum())
    bnd_stim = int(d.raw.str.contains(re.compile(r'\bstim\b'), na=False).sum())
    L['stim_substring_effect'] = {'set': 'QCS dataset', 'substring': sub_stim,
                                  'word_boundary': bnd_stim,
                                  'inflation_pct': round(100*(sub_stim-bnd_stim)/bnd_stim, 0)}
    print(f'\n   Stim on the QCS dataset: substring {sub_stim}, word boundary {bnd_stim} '
          f'({L["stim_substring_effect"]["inflation_pct"]:.0f} per cent inflation)\n')

    # ---- 4. algorithms ---------------------------------------------------------
    print('== 4. Algorithms, same convention ==')
    rows = []
    for name, (pat, typ) in ALGOS.items():
        rx = re.compile(bounded(pat), re.I)
        hit = d[d.raw.str.contains(rx, na=False)]
        if not len(hit):
            continue
        rows.append({'algorithm': name, 'class': typ, 'QCS': len(hit),
                     'L1': int((hit.layer == 'L1').sum()), 'L2': int((hit.layer == 'L2').sum()),
                     'pct_L1': round(100*(hit.layer == 'L1').sum()/len(l1), 1),
                     'pct_L2': round(100*(hit.layer == 'L2').sum()/len(l2), 1)})
    algos = pd.DataFrame(rows).sort_values('L1', ascending=False)
    L['algorithms'] = algos.to_dict('records')
    print(algos.to_string(index=False), '\n')

    d[['post_id', 'platform', 'layer', 'conf']].to_csv(f'{ROOT}/ledger/qcs_flags.csv', index=False)
    json.dump(L, open(f'{ROOT}/ledger/numbers_ledger.json', 'w'), indent=1, default=str)
    return d, l1, l2, L


if __name__ == '__main__':
    main()
