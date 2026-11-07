# Coding rules

This document describes how the posts were collected, filtered and labelled. The scripts that apply these rules are in `code/`.

## 1. Data collection

### 1.1 Platforms

| Platform | Posts retrieved | Posts retained |
|---|---:|---:|
| Quantum Computing Stack Exchange (QCSE) | 11,987 | 4,408 |
| Math Stack Exchange (MSE) | 685 | 99 |
| Stack Exchange Security (SES) | 94 | 59 |
| Stack Overflow (SO) | 446 | 131 |
| Reddit | 1,027 | 106 |
| GitHub | 1,114 | 360 |
| **Total** | **15,353** | **5,163** |

The data were retrieved on 5 February 2025. GitHub items are issue threads and discussion threads, each counted as one post. In `data/QCS_dataset_5163.csv` the platform of a post is taken from its URL, so the retained posts there are 102 Reddit, 361 GitHub and 3 on other sites (news or preprint links, removed before classification); the other platforms are as above. Reddit posts come from r/QuantumComputing and r/Qiskit; the Reddit API returns a limited number of the most recent posts of a listing, so 87 of the 102 Reddit posts date from 2024 or 2025.

### 1.2 Search query

The following query was used on every platform:

```
((Quantum) AND (Computing OR Computing Security OR Post Quantum Computing OR Crypto
OR Information OR Algorithm OR Gates OR Error OR encryption)) OR (Qiskit)
```

Reddit posts were collected through the Reddit API (PRAW), Stack Overflow and the Stack Exchange sites with BeautifulSoup, and GitHub threads with Selenium.

### 1.3 Keyword filter

A post was kept if it contained the word "quantum" and at least one of the following 45 terms.

- **Error correction and fault tolerance (23):** error correction, surface code, steane code, shor code, toric code, color code, quantum parity check, syndrome measurement, stabilizer, fault tolerant, magic state distillation, state injection model, zero noise extrapolation, probabilistic error cancellation, measurement error mitigation, randomised benchmarking, depolarizing channel, decoherence, dynamical decoupling, cross talk, qubit leakage, quantum gate calibration, lattice structure
- **Cryptography and key distribution (9):** quantum key distribution, qkd, bb84, e91, ntru, rainbow, homomorphic encryption, encryption, quantum shielding
- **Quantum information (4):** no cloning theorem, quantum teleportation, bell test, entanglement purification
- **Tools and algorithms (3):** cirq, stim, vqe
- **Short forms (6):** noise, error, surface, steane, shor, toric

The terms were matched as substrings, so a short form can also match inside a longer word (for example, "shor" inside "short"). The filter therefore kept many posts that are not about security, and every retained post was classified into a layer before analysis (Section 2). All later counts of tools and algorithms use whole-word matching.

## 2. Layers

Each post is assigned to one layer according to the main concern of the person asking.

| Layer | Definition | Examples |
|---|---|---|
| Core security | Protecting confidentiality, integrity or authenticity against an adversary, or cryptography affected by quantum computing. Includes the threat of Shor's and Grover's algorithms to RSA, ECC and AES; post-quantum cryptography and its libraries; QKD protocols such as BB84 and E91; attacks on quantum hardware or cloud services; and delegated or verifiable quantum computation. | "How long until quantum computers can decrypt RSA using Shor?"; "How to show BB84 is safe against imperfect cloning?" |
| Integrity of computation | Whether a quantum computation stays correct despite faults that are not caused by an adversary. Includes error correction, stabilizer and surface codes, fault tolerance, decoders, decoherence, noise models, error mitigation and calibration. | "How to initialize logical qubit stabilizer states fault-tolerantly?"; "How to change the noise properties of a Qiskit noise model?" |
| Development context | About quantum computing, but the main concern is neither security nor integrity, for example programming, installation, SDK usage, or algorithms for chemistry or optimisation. | "Plotting Bloch sphere in QuTiP" |
| Out of scope | Not about quantum computing, or empty, unreadable or a news link without discussion. | |

**Decision rules**

1. Code the main concern of the post, not every word mentioned. A passing mention of "secure" or "noise" is not enough.
2. If a post is about both security and integrity, choose core security.
3. A post on Shor's or Grover's algorithm is core security only if its cryptographic consequence is part of the question; implementing Shor's algorithm to factor 15 is development context.
4. Noise or error correction in the context of an attack, such as fault injection, is core security.
5. If a decision is not possible after reading the full post, give the best label and mark it as unsure.
6. Security work that runs into a tooling problem stays core security, for example a build error in liboqs or an import error while coding BB84.
7. Classical cryptography with no link to quantum computing is out of scope.
8. "Quantum" used in an unrelated sense (for example, a time quantum in scheduling) is out of scope.
9. Classical cryptography is core security only if the post asks about it in light of quantum computing, for example whether RSA-2048 is safe against quantum computers.

## Use of an LLM in labelling

Claude Opus 5.5 assisted with initial coding in round 1, round 2, integrity challenge classification, the adjudication of core-security challenge labels, and the 200-post evaluation of stated non-understanding. The first author reviewed the LLM-drafted labels against the relevant codebooks. The LLM-drafted adjudications of the core-security challenge labels were verified by the second author. In round 1, the third author coded the same 360 posts independently without access to the drafts or the first author's labels, consulting an LLM on 10 borderline cases. In round 2, the first author reviewed all 486 candidates. Round 3 involved independent re-coding of 100 of these posts by the second author, who had not participated in round 2. Round 4 used two independent coders without LLM assistance. The second author adjudicated coding disagreements. The LLM did not make final coding decisions. Rule-assigned integrity-layer labels outside the core-security candidates were retained and evaluated through independent sampling.

## 3. Keyword rules for layer assignment

The keyword rules assign a layer to every post automatically. Every core-security candidate was then reviewed individually (round 2), and the integrity layer was validated on samples (see `validation/`). The final rules are in `code/layer_rules_final.py`, and the first version is in `code/layer_rules_first_version.py`.

| Term group | Terms |
|---|---|
| Quantum context (required) | qubit, quantum, qiskit, cirq, qkd, shor, grover, qpu, nisq, ibmq, stim, pennylane, qutip |
| Core security, strong terms | qkd, bb84, e91, b92, quantum key distribution, key distribution, post-quantum, pqc, quantum-safe, quantum-resistant, kyber, ml-kem, dilithium, ml-dsa, sphincs, mceliece, ntru, liboqs, oqs-provider, pqclean, open quantum safe, eavesdropping, cryptanalysis, side channel, fault injection, trojan, quantum money, blind quantum, delegated quantum, verifiable quantum, one-time pad, quantum cryptography, harvest now |
| Core security, context terms | crypto, encryption, decryption, cipher, rsa, aes, elliptic curve, ecdsa, ecdh, diffie, digital signature, authentication, key length, key size, attack, adversary, secure, security, insecure, vulnerability, brute force, confidentiality, privacy, tampering, malicious, threat |
| Exclusion terms (development context) | parameterized quantum circuit, pqc followed within 80 characters of the same sentence by keras, tensorflow, pennylane, vqc or agent, time quantum, send_quantum, firefox quantum, imagemagick |
| Integrity, strong terms | error correction, qec, surface code, color code, toric code, steane, shor code, repetition code, stabilizer, fault tolerance, logical qubit, syndrome, decoder, decoding, mwpm, bposd, decoherence, dephasing, error mitigation, zero-noise extrapolation, magic state, distillation, threshold theorem, lattice surgery, transversal, kraus, depolarizing, amplitude damping, crosstalk, readout error, noise model, noise channel, t1, t2, coherence time, randomized benchmarking, quantum channel |
| Integrity, weak terms | noise, noisy, error rate, fidelity, calibration, bit flip, phase flip, leakage |
| Ignored for integrity | text of error messages and stack traces |

The rules are applied in this order:

1. Out of scope if the post is not from one of the six platforms, is shorter than 30 characters, or contains no quantum-context term.
2. Development context if an exclusion term is present and no strong core-security term. Because this rule applies before rule 4, a post containing an exclusion term is not assigned to the integrity layer.
3. Core security if there is a strong core-security term, or if context terms are prominent (one in the title and at least two in the post, or three or more in the post).
4. Integrity if, after removing error-message text, there is a strong integrity term in the title, two strong integrity terms, one strong and one weak term, or a weak term in the title and at least two weak terms in the post.
5. Core security if a context term appears in the title.
6. Otherwise development context.

Names of quantum frameworks (Qiskit, Cirq, Stim, PennyLane, QuTiP) only show that a post concerns quantum computing and do not decide its layer. Names of post-quantum libraries (liboqs, Open Quantum Safe, PQClean) count as core-security evidence. Running the final rules without the library names changes the core-security nomination of none of the 5,160 classified posts (`code/library_names_check.py`).

## 4. Challenge categories: core security

| Category | Definition |
|---|---|
| Quantum communication and QKD | The security of key distribution protocols, eavesdropping strategies and their effect, and QKD in practice. |
| Information sought, no obstacle reported | The post asks for an explanation, an overview or literature without reporting a specific problem. |
| Tooling and implementation | Practical use of cryptographic libraries and protocols in software, including post-quantum support in existing tools and build or configuration problems. |
| Cryptographic transition and post-quantum threats | Whether deployed schemes remain secure, and how and when to migrate. |
| Algorithm and protocol design | Design and security analysis of quantum protocols and attacks, including security proofs. |
| Conceptual and knowledge gaps | A misunderstanding of a basic concept with no more specific subject. Used only when no other category fits. |
| Attacks on quantum systems | Attacks on quantum hardware or cloud quantum services, such as fault injection, side channels and crosstalk. |

Each post receives one category, the main difficulty it reports.

## 5. Challenge categories: integrity of computation

| Category | Definition |
|---|---|
| No difficulty reported | Release notes, announcements, requests for literature or an overview, without a question about a specific concept or task. |
| Code construction and properties | Construction, properties and classification of codes: logical operators, bounds, parameters, stabilizer groups, and what a named code can correct. |
| Fault-tolerant logical operations | Computation on encoded qubits: transversal gates, code switching, magic states and distillation, lattice surgery, logical circuit compilation. |
| Decoding, thresholds and logical error rates | Decoders and their behaviour, threshold estimation, memory experiments and logical error rates, including when a simulator is used. |
| Noise channels and their mathematics | Channels and their action on states, correctability of a channel, twirling, distances between noisy and ideal states, and the density-matrix description of noise. |
| Hardware noise: characterisation and mitigation | Noise on real devices: T1 and T2, fidelity, randomized benchmarking, error mitigation (ZNE, PEC, dynamical decoupling) and noise-aware circuit or backend choice. |
| Simulators and QEC software | A concrete problem with a tool, such as Qiskit, Aer, Stim, PyMatching, Cirq or QuTiP: its capabilities, API use, error messages or performance. |
| Conceptual foundations | General questions on why error correction works, notation and definitions. Used only when no other category fits. |

Each post receives one category, the main difficulty it reports. A subject category takes precedence over "Conceptual foundations", and "No difficulty reported" is used only when no specific concept or task is asked about.

## 6. Topics

Each layer was modelled separately with LDA (seven topics, five random seeds). Two authors labelled each topic independently from its fifteen most probable words and its representative posts, and settled differences by discussion. Stability is the Jaccard overlap between the top ten words of a topic in the reference fit (seed 100) and those of its best-matching topic in each of four refits (seeds 1 to 4), averaged over the refits. A label is marked provisional when this value is below 0.3. `code/topic_robustness.py` computes the stability, the share of posts that keep their topic under reseeding, Table 11 in every refit and the rank of each topic by stated non-understanding in every refit.

## 7. Stated non-understanding

A post is flagged when its author states explicitly that they do not understand something, for example "I don't understand why…" or "I am not sure how…". The marker list is in `code/non_understanding_detector.py`.

- Only first-person statements count. "The documentation is unclear" is not counted.
- An aim does not count. "I am trying to understand X" is not counted.
- Asking a question is not enough on its own.
- Statements of understanding and reported speech ("he said he was confused") are not counted.

Against the 200 posts in `validation/non_understanding_coded_200.csv`, whose labels were drafted by the LLM and reviewed by the first author, the marker list has a precision of 0.86 and a recall of 0.84.

The keyword-defined check of the surface-code and decoding result counts an integrity post as surface-code or decoding work if its title or body, in lower case, contains any of: surface code, detector error model, threshold, decoding, decode, logical error rate (substring match). It does not use the topic model and matches 428 integrity posts, 109 of which state non-understanding (`code/decoding_check.py`).

## 8. Tools and algorithms

Tool and algorithm names are matched as whole words in the title and body of each post, so that "stim" does not match "estimate". A post that names two tools is counted for each. Mentions of the Shor code, Shor's nine-qubit code and the Shor-Preskill proof are not counted as Shor's algorithm.

| Tool | Names matched |
|---|---|
| Qiskit | qiskit |
| Stim | stim |
| Cirq | cirq |
| PennyLane | pennylane |
| QuTiP | qutip |
| liboqs | liboqs |
| Open Quantum Safe | open quantum safe, oqs-provider, oqs |
| OpenSSL | openssl |
| OpenSSH | openssh |
| GnuPG | gpg, gnupg |
| strongSwan | strongswan |
| Bouncy Castle | bouncy castle |
| PQClean | pqclean |
| SimulaQron | simulaqron |
| QuNetSim | qunetsim |
| NetSquid | netsquid |
| PyQuil | pyquil |
| ProjectQ | projectq |
| Q# / QDK | q#, qdk, quantum development kit |
| Qulacs | qulacs |
| Quimb | quimb |
| Braket | braket |
| OpenQASM | openqasm |
