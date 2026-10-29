"""Builds the cleaned, lemmatised corpus for topic modelling and reports what each step removed."""
import pandas as pd, json, re, sys, collections, spacy
from gensim.models.phrases import Phrases, Phraser
from clean_text import clean
from spacy.lang.en.stop_words import STOP_WORDS

SRC = sys.argv[1] if len(sys.argv) > 1 else "Final_Data_File.csv"
P = {"quantumcomputing.stackexchange.com": "QCSE", "stackoverflow.com": "SO", "github.com": "GitHub",
     "reddit.com": "Reddit", "math.stackexchange.com": "MSE", "security.stackexchange.com": "SES"}

STOP = set(STOP_WORDS) | {
    # original extension (kept for comparability)
    'make','need','get','thing','good','well','go','work','way','think','know','say','take','use','find','help','give','put','keep',
    'see','seem','try','start','stop','want','like','ask','explain','time','post','begin','blog','paper','close','people','question',
    'answer','example','case','part','point','problem','solution','issue','idea','method','heard','user','comment','guy','follow',
    'topic','professor','lecture','actually','probably','maybe','really','already','just','kind','sort','basically','definitely',
    'obviously','literally','install',
    # platform / conversational
    'thank','thanks','hi','hello','please','anyone','someone','somebody','edit','update','also','would','could','should','may','might',
    'one','two','three','first','second','new','different','following','able','sure','much','many','lot','even','still','however',
    'understand','look','mean','read','write','show','run','call','come','let','tell','feel','happen','wonder','confused','clear',
    # programming leftovers
    'self','def','import','print','return','true','false','none','np','numpy','str','int','list','dict','file','line','code',
    'function','value','variable','output','input','result','version','error_message','traceback',
    'recent_call','call_last','tick','tick_tick','thank_advance','make_sense','like_know','let_say','file_line','line_line'}

def main():
    d = pd.read_csv(SRC)
    d["post_id"] = [f"P{i:05d}" for i in range(len(d))]
    d["platform"] = d.url.astype(str).str.extract(r"https?://(?:www\.)?([^/]+)")[0].map(P).fillna("Other")
    stats = collections.OrderedDict()
    raw_tok = d.question_title.fillna("").str.split().str.len() + d.Question_body.fillna("").str.split().str.len()
    stats["raw_whitespace_tokens"] = int(raw_tok.sum())
    cl = [clean(t, b) for t, b in zip(d.question_title, d.Question_body)]
    d["clean_text"] = [c[0] for c in cl]; d["tags"] = [";".join(c[1]) for c in cl]
    stats["after_boilerplate_math_code_removal"] = int(d.clean_text.str.split().str.len().sum())

    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    docs = []
    for doc in nlp.pipe(d.clean_text.str.lower(), batch_size=200):
        docs.append([t.lemma_ for t in doc if t.pos_ in {"NOUN", "PROPN", "ADJ", "VERB"} and t.is_alpha and len(t) > 2])
    stats["after_lemmatisation_pos_filter"] = sum(map(len, docs))
    bigram = Phraser(Phrases(docs, min_count=10, threshold=20))
    docs = [[w.replace("fouri_","fourier_") for w in bigram[x]] for x in docs]
    docs = [[w for w in x if w not in STOP] for x in docs]
    stats["after_stopwords"] = sum(map(len, docs))
    d["tokens"] = [json.dumps(x) for x in docs]
    keep = d.platform != "Other"
    stats["posts_total"] = len(d); stats["posts_excluded_other_domain"] = int((~keep).sum())
    stats["posts_empty_after_cleaning"] = int((d.tokens == "[]").sum())
    d.to_csv("corpus_clean.csv", index=False)
    json.dump(stats, open("cleaning_stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))
    phr = collections.Counter(w for x in docs for w in x if "_" in w)
    print("top bigrams:", phr.most_common(40))

if __name__ == "__main__":
    main()
