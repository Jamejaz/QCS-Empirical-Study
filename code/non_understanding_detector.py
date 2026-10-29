"""Detection of explicitly stated non-understanding ("confusion") in QCS posts.

Construct
---------
The detector measures a directly observable act: the author explicitly saying that they do not
understand something, the construct Ebert et al. (2019) use for confusion in code review. It is a
list of first-person markers applied with word boundaries to the post text; its precision and recall
are measured against the 200 manually coded posts (validation/non_understanding_coded_200.csv).

Design decisions, stated so that they can be checked:
  * FIRST PERSON ONLY. "I do not understand" counts; "the documentation is unclear" does not, because
    the latter is a statement about an artefact, not about the author's state.
  * A MARKER MUST BE EPISTEMIC, not a goal. "I am trying to understand X" is an aim and is excluded;
    "I do not understand X" and "I am not sure how" are confessions and are included.
  * QUESTIONS ALONE DO NOT COUNT. Every post on these platforms is a question; treating the question
    itself as confusion would make the measure vacuous.
  * NEGATED AND REPORTED USES ARE EXCLUDED: "I understand X well", "he said he was confused".
"""
import re

# --- first-person epistemic markers -------------------------------------------------------------
I = r"(?:i|we)"
BE = r"(?:'m|\s+am|\s+are|\s+was|\s+were)"
# intensity/hedge words that may sit between the verb and the epistemic word
DEG = r"(?:really|quite|very|a\s+bit|a\s+little|rather|somewhat|slightly|still|totally|completely|fully|kind\s+of|sort\s+of)"

MARKERS = [
    # explicit non-understanding
    rf"\b{I}\s+(?:do\s*n[o']?t|don't|cannot|can'?t|could\s*n[o']?t)\s+(?:really\s+|quite\s+|fully\s+|well\s+)?"
    r"(?:understand|get|see|follow|grasp|figure\s+out|work\s+out|make\s+sense\s+of|comprehend|tell)\b",
    rf"\b{I}\s+(?:did\s*n[o']?t|didn't)\s+(?:really\s+|quite\s+|fully\s+)?(?:understand|get|follow|see)\b",
    rf"\b{I}\s+fail\s+to\s+(?:understand|see|grasp)\b",
    # stated uncertainty about one's own knowledge
    rf"\b{I}{BE}\s+(?:not|un)\s*sure\b",
    rf"\b{I}{BE}\s+(?:{DEG}\s+)?(?:confused|puzzled|lost|baffled|unclear)\b",
    rf"\bwhat\s+{I}\s+(?:do\s*n[o']?t|don't)\s+(?:get|understand|see)\b",
    rf"\b(?:but|and|however)\s+(?:{I}\s+)?(?:do\s*n[o']?t|don't|can'?t|cannot)\s+(?:{DEG}\s+)?"
    r"(?:understand|get|see|follow|grasp|figure\s+out)\b",
    rf"\b(?:has|have|is|are|been)\s+(?:somewhat\s+|rather\s+|quite\s+)?(?:perplexing|confusing|puzzling|baffling)\s+(?:to\s+)?(?:me|us)\b",
    rf"\b{I}\s+have\s+(?:a\s+couple\s+of\s+|some\s+|a\s+few\s+|several\s+)?doubts?\b",
    rf"\bnot\s+(?:very\s+|entirely\s+|completely\s+|totally\s+)?clear\s+to\s+(?:me|us)\b",
    rf"\b{I}\s+(?:can'?t|cannot|could\s+not|couldn'?t)\s+understand\b",
    rf"\b{I}\s+have\s+(?:no|little)\s+(?:idea|clue)\b",
    rf"\bno\s+idea\s+(?:how|why|what|whether|if|where)\b",
    rf"\bmy\s+(?:confusion|doubt|doubts|misunderstanding)\b",
    rf"\b{I}\s+have\s+(?:a\s+)?(?:doubt|doubts|difficulty|difficulties|trouble|problems?\s+understanding)\b",
    rf"\b{I}\s+have\s+(?:a\s+)?(?:really\s+)?hard\s+time\s+understanding\b",
    rf"\b{I}{BE}\s+(?:struggling|having\s+trouble|having\s+difficult\w*)\s+(?:to|with|understanding)\b",
    rf"\b{I}\s+(?:seem|appear)\s+to\s+(?:be\s+)?miss\w*\b",
    rf"\bam\s+{I}?\s*missing\s+something\b",
    rf"\bwhat\s+am\s+i\s+missing\b",
    rf"\b{I}{BE}\s+not\s+(?:sure|clear|certain)\s+(?:how|why|what|whether|if|where)\b",
    rf"\b{I}\s+(?:can'?t|cannot)\s+wrap\s+my\s+head\b",
    rf"\bthis\s+(?:is\s+)?confus\w+\s+me\b",
    rf"\b{I}{BE}\s+unclear\s+(?:on|about|how|why|what)\b",
    rf"\b{I}\s+don'?t\s+know\s+(?:how|why|what|which|whether|where)\b",
    rf"\b{I}\s+do\s+not\s+know\s+(?:how|why|what|which|whether|where)\b",
]

# --- exclusions: goals, positives, and statements about artefacts rather than the author ----------
EXCLUDE = [
    rf"\b{I}\s+(?:am\s+)?tr(?:y|ie)\w*\s+to\s+understand\b",   # a goal, not a confession
    rf"\b{I}\s+(?:would\s+like|want|wish|hope)\s+to\s+understand\b",
    rf"\b{I}\s+understand\s+(?:this|that|the|it|how|why)\s+\w+\s+(?:well|clearly|fine)\b",
]

MARKER_RE = re.compile("|".join(f"(?:{p})" for p in MARKERS), re.I)
EXCL_RE = re.compile("|".join(f"(?:{p})" for p in EXCLUDE), re.I)


def detect(text):
    """Return (bool has_confusion, list of the matched marker strings)."""
    t = re.sub(r"\s+", " ", str(text))
    spans = [m.group(0) for m in MARKER_RE.finditer(t)]
    if not spans:
        return False, []
    # drop a match that is wholly inside an excluded construction
    kept = [s for s in spans if not EXCL_RE.fullmatch(s.strip())]
    return bool(kept), kept
