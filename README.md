# NBA Best Ball V2.9 — Network-Enabled Source Acquisition Alternatives

**Research-only portable runner, October 14, 2026.** The supplied `source_custody.py`, `qualification.py`, and `test_source_gates.py` are byte-for-byte copies from the saved R9-S19A archive. The original R9-S19A and S19B ZIPs are included unmodified for provenance. No historical V2.8 production files are modified.

## Route A: GitHub Actions — best for repeatable batches

1. Create a **new PRIVATE** GitHub repository, e.g. `nba-bestball-v29-research`. The connected GitHub integration currently does not expose an existing repository, and it has no repository-creation action. Creating a repository must be done by the user on GitHub.
2. Upload the **contents** of this folder to the private repository, preserving the `.github/workflows/nba-original-source-capture.yml` path and root-level Python scripts. Using `git` from a computer is the simplest way to preserve hidden `.github` paths.
3. Navigate to **Actions → NBA V2.9 R9-S19A direct source capture → Run workflow**. Choose `smoke`. No bulk acquisition is triggered automatically.
4. Inspect source receipts and errors in the uploaded job artifact. Three smoke attempts target the 2024 schedule, 2025 schedule, and game `0022501208`. If an origin blocks traffic or responds with a non-200, the job fails and artifacts still upload.
5. Only after passing smoke tests, choose `batch`, `start_index=0`, `count=25`. To collect other slices, use non-overlapping indices across `0..2461`, max `100` each. GitHub runners are stateless; **download every run's artifact**. Each batch's raw body+receipt is independently preserved as a temporary artifact; no job is claimed to persist from previous runs. When importing batches into a durable store, deduplicate by URL/native ID and SHA; never overwrite mismatches.
6. **Important:** GitHub artifacts expire. Move original bytes and headers to durable, access-controlled storage quickly; GitHub artifacts and ordinary SHA hashes are NOT third-party timestamps or WORM retention.

Captured metadata includes original URL, final URL, status, all response headers, self-observed UTC begin/end, size and SHA-256. Requests are direct HTTP from the runner. The wrapper preserves original S19A implementation and independently checks redirect host before counting a successful local receipt. It does not claim an independent timestamp witness.

## Route B: Google Colab — best for fastest initial execution

1. Open [colab.research.google.com](https://colab.research.google.com/), choose **Upload notebook**, upload `NBA_V29_S19A_COLAB_RUNNER_20261014.ipynb` from this bundle.
2. Run each cell **manually**, granting Google Drive access only if you want persistent output in Drive.
3. Upload this entire runner bundle ZIP using the notebook upload prompt, run local tests, then manually execute the three-request smoke test.
4. If HTTP origin access works, manually run additional conservative batches, writing outputs to your own Google Drive folder.
5. Google Colab access, VM lifetime and Drive operations can be limited. Keep independent backup copies and retain the original source response receipts.

## Qualification / DO NOT PROMOTE

- Schedule inventory: 2,462 URLs = 2 official schedules + 2,460 game boxscores.
- Original-byte target count remains zero until **this runner actually succeeds on a network-enabled executor**.
- Original NBA PDF injury snapshots, effective contract/roster intervals, G League assignments/recalls and pretip publication times are separate unfinished evidence classes.
- **NOT_ELIGIBLE**, **ELIGIBLE_NONAPPEARANCE**, **APPEARED**, **UNKNOWN** remain separate labels with admission gates enforced by `qualification.py`.
- A boxscore omission is not a zero or an injury; `ACTIVE/played=0` is not an appearance.
- Historical 835-row and 1,050-row samples cannot be merged without native-ID overlap reconciliation.
- V2.8-DRAFTOPS-FINAL-1.0 remains frozen (SHA-256 `099f46c1c5f64d9d82ea35867601b0d654cead3b0a50c532c734f42de1c3d07f`). No V2.9 fit/calibration/MEAIR/MEAA promotion is authorized by this execution infrastructure.

## Engineering validation

This package includes unchanged S19A tests plus six new wrapper tests; they can be run without network access. A successful local unit test does not establish live source retrieval or historical predictive accuracy.
