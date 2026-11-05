"""Challenge associations of RQ5 for tools, algorithms and topics (Sections 5.6.1 to 5.6.3).

Run from code/ after prepare_corpus.py:  python3 association_tests.py
Each group (a tool, algorithm or topic named in at least one post of the layer) is tested against the
rest of its layer for every challenge category: chi-square with continuity correction, or Fisher's
exact test where any cell holds fewer than five posts. Benjamini-Hochberg correction is applied over
all group-category pairs of one analysis in one layer. Tool and algorithm names are matched on word
boundaries in the lower-cased title and body.
Writes ../results/association_tests.csv.
"""
import re
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.multitest import multipletests

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

NO_TITLE = '(no title, GitHub thread)'


def family(s, groups):
    rows = []
    for g, mask in groups:
        if mask.sum() == 0:
            continue
        for c in sorted(s.challenge.unique()):
            y = (s.challenge == c).values
            a = int((y & mask).sum()); n = int(mask.sum()); b = int((y & ~mask).sum()); m = int((~mask).sum())
            tab = [[a, n - a], [b, m - b]]
            p = fisher_exact(tab)[1] if min(min(r) for r in tab) < 5 else chi2_contingency(tab)[1]
            rows.append(dict(group=g, category=c, k=a, n=n, rate=a / n, lift=(a / n) / y.mean(), p=p))
    r = pd.DataFrame(rows)
    r['p_adj'] = multipletests(r.p, method='fdr_bh')[1]
    return r


d = pd.read_csv('../data/QCS_dataset_5163.csv', keep_default_na=False)
lab = pd.read_csv('../data/QCS_labels_5163.csv')
d = d.merge(lab[['post_id', 'layer', 'topic', 'challenge']], on='post_id')
d['title'] = d['title'].replace(NO_TITLE, '')
d['raw'] = (d.title.astype(str) + ' ' + d.body.astype(str)).str.lower()
out = []
for layer in ['core security', 'integrity']:
    s = d[d.layer == layer].reset_index(drop=True)
    rx = lambda p: s.raw.str.contains(re.compile(r'\b(?:' + p + r')\b', re.I)).values
    for analysis, groups in [('tool', [(k, rx(p)) for k, p in TOOLS.items()]),
                             ('algorithm', [(k, rx(p)) for k, (p, _) in ALGOS.items()]),
                             ('topic', [(t, (s.topic == t).values) for t in sorted(s.topic.unique())])]:
        r = family(s, groups); r.insert(0, 'analysis', analysis); r.insert(0, 'layer', layer); out.append(r)
res = pd.concat(out)
res.to_csv('../results/association_tests.csv', index=False)
show = res[(res.p_adj < 0.05) & (res.lift > 1) & (res.k >= 5)].sort_values(['layer', 'analysis', 'p_adj'])
print(show[['layer', 'analysis', 'group', 'category', 'k', 'n', 'lift', 'p_adj']].round(4).to_string(index=False))
