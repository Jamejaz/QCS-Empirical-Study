# Coding rules

All rules used to build and label the dataset, in one place. The executable versions are in `code/`.

## 1. Retrieval and keyword filtering
### 1.1 Platforms

Data were collected from six practitioner platforms:

| Platform | Posts retrieved | Posts retained |
|---|---:|---:|
| Quantum Computing Stack Exchange (QCSE) | 11,987 | 4,408 |
| Math Stack Exchange (MSE) | 685 | 99 |
| Stack Exchange Security (SES) | 94 | 59 |
| Stack Overflow (SO) | 446 | 131 |
| Reddit | 1,027 | 106 |
| GitHub | 1,114 | 360 |
| **Total** | **15,353** | **5,163** |

GitHub items are issue threads and release discussions, counted as posts. The dataset was retrieved on 5 February 2025.

### 1.2 Stage 1: retrieval query

The first stage was designed for broad retrieval rather than security classification. The following query was applied to each platform:

```
(Quantum) AND (Computing OR Computing Security OR Post Quantum Computing OR Crypto
OR Information OR Algorithm OR Gates OR Error OR encryption) OR (Qiskit)
```

Extraction techniques:

- Reddit: API-based retrieval with the PRAW library.
- Stack Overflow and the Stack Exchange sites: HTML scraping with BeautifulSoup.
- GitHub: dynamic scraping of issue and discussion pages with Selenium WebDriver.

### 1.3 Stage 2: keyword filter (45 terms)

A post was retained only if its text contained the term "quantum" (in any form) and at least one of the following 45 terms.

**Error correction and fault tolerance (23):**
error correction, surface code, steane code, shor code, toric code, color code, quantum parity check, syndrome measurement, stabilizer, fault tolerant, magic state distillation, state injection model, zero noise extrapolation, probabilistic error cancellation, measurement error mitigation, randomised benchmarking, depolarizing channel, decoherence, dynamical decoupling, cross talk, qubit leakage, quantum gate calibration, lattice structure

**Cryptography and key distribution (9):**
quantum key distribution, qkd, bb84, e91, ntru, rainbow, homomorphic encryption, encryption, quantum shielding

**Quantum information (4):**
no cloning theorem, quantum teleportation, bell test, entanglement purification

**Tools and algorithms (3):**
cirq, stim, vqe

**Short forms also matched (6):**
noise, error, surface, steane, shor, toric

### 1.4 Matching convention

The Stage 2 list was applied as a **substring test**, not on word boundaries. The short forms therefore also matched inside other words. For example, *shor* matches *short*, *stim* matches *estimate*, and *surface* matches text about surfaces of any kind. Re-running the list over the stored post text with word boundaries retains roughly four fifths of the corpus, so the substring convention widened the second stage appreciably.

All analyses in the paper (tool and algorithm counts, topics, challenges, non-understanding) use word-boundary matching, and they are run on the validated layers rather than on the output of this filter.

### 1.5 Why this matters for the results

The list is weighted towards error correction and noise, which is the vocabulary of the integrity layer, while core-security terms are the smaller part of it. Together with the substring convention, this explains why only 289 of the 5,163 retained posts are core security (5.6%). The filter that built the corpus was broader than the subject of the study. This is why every retained post was classified into a layer and the classification was validated before analysis (Section 4.1.4 of the paper). The convention affects which posts were available to classify, not how any of them was classified.

The retrieval also used tool names among its terms. A post naming Qiskit or Stim therefore had a better chance of entering the pool than an otherwise identical post naming neither. The tool counts reported in the paper should be read with this in mind (Section 7, Threats to Validity).

## 2. Layer definitions and manual labelling codebook

Every post is assigned to exactly one layer. The same codebook was used by every coder who labelled layers by hand.

- Question to answer for each post: What is the PRIMARY concern of the person asking?
- L1 — Core security | The post is about protecting confidentiality, integrity or authenticity against an adversary, or about cryptography affected by quantum computing. | Includes: Shor/Grover threat to RSA, ECC, AES, key sizes; post-quantum cryptography (Kyber/ML-KEM, Dilithium, NTRU, McEliece, SPHINCS+), PQC libraries and migration; QKD/BB84/E91 and quantum cryptographic protocols; attacks on quantum systems (side-channel, fault injection, trojans, multi-tenant/crosstalk attacks, cloud privacy); blind/verifiable delegated computation; quantum randomness for security; authentication/signatures. | Example: 'How long until quantum computers can decrypt RSA using Shor?' / 'How to show BB84 is safe against imperfect cloning?'
- L2 — Integrity & reliability | The post is about whether a quantum computation stays correct despite NON-adversarial faults. | Includes: quantum error correction, stabilizer/surface/color codes, logical qubits, fault tolerance, decoders, decoherence, noise models and channels, error mitigation, calibration, gate/readout fidelity, verifying outputs. | Example: 'How to initialize logical qubit stabilizer states fault-tolerantly?' / 'How to change the noise properties of a Qiskit noise model?'
- L3 — Development context | Quantum computing topic, but the primary concern is neither security nor integrity. | Includes: how-to programming, installation/dependency errors, SDK/API usage, plotting/visualisation, algorithms used for chemistry/optimisation/ML without a security or correctness-under-noise angle, general theory and maths. | Example: 'Plotting Bloch sphere in QuTiP' / 'Quantum Device Error, Device qiskit does not exist'
- L0 — Out of scope | Not about quantum computing, spam, news link without discussion, empty or unreadable.
- Decision rules
- R1 | Code the PRIMARY concern, not every word mentioned. A passing mention of 'secure' or 'noise' does not make a post L1/L2.
- R2 | If a post is genuinely about both security and integrity, choose L1.
- R3 | Shor/Grover/QFT posts: L1 only if the cryptographic implication is part of the question (e.g., breaking RSA, key length). Pure circuit/implementation of Shor for factoring 15 = L3.
- R4 | Noise/QEC in an attack context (e.g., fault injection, crosstalk attack) = L1.
- R5 | If you cannot decide after reading the full post (open the URL), choose your best label and set Confidence = 'unsure'.
- R6 | Security work that hits a tooling/implementation problem stays L1 (e.g., build error in liboqs/oqs-provider, import error while coding BB84 or E91). The security task defines the layer.
- R7 | Classical cryptography with NO link to quantum computing in the post (e.g., RSA key generation code, a disk-encryption app bug) = L0.
- R8 | 'Quantum' used in an unrelated sense (ImageMagick Quantum type, round-robin time quantum, a variable named send_quantum) = L0.
- R9 | Classical cryptography: L1 only if the post asks about security IN LIGHT OF quantum computing (e.g., 'is RSA-2048 safe against quantum computers?', 'which key size is quantum-safe?'). If quantum is only a side remark or explicitly excluded, code L0 (see R7).
- Columns to fill: 'layer' (dropdown L0–L3), 'confidence' (sure/unsure), 'comment' (optional, especially when unsure).

## 3. Keyword rules that assign a layer (final version)

Implemented in `code/layer_rules_final.py`; the first version is `code/layer_rules_first_version.py`.

| Term list | Terms |
|---|---|
| Quantum context (required) | qubit*, quantum, qiskit, cirq, qkd, shor, grover, qpu, nisq, ibmq?, stim, pennylane, qutip |
| Core security, strong evidence | qkd, bb84, e91, b92, quantum key distribution, key distribution, post quantum, pqc, quantum safe, quantum resistant, kyber, ml kem, dilithium, ml dsa, sphincs, mceliece, ntru, liboqs, oqs provider, pqclean, open quantum safe, eavesdrop*, cryptanaly*, side channel, fault injection, trojan, quantum money, blind quantum, delegated quantum, verifiable quantum, one time pad, quantum cryptograph*, harvest now |
| Core security, context terms | crypt*, encrypt*, decrypt*, cipher*, rsa, aes, elliptic curve, ecdsa, ecdh, diffie, digital signature*, authenticat*, key (length/size), attack*, adversar*, secure, security, insecure, vulnerab*, brute force, confidential*, privacy, tamper*, malicious, threat* |
| Core security exclusions | parameteri[sz]ed quantum circuit, pqc(?=[^.]{0,80}(keras/tensorflow/pennylane/vqc/agent)), time quantum, send_quantum, firefox quantum, imagemagick |
| Integrity, strong evidence | error correct*, qec, surface code*, color code*, toric code, steane, shor code, repetition code, stabili[sz]er*, fault toleran*, logical qubit*, syndrome*, decoder*, decoding, mwpm, bposd, decoher*, dephas*, error mitigation, zero noise extrapolation, magic state*, distillation, threshold theorem, lattice surgery, transversal, kraus, depolari[sz]*, amplitude damping, crosstalk, readout error*, noise model*, noise channel*, t1, t2, coherence time*, randomi[sz]ed benchmarking, quantum channel* |
| Integrity, weak evidence | noise, noisy, error rate*, fidelity, calibrat*, bit flip, phase flip, leakage |
| Error-message text masked before integrity matching | error message, traceback, raise[sd]? an? error, getting an? error, error:, errors? (while/when) (running/simulating/importing/installing), \w+Error, throws? an? error, an error occur* |

Decision order for each post:

1. Not one of the six platforms, shorter than 30 characters, or no quantum-context term: out of scope.
2. A core-security exclusion and no strong security term: development context.
3. At least one strong security term, or security context terms that are prominent (in the title and repeated, or three or more): core security.
4. After masking error-message text: an integrity term in the title, two strong integrity terms, or one strong and one weak: integrity.
5. Otherwise: development context.

The names of quantum frameworks (Qiskit, Cirq, Stim, PennyLane, QuTiP) only establish quantum context and do not decide a layer. The names of the post-quantum libraries liboqs, Open Quantum Safe and PQClean count as core-security evidence.

## 4. Core-security challenge codebook

| Category | Definition |
|---|---|
| Quantum communication and QKD | Difficulties with the security of key distribution protocols, eavesdropping strategies and their effect, QKD in practice. |
| Information sought, no obstacle reported | The post asks for an explanation, an overview or literature without reporting a specific problem. |
| Tooling and implementation | Practical use of cryptographic libraries and protocols in software, including post-quantum support in existing tools, build and configuration problems. |
| Cryptographic transition and post-quantum threats | Whether deployed schemes remain secure, and how and when to migrate. |
| Algorithm and protocol design | Design and security analysis of quantum protocols and attacks, including security proofs. |
| Conceptual and knowledge gaps (residual) | A misunderstanding of a basic concept with no more specific subject. Any subject category takes precedence. |
| Attacks on quantum systems | Attacks on quantum hardware or cloud quantum services: fault injection, side channels, crosstalk. |

Rules: one label per post; a post that reports no obstacle has its own category; the residual category applies only when no subject category fits.

## 5. Integrity challenge codebook

```
INTEGRITY-LAYER CHALLENGE CODEBOOK v1.1 (pilot-reviewed)
Assign ONE label per post: the main difficulty the author reports.

I0 No difficulty reported. Release notes, announcements, contributor wishlists, requests for literature, a review or an overview. Not for a question about a specific concept or task, even a short one.
I1 Code construction and properties. Properties, construction, existence, equivalence, classification of codes: logical operators, bounds, parameters, degeneracy, stabilizer/destabilizer groups, centralizer/normalizer. INCLUDES the error-correcting capability of a NAMED code (e.g. can the Shor code correct X). General correctability of a channel goes to I4; generic "why does QEC work" goes to I7.
I2 Fault-tolerant logical operations. Computation on encoded qubits: transversal gates, code switching, magic states and distillation, lattice surgery, logical circuit compilation, combining logical computation with QEC. The main issue must concern encoded computation or a fault-tolerant operation. Naming a software package (Qiskit, Stim) does NOT move the post to I6.
I3 Decoding, thresholds and logical error rates. Decoders and their behaviour, threshold estimation, memory experiments, logical error rates, reproducing or interpreting such results. Stays I3 even when a simulator is used. Use I6 only for an identified API/tool limitation.
I4 Noise channels and their mathematics. Channels and their action on states, correctability of a channel, twirling, distances between noisy and noiseless states, decoherence formalism, mixed-state descriptions of noise and why density matrices are needed. A simulator mentioned only as context does not make a theoretical question I6.
I5 Hardware noise: characterisation, mitigation, noise-aware design. Real or near-term device noise: T1/T2, fidelity, randomized benchmarking (including benchmarking theory when tied to characterisation), error mitigation (ZNE, PEC, DD), noise-aware circuit or backend choice, interpreting device error metrics. A question about retrieving a quantity through an API is I6.
I6 Simulators and QEC software. Requires a concrete tool capability, implementation, API use, error message or performance issue (Qiskit, Aer, Stim, PyMatching, Cirq, QuantumClifford, QuTiP, frameworks). Theoretical questions about noise representation are I4.
I7 Conceptual foundations (RESIDUAL). Apply only after excluding I1-I6. Why QEC works in general, notation, definitions, the name or general use of a technique, where a technique fits in the field. If a subject category fits, it wins. Broad application questions with no integrity difficulty also land here; set flag=scope for them.

Rules: (1) one label, the main difficulty; (2) I7 residual, subject wins; (3) I0 only when no difficulty and no specific concept/task is asked; (4) if nothing fits, label NEW and describe it.

```

## 6. Topic labels

Each layer is modelled separately with LDA (k = 7, five seeds). Two authors assigned each topic label independently from its fifteen highest-weighted words and its representative posts, and resolved disagreements by discussion. A label is marked provisional when the mean Jaccard overlap of the topic's top ten words across seeds is below 0.3.

## 7. Stated non-understanding

A post is flagged when its author explicitly states that they do not understand something. The marker list is in `code/non_understanding_detector.py`.

* FIRST PERSON ONLY. "I do not understand" counts; "the documentation is unclear" does not, because
    the latter is a statement about an artefact, not about the author's state.
  * A MARKER MUST BE EPISTEMIC, not a goal. "I am trying to understand X" is an aim and is excluded;
    "I do not understand X" and "I am not sure how" are confessions and are included.
  * QUESTIONS ALONE DO NOT COUNT. Every post on these platforms is a question; treating the question
    itself as confusion would make the measure vacuous.
  * NEGATED AND REPORTED USES ARE EXCLUDED: "I understand X well", "he said he was confused".

Accuracy against the 200 manually coded posts (`validation/non_understanding_coded_200.csv`): precision 0.86, recall 0.84.

## 8. Tool and algorithm matching

* Names are matched on word boundaries on the raw post text (title and body), so that, for example, "stim" does not match "estimate".
* A post naming two tools is counted once under each.
* Mentions of the Shor code, Shor's nine-qubit code and the Shor-Preskill proof are not counted as Shor's algorithm.

Tool dictionary:

| Tool | Patterns |
|---|---|
| Qiskit | qiskit |
| Stim | stim |
| Cirq | cirq |
| PennyLane | pennylane |
| QuTiP | qutip |
| liboqs | liboqs |
| PyQuil | pyquil |
| ProjectQ | projectq |
| QDK / Q# | qdk, q#, quantum development kit |
| Open Quantum Safe | open quantum safe, oqs[- ]provider, oqs |
| SimulaQron | simulaqron |
| Qulacs | qulacs |
| Quimb | quimb |
| Bouncy Castle | bouncy ?castle |
| PQClean | pqclean |
| QuNetSim | qunetsim |
| Braket | braket |
| OpenQASM | openqasm |
| NetSquid | netsquid |
| OpenSSL | openssl |
| GnuPG/GPG | gpg, gnupg |
| strongSwan | strongswan |
| OpenSSH | openssh |
