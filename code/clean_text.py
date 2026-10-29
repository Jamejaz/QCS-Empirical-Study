"""Text cleaning for topic modelling.
Removes: platform boilerplate, comments by other users, tag blocks, URLs, LaTeX/MathJax, code lines and
code-like tokens, mojibake. Keeps: the asker's own title + question text. Tags are extracted separately."""
import re, ftfy

TAG_RX   = re.compile(r"\(/questions/tagged/([^)]+)\)")
CUT_RX   = re.compile(r"\n(?:Share \(/q/|\$\\begingroup\$|Improve this question|Add a comment|edited[A-Z][a-z]{2} \d)")
URL_RX   = re.compile(r"\(?https?://\S+\)?|www\.\S+|\S+\.(?:com|org|net|io|edu)/\S*")
LINK_RX  = re.compile(r"\((?:/posts|/users|/q/|/help|/questions|#)[^)]*\)")
MATH_RX  = [re.compile(p, re.S) for p in [r"\$\$.*?\$\$", r"\$[^$]{0,400}?\$", r"\\begin\{(\w+\*?)\}.*?\\end\{\1\}",
                                          r"\\\[.*?\\\]", r"\\\(.*?\\\)"]]
TEX_RX   = re.compile(r"\\[a-zA-Z]+(\{[^}]*\})?")
CODE_LINE= re.compile(r"^\s*(import |from \S+ import|def |class |return\b|print\(|#include|for .* in .*:|if .*:|\w+\s*=\s*\S|"
                      r"[\w.]+\(.*\)\s*$|OPENQASM|qreg |creg |>>>|\$ |pip install|Traceback|File \"|\w+Error:)")
CODE_TOK = re.compile(r"[=(){}\[\]<>;:`_/\\|@#*^~]|\w\.\w|\d")
STACK_BOILER = re.compile(r"\((?:/posts/\d+/timeline)\)|Closed.*?ago\.|Want to improve this question\?.*?post\.|"
                          r"This question (?:does not|is missing|is opinion-based).*?(?:\.|$)|\[closed\]|\[duplicate\]", re.S)

def split_body(body):
    body = ftfy.fix_text(str(body))
    tags = sorted(set(TAG_RX.findall(body)))
    m = CUT_RX.search(body)
    core = body[:m.start()] if m else body
    lines = [l for l in core.split("\n") if not TAG_RX.search(l)]
    # drop tag-name lines that precede '(/questions/tagged/...)' lines
    lines = [l for l in lines if l.strip() not in tags]
    return "\n".join(lines), tags

def clean(title, body):
    core, tags = split_body(body)
    txt = ftfy.fix_text(str(title) if title == title else "") + "\n" + core
    txt = STACK_BOILER.sub(" ", txt)
    txt = LINK_RX.sub(" ", txt); txt = URL_RX.sub(" ", txt)
    for rx in MATH_RX: txt = rx.sub(" ", txt)
    txt = TEX_RX.sub(" ", txt)
    kept = []
    for line in txt.split("\n"):
        if CODE_LINE.search(line): continue
        toks = [t.strip(".,;:!?()[]\"'") for t in line.split()]
        toks = [t for t in toks if t and not CODE_TOK.search(t)]
        kept.append(" ".join(toks))
    txt = " ".join(kept)
    txt = re.sub(r"\b(\w+)( \1\b)+", r"\1", txt)      # collapse duplicated inline words (scraping artefact)
    return re.sub(r"\s+", " ", txt).strip(), tags
