"""Rule-based first-pass labelling of the 5,163 posts into QCS layers.
L1 Core security | L2 Integrity & reliability | L3 Development context | L0 Out of scope.
This is ONLY a first pass; the validated labels come from the two human coders."""
import re, pandas as pd

PLATFORMS = {"quantumcomputing.stackexchange.com": "QCSE", "stackoverflow.com": "SO", "github.com": "GitHub",
             "reddit.com": "Reddit", "math.stackexchange.com": "MSE", "security.stackexchange.com": "SES"}

L1 = [r"crypt\w*", r"encrypt\w*", r"decrypt\w*", r"cipher\w*", r"secur\w*", r"insecur\w*", r"attack\w*",
      r"attacker\w*", r"vulnerab\w*", r"adversar\w*", r"eavesdrop\w*", r"\bqkd\b", r"bb84", r"\be91\b", r"b92",
      r"key distribution", r"key exchange", r"key agreement", r"post[- ]quantum", r"\bpqc\b", r"quantum[- ]safe",
      r"quantum[- ]resistant", r"kyber", r"ml-kem", r"dilithium", r"ml-dsa", r"falcon signature", r"sphincs",
      r"mceliece", r"\bntru\b", r"lattice[- ]based", r"\brsa\b", r"elliptic curve", r"\becdsa\b", r"\becdh\b",
      r"diffie", r"\baes\b", r"sha-?256", r"side[- ]channel", r"fault injection", r"trojan", r"tamper\w*",
      r"malicious", r"threat\w*", r"privacy", r"confidential\w*", r"authenticat\w*", r"digital signature\w*",
      r"blind quantum", r"delegated quantum", r"verifiable quantum", r"one[- ]time pad", r"no[- ]cloning",
      r"quantum money", r"\bqrng\b", r"random number generat\w*", r"break(?:ing)? (?:rsa|encryption|crypto)"]
L2 = [r"error[- ]correct\w*", r"\bqec\b", r"surface code\w*", r"stabili[sz]er code\w*", r"color code\w*",
      r"toric code", r"fault[- ]toleran\w*", r"logical qubit\w*", r"decoher\w*", r"dephas\w*", r"noise",
      r"noisy", r"error mitigation", r"error rate\w*", r"fidelity", r"syndrome\w*", r"decoder\w*", r"decoding",
      r"calibrat\w*", r"crosstalk", r"depolari[sz]\w*", r"amplitude damping", r"bit[- ]flip", r"phase[- ]flip",
      r"readout error\w*", r"\bt1\b", r"\bt2\b", r"threshold theorem", r"magic state\w*", r"distillation",
      r"kraus", r"leakage", r"verification of", r"benchmarking"]
RX1 = re.compile("|".join(f"(?:{p})" for p in L1), re.I)
RX2 = re.compile("|".join(f"(?:{p})" for p in L2), re.I)
BOILER = re.compile(r"\((?:/posts|/users|/questions/tagged|/q/|#|https?://i\.sstatic)[^)]*\)|Share|Improve this question|"
                    r"Follow|Add a comment|Code of Conduct|edited [A-Z][a-z]{2} \d+.*?at \d+:\d+|asked [A-Z][a-z]{2} \d+.*?at \d+:\d+")

def clean(t):
    t = BOILER.sub(" ", str(t))
    return re.sub(r"\s+", " ", t).strip()

def platform(url):
    m = re.search(r"https?://(?:www\.)?([^/]+)", str(url))
    return PLATFORMS.get(m.group(1) if m else "", "Other")

def label(row):
    if row.platform == "Other" or len(row.text) < 30:
        return "L0"
    title, text = str(row.question_title), row.text
    h1 = len(RX1.findall(text)); h2 = len(RX2.findall(text))
    if RX1.search(title) or h1 >= 2 or (h1 >= 1 and h2 == 0):
        return "L1"
    if RX2.search(title) or h2 >= 1:
        return "L2"
    return "L3"

def load(path):
    d = pd.read_csv(path)
    d["post_id"] = [f"P{i:05d}" for i in range(len(d))]
    d["platform"] = d.url.map(platform)
    d["text"] = (d.question_title.fillna("") + " || " + d.Question_body.fillna("").map(clean))
    d["auto_layer"] = d.apply(label, axis=1)
    return d
