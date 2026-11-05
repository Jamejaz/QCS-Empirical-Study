"""Check that the post-quantum library names do not decide the core-security layer (Section 4.1.4).

Run from code/:  python3 library_names_check.py
The final rules are run once as published and once with the four library-name patterns
(liboqs, oqs-provider, pqclean, open quantum safe) removed from the strong core-security terms.
Reported: the core-security nomination of none of the 5,160 classified posts changes (351 nominations either way).
"""
import re
import pandas as pd
import layer_rules_final as R

LAYER = {'L1': 'core security', 'L2': 'integrity', 'L3': 'development context', 'L0': 'out of scope'}
d = pd.read_csv('../data/QCS_dataset_5163.csv')
d = d[d.platform.isin(['QCSE', 'SO', 'GitHub', 'Reddit', 'MSE', 'SES'])]  # the 5,160 posts the rules classify
with_lib = [LAYER[R.classify(t, b, p)] == 'core security' for t, b, p in zip(d.title, d.body, d.platform)]

LIB = ['liboqs', 'oqs[- ]provider', 'pqclean', 'open quantum safe']
pats = R.SEC_STRONG.pattern.split('|')
R.SEC_STRONG = re.compile('|'.join(p for p in pats if not any(l in p for l in LIB)), re.I)
without = [LAYER[R.classify(t, b, p)] == 'core security' for t, b, p in zip(d.title, d.body, d.platform)]

changed = sum(x != y for x, y in zip(with_lib, without))
print(f'{len(d)} posts; core-security nominations: {sum(with_lib)} with library names, {sum(without)} without; changed: {changed}')
