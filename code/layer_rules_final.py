"""Final layer rules, refined after the 360-post validation sample.
Changes vs v1: security terms must occur in a quantum context; strong vs weak evidence;
error-message text no longer counts as an integrity signal; explicit exclusions for known confusions."""
import re, ftfy

def rx(*pats): return re.compile("|".join(f"(?:{p})" for p in pats), re.I)

QUANTUM   = rx(r"\bqubit\w*", r"\bquantum\b", r"\bqiskit\b", r"\bcirq\b", r"\bqkd\b", r"\bshor\b", r"\bgrover\b",
               r"\bqpu\b", r"\bnisq\b", r"\bibmq?\b", r"\bstim\b", r"\bpennylane\b", r"\bqutip\b")
# --- Layer 1: confidentiality / authenticity ---------------------------------
SEC_STRONG = rx(r"\bqkd\b", r"bb84", r"\be91\b", r"\bb92\b", r"quantum key distribution", r"key distribution",
                r"post[- ]quantum", r"\bpqc\b", r"quantum[- ]safe", r"quantum[- ]resistant", r"kyber", r"ml[- ]kem",
                r"dilithium", r"ml[- ]dsa", r"sphincs", r"mceliece", r"\bntru\b", r"liboqs", r"oqs[- ]provider",
                r"pqclean", r"open quantum safe", r"eavesdrop\w*", r"cryptanaly\w*", r"side[- ]channel",
                r"fault injection", r"trojan", r"quantum money", r"blind quantum", r"delegated quantum",
                r"verifiable quantum", r"one[- ]time pad", r"quantum cryptograph\w*", r"harvest now")
SEC_CTX    = rx(r"crypt\w*", r"encrypt\w*", r"decrypt\w*", r"cipher\w*", r"\brsa\b", r"\baes\b", r"elliptic curve",
                r"\becdsa\b", r"\becdh\b", r"diffie", r"digital signature\w*", r"authenticat\w*", r"key (?:length|size)",
                r"\battack\w*", r"adversar\w*", r"\bsecure\b", r"\bsecurity\b", r"insecure", r"vulnerab\w*",
                r"brute[- ]force", r"confidential\w*", r"\bprivacy\b", r"tamper\w*", r"malicious", r"\bthreat\w*")
L1_EXCL    = rx(r"parameteri[sz]ed quantum circuit", r"\bpqc\b(?=[^.]{0,80}(?:keras|tensorflow|pennylane|vqc|agent))",
                r"time quantum", r"send_quantum", r"firefox quantum", r"imagemagick")
# --- Layer 2: integrity of computation ---------------------------------------
INT_STRONG = rx(r"error[- ]correct\w*", r"\bqec\b", r"surface code\w*", r"color code\w*", r"toric code", r"steane",
                r"shor code", r"repetition code", r"stabili[sz]er\w*", r"fault[- ]toleran\w*", r"logical qubit\w*",
                r"syndrome\w*", r"decoder\w*", r"\bdecoding\b", r"\bmwpm\b", r"\bbposd\b", r"decoher\w*", r"dephas\w*",
                r"error mitigation", r"zero[- ]noise extrapolation", r"magic state\w*", r"distillation",
                r"threshold theorem", r"lattice surgery", r"transversal", r"kraus", r"depolari[sz]\w*",
                r"amplitude damping", r"crosstalk", r"readout error\w*", r"noise model\w*", r"noise channel\w*",
                r"\bt1\b", r"\bt2\b", r"coherence time\w*", r"randomi[sz]ed benchmarking", r"quantum channel\w*")
INT_WEAK   = rx(r"\bnoise\b", r"\bnoisy\b", r"error rate\w*", r"\bfidelity\b", r"calibrat\w*", r"\bbit[- ]flip\b",
                r"phase[- ]flip", r"\bleakage\b")
ERRMSG     = rx(r"error message", r"traceback", r"raise[sd]? an? error", r"getting an? error", r"\berror:",
                r"errors?\s+(?:while|when)\s+(?:running|simulating|importing|installing)", r"\w+Error\b",
                r"throws? an? error", r"an error occur\w*")

BOILER = re.compile(r"\((?:/posts|/users|/questions/tagged|/q/|#|https?://i\.sstatic)[^)]*\)")

def clean(title, body):
    t = ftfy.fix_text(f"{title if title == title else ''}\n{body}")
    return re.sub(r"\s+", " ", BOILER.sub(" ", t))

def classify(title, body, platform):
    if platform not in {"QCSE", "SO", "GitHub", "Reddit", "MSE", "SES"}:
        return "L0"
    title = "" if title != title else str(title)
    text = clean(title, body)
    if len(text) < 30 or not QUANTUM.search(text):
        return "L0"
    if L1_EXCL.search(text) and not SEC_STRONG.search(text):
        return "L3"
    head = clean(title, "")[:300]
    # Layer 1: strong security evidence, or security context terms that are prominent (title / repeated)
    s_strong = len(SEC_STRONG.findall(text)); s_ctx = len(SEC_CTX.findall(text))
    if s_strong >= 1 or SEC_CTX.search(head) and s_ctx >= 2 or s_ctx >= 3:
        return "L1"
    # Layer 2: integrity, ignoring error-message noise
    masked = ERRMSG.sub(" ", text)
    i_strong = len(INT_STRONG.findall(masked)); i_weak = len(INT_WEAK.findall(masked))
    if INT_STRONG.search(head) or i_strong >= 2 or (i_strong >= 1 and i_weak >= 1) or (INT_WEAK.search(head) and i_weak >= 2):
        return "L2"
    if s_ctx >= 1 and s_strong == 0 and SEC_CTX.search(head):
        return "L1"
    return "L3"
