# Replication package: Quantum Computing Security Discussions on Practitioner Platforms

Data, labels, validation records, code and figures for the revised EMSE manuscript *Exploring Quantum Computing Security Discussions on Practitioner Platforms: A KDD-Based Empirical Study with a Validated Relevance Filter*.

## Dataset at a glance

| Step | Posts |
|---|---:|
| Retrieved from QCSE, SO, GitHub, Reddit, MSE and SES (5 February 2025) | 15,353 |
| Retained by the second-stage keyword filter | 5,163 |
| Core security, each post verified by a human coder | 289 |
| Integrity of computation | 1,624 |
| Development context or out of scope | 3,247 |
| Off-platform URLs removed | 3 |
| **Validated dataset analysed in the paper** | **1,913** |

## Files

| File | Content | Paper |
|---|---|---|
| `data/QCS_dataset_5163.csv` | The 5,163 retained posts: post ID, platform, date, URL, title, body, answers, views and votes | Sec. 4.1.2 |
| `data/QCS_labels_5163.csv` | The labels of each post: layer, keyword-rule labels, topic, challenge category and stated non-understanding | Sec. 4, 5 |
| `coding_rules.md` | All coding rules in one file: retrieval query and keyword list, layer codebook, keyword layer rules, both challenge codebooks, topic labelling, non-understanding markers, tool matching | Sec. 4.1 |
| `validation/rule_validation_sample_360.csv` | Stratified sample of 360 posts labelled by two coders, with the label of the first version of the rules and the agreed or adjudicated final label | Sec. 4.1.4, Table 3 |
| `validation/core_security_manual_check_486.csv` | Every post nominated as core security by either version of the rules, and whether it was confirmed by manual checking | Sec. 4.1.4, Table 3 |
| `validation/blind_recheck_100.csv` | 100 of those posts labelled again from the post text alone, without seeing any label, next to the final label | Sec. 4.1.4, Table 3 |
| `validation/integrity_holdout_sample_150.csv` | Fresh sample of 150 posts not used to refine the rules, labelled by two coders, with the label of the final rules and the agreed or adjudicated final label | Sec. 4.1.4, Table 3 |
| `validation/non_understanding_coded_200.csv` | 200 posts coded manually for stated non-understanding | Sec. 4.1.5 |
| `challenges/core_security_challenge_coding_289.csv` | Labels of the three coders and the settled category of every core-security post | Sec. 4.1.5, 5.5 |
| `challenges/integrity_challenge_validation_300.csv` | 300-post validation of the integrity challenge labels by two coders | Sec. 4.1.5, 5.5 |
| `topics/topics_core_security.csv`, `topics/topics_integrity.csv` | Seven topics per layer with posts, top-15 words and stability | Tables 6, 7 |
| `topics/coherence_by_k.csv` | Mean c_v coherence over five seeds for each number of topics | Fig. 4 |
| `results/results.json` | Every number reported in the paper, including the tests behind Tables 11 and 12 | Sec. 5 |
| `code/` | Layer rules (first and final version), text cleaning, LDA, non-understanding detector, RQ5 integration, results script | |
| `figures/` | Figures of the paper | |

## Labels

* Layers: core security, integrity, development context, out of scope. The `layer` column of `QCS_labels_5163.csv` is the final layer used in the paper.
* `first_rule_label` and `final_rule_label` are the layers assigned by the first and the final version of the keyword rules.
* Challenge categories and topics are given by name; definitions are in `coding_rules.md`. Posts outside the two analysed layers are marked "not analysed (excluded post)".
* In the coding files, `settled_by` and `agreement` record how each final label was reached: coders agreed, one coder (posts assigned to a single coder), tie resolved by codebook rule (the subject category takes precedence over the residual category), or decided by adjudication. The counts match Section 4.1.5 of the paper.
* `answers` and `views` are `n/a` where the platform does not provide them (GitHub and Reddit); views are given as displayed by the platform.

## Conventions

* Tool and algorithm names are matched on word boundaries on the raw post text.
* Mentions of the Shor code, Shor's nine-qubit code and the Shor-Preskill proof are not counted as Shor's algorithm.
* RQ5 relations are reported as rate, lift over the layer and Benjamini-Hochberg adjusted p.
* Sampling uses fixed seeds (2026).

## Post text

Titles and bodies are given as retrieved from the platforms. Posts are joined across all files of this package on `post_id`.

## Known duplicates

The GitHub scraper collected 29 discussion threads twice, with the same URL and nearly identical text. Two of the duplicates fall in the core-security layer and four in the integrity layer; the rest are excluded posts. They are retained as retrieved, and removing them changes no ranking and no reported proportion by more than one percentage point.

## Earlier version

The files of the originally submitted version are available in release v1.0 of this repository.
