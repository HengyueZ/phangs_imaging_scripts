# PHANGS-CMZs Imaging Quality Assurance — Plan
 
> **This file is the single source of truth for the QA effort.**
> Decisions, owners, open questions and status live here — not in individual chats.
> If a chat (with a colleague or with Claude) produces a decision or change, update this file and commit it.
 
| | |
|---|---|
| **Last updated** | 2026-11-23 |
| **Upstream repo** | [akleroy/phangs_imaging_scripts](https://github.com/akleroy/phangs_imaging_scripts) |
| **Team fork** | [HengyueZ/phangs_imaging_scripts](https://github.com/HengyueZ/phangs_imaging_scripts) |
| **Integration branch** | `CMZ-QA` (development on `QA-build`; fork `master` mirrors upstream). See §3. |
| **Task tracker** | GitHub Project on the fork (Hengyue to set up) |
| **Lead** | Hengyue (QA infrastructure build) |
| **Target** | QA infrastructure ready by Christmas 2026; QA of individual galaxies starts in the New Year |
| **Existing QA code** | See §10 (inventory of Annie's and Daizhong's code) |
| **Task tracker** | _TBD — GitHub Project board on the fork_ |
| **Related documents** | `phangs_alma_qa_design_jakob.md`: first-pass design draft (input only, not decisions; it uses different check IDs and assumes PHANGS-ALMA scope; QA_PLAN.md supersedes it where they conflict) |
---
 
## 1. Purpose
 
Build a QA layer for the PHANGS imaging pipeline that, for every target and product:
 
1. **Detects** problems in the data and products (artefacts, poor convergence, beam/sensitivity issues, flux recovery, mask inconsistencies).
2. **Localises** them to the stage where the fix belongs — pre-imaging, imaging or products — because diagnostics mostly run *after* imaging/product creation, but the remedy depends on where the problem originates.
3. **Summarises** results in a machine-readable form so we can compare across the full sample.
This extends the existing QA scripts by Daizhong and Annie (external collaborators, see §2); it does not replace them.
 
### What a QA finding should lead to
 
| Origin of problem | Example remedy |
|---|---|
| **Pre-imaging** | Re-image TP if bandwidth is insufficient (and more is available); revise field selection |
| **Imaging** | Fix artefacts, adjust clean depth / masks / iteration limits, address non-convergence |
| **Products** | Revise masks (e.g. check PHANGS masks are consistent), adjust clipping in moment maps |
 
### Scope (to be confirmed)
- Development/validation target: NGC1097 (ALMA CMZ data).
- All QA runs on MPCDF.
 
Not yet written down. To be filled in:
- Which PHANGS-CMZs data: targets, lines, array configurations (incl. which 12m arrays are combined), TP yes/no.
- Which stages are in scope. In particular, whether **postprocessing** (PB correction, feathering with TP, round-beam convolution, mosaicking) gets QA. See §5.5.
- Which product versions / resolutions, and whether QA must also run on products that already exist (see A8).
---
 
## 2. People and roles
 
### Project members
 
| Person | Current responsibility |
|---|---|
| Jakob | Claude Project Setup; Field-of-view / pointing coverage plot (scratch version exists) |
| Hengyue | Leads the QA infrastructure build (porting Daizhong's code on `QA-build` → `CMZ-QA`); owns the fork (team access, GitHub Project); liaises with Annie & Daizhong |
| Jonny | _TBD_ |
| Francesco | _TBD_ |
| _TBD_ | Owners for individual checks; assign in §5 |
 
### External contacts (not project members)
 
| Person | Relation to this work |
|---|---|
| Annie | Author of existing QA scripts |
| Daizhong | Author of existing QA scripts |
 
Annie and Daizhong do not have access to the Claude Project or this team's chats; contact goes through Hengyue. Credit their scripts in code headers and in any upstream PR.
 
_Please correct/extend these tables._
 
---
 
## 3. Workflow
 
### Git
 
Branches on the fork:
- `master`: mirrors upstream `akleroy/phangs_imaging_scripts`; no QA commits.
- `QA-build`: development of ported/new QA code. Changes reach it only through reviewed PRs from `QA-build-<task name>` branches (rule 7).
- `QA-build-<task name>`: one branch per issue, off `QA-build` (e.g. `QA-build-beam`).
- `QA-build-workflow`: long-lived branch for updates to this file (no PR needed).
- `CMZ-QA`: integration branch. Ported code moves here from `QA-build` only once it passes the validation check below. The eventual upstream PR comes from `CMZ-QA`.

Rules:
1. Infrastructure build (Hengyue): port Daizhong's code on `QA-build`; each of Daizhong's existing plots is ported as a separate GitHub issue.
2. Validation of ported code: run Daizhong's original package and the ported version on the same NGC1097 data on MPCDF; outputs must agree within a small tolerance (definition open, see §7) before merging to `CMZ-QA`.
3. Team members may create their own branches on the fork and add their own plots/checks (not limited to Annie's or Daizhong's code), working from their own MPCDF copies. How these branches are merged into `CMZ-QA` is open (see §7).
4. Each person edits code locally, pushes to GitHub, and pulls into their own MPCDF copy.
5. Periodically sync `master` with upstream, then merge `master` into `CMZ-QA` to limit drift.
6. Review requirement for merges into `CMZ-QA`: open (see §7).
7. Per-issue branches and PRs (2026-11-26): code for each issue is committed on a branch `QA-build-<task name>` off `QA-build`, not on `QA-build` itself. It reaches `QA-build` through a pull request reviewed by other team members. The PR must show that the port is faithful: Daizhong's plot and ours side by side, plus the numerical comparison of the saved arrays. PRs go only from `QA-build-<task name>` to `QA-build`; no PRs to the upstream repo or to `CMZ-QA` as part of this workflow. PRs are for code changes only: updates to this file are committed on the long-lived branch `QA-build-workflow`, without a PR.
8. Modularity (2026-11-26): before writing a new QA utility, check whether code with the same function already exists in the repo, and reuse it. Code that exists only to reproduce Daizhong's plot faithfully but duplicates or closely resembles existing code is flagged in the issue (and PR). Separate cleanup issues will be opened later; at that stage plots may differ from Daizhong's as long as they effectively do the same.
9. Bugs in the original code (2026-11-26): the port stays faithful, but every bug found in Daizhong's code is recorded (§10 and the port issue/PR) and gets its own GitHub issue for the fix.
10. Saved plot data (2026-11-26): the data plotted in each QA plot is saved next to the PNG as an astropy Table (ECSV) instead of `.npz`, for numerical comparison.
### Keeping everyone in sync (Claude Project + GitHub)
 
- Claude chats are **per person** and Claude's memory is **per user** — nothing in your chat is automatically visible to others.
- Shared context = **this file** (+ code) in the Claude Project knowledge base. Re-sync / re-upload after changes.
- At the end of a productive chat, ask Claude: *"Summarise decisions, changes and open questions from this chat as an update to QA_PLAN.md"*, then commit it.
- Tasks live as GitHub issues (one per check), not in chats.
---
 
## 4. Architecture (to be decided — Phase 1)
 
Get familiar with the pipeline structure first: handlers (`phangsPipeline/handler*.py`), `scSCRIPTS` / `casaSCRIPTS` modules, plotting utilities, key files.
 
Open design decisions:
 
| # | Question | Options | Leaning | Decision |
|---|---|---|---|---|
| A1 | Where does QA live? | (a) new `handlerQA` following handler pattern; (b) standalone post-hoc tool; (c) both. Design draft suggests (c) led by (a) | (a) reuses key files and target lists. Proposal (Hengyue, 2026-11-19, not agreed): one `QAHandler(HandlerTemplate)` in `phangsPipeline/handlerQA.py`, run after all other stages, with no hooks in existing handlers. Per-stage loops (`loop_qa_imaging`, `loop_qa_postprocess`, `loop_qa_derived`, later `loop_qa_vis`) plus `loop_qa(do_all=True)`, so it can run right after one stage or all at the end. Targets/products/configs come from `KeyHandler` + `HandlerTemplate.looper()` instead of Daizhong's filename discovery. Plot/stat code in pure-Python `utilsQA*` / `scQA*` modules called by the handler. Compatible with A7(a) and A8 | **Decided (2026-11-23): (a).** QA is a handler (`QAHandler`) in `phangsPipeline`, run in series with the other stages from the pipeline run script: setting `do_qa = True` is all a user needs to produce the plots. No standalone tool for now. Option (b)/(c) may be revisited later |
| A2 | QA results format | (i) one record per *target × product × check*: status, metric values, thresholds used, plot paths. (ii) Design draft: one row per *metric* (long format), raw values stored, pass/warn/fail computed from the thresholds file at a `collect` step, so retuning thresholds needs no QA rerun and X1–X3 read raw metrics directly. Per-target JSON-lines, aggregated to one table (Parquet / ECSV). | — | _open_ |
| A3 | CASA vs pure Python | Split checks needing CASA (visibility-level: per-part PSF, sensitivity) from FITS-only checks | Keep separate | _open_ |
| A4 | Thresholds | Config/key file, never hard-coded; per-target/per-product overrides? | Config | _open_ |
| A5 | Plots | Standard per-target diagnostic directory + naming convention (draft: `qa/plots/<target>/<product>/<config>/<check_id>.png` + thumbnails); minimal required plot set per check | — | Partly decided (2026-11-23): QA output goes under a new `qa_root` entry in `master_key.txt`, parsed by `KeyHandler` and created by `make_missing_directories` like the other stage roots. Layout below `qa_root`, naming convention and minimal plot set still open |
| A6 | Integration of Annie/Daizhong scripts (external) | Port into new framework vs wrap as-is; maintenance falls to us either way | — | Port Daizhong's Python code (which already ports Annie's older IDL), validated against his original outputs on NGC1097 (2026-11-18) |
| A7 | Reporting or gating? | (a) QA only reports; (b) a QA fail can block downstream stages (opt-in key-file flag). Determines whether QA hooks are needed inside existing handlers. | — | _open_ |
| A8 | Retroactive QA | Must QA run on already-existing products? If yes, checks must work without in-process records, e.g. I3 must parse logs or degrade gracefully. | — | _open_ |
| A9 | Provenance in results | Fields per record: run ID, timestamp, pipeline git hash, CASA version, QA version, key-file hashes, input file checksums. Optional "provenance-only" sidecar JSON written by existing handlers (clean-loop record, stopping reason, predicted noise, applied parameters), with no QA logic in them. | — | _open_ |
| A10 | Waivers | Curated file (target, product, check, reason, who, date) so accepted issues show as "waived"; who may waive; do waivers expire when inputs change? | — | _open_ |
| A11 | Threshold calibration | Design draft suggests: run metrics on existing products first, set thresholds from sample distributions + visual inspection, instead of adopting numbers a priori | — | _open_ |
 
**Deliverable of Phase 1:** skeleton pushed to `qa` — empty module, results schema, one trivial check running end-to-end, plot output directory.
 
---
 
## 5. QA checks
 
Status key: `exists` · `scratch` · `new` · `undefined` (needs definition before work starts)
 
### 5.1 Pre-imaging
 
| ID | Check | Purpose | Status | Needs CASA | Owner |
|---|---|---|---|---|---|
| P1 | Integrated flux over cube | Detect TP bandwidth problems | exists? Not located in the received code. Candidates: `phangs_cube_compare.pro` / `phangs_tpcube_show.pro` (Annie's older IDL, archived in Daizhong's repo under `idl_code_by_annie_hughes/cube_compare/`; not in `cmz_qa_idl`), Daizhong's `python_code_by_daizhong_liu/phangs_alma_QA_two_cube_image_comparison.py` (to confirm, see §7) | ? | _TBD (porting)_ |
| P2 | Field-of-view coverage map | Map of anchor pointings: pointing centres + primary-beam circles from field-selected data | scratch (Jakob). Daizhong's MS module has a version with a fixed 60″ primary beam (wrong for 7m and for frequencies other than ~230 GHz); Jakob's version to replace it | likely (reads MS) | Jakob |
| P3 | Per-part diagnostics of concatenated data | PSF, noise, … of part 1 vs part 2 passed to joint deconvolution | new | yes | |
| P4 | Sensitivity per array configuration | Sensitivity of each constituent config and of the combination | new | yes / sensitivity calc. | |
 
### 5.2 Imaging
 
| ID | Check | Purpose | Status | Needs CASA | Owner |
|---|---|---|---|---|---|
| I1 | Beam checks | Beam shape/size consistency, esp. when combining multiple 12m arrays — **not in previous QA** | new — **high priority**. Existing code reads one beam per cube (Daizhong: largest-area beam for multibeam cubes), so there are no per-plane checks | no (FITS headers) | |
| I2 | Residual RMS ("Antonio plot") | Residual noise diagnostics | undefined. Both code bases label the per-channel 2D value-density spectrum (+ per-channel percentiles in/out of mask) as the "Antonio" plot; implemented in Daizhong's `diagnostics/cube_show_plots.py`. Interpretation to be confirmed | no | |
| I3 | Convergence / iteration limit | Did clean converge, or hit max loop before convergence? | new. Not in Annie's or Daizhong's code; starting point: upstream `casaImagingRoutines.check_noise_convergence()` (tclean summary) | no (logs) | |
| I4 | Artefact capture | Flag imaging artefacts | undefined. Residual histograms vs. signal-free data exist in both code bases (plots only, no metric) | ? | |
 
### 5.3 Products
 
| ID | Check | Purpose | Status | Needs CASA | Owner |
|---|---|---|---|---|---|
| D1 | Mask consistency | Are PHANGS masks identical where they should be? | undefined | no | |
| D2 | Moment-map clipping | Is clipping in moment creation appropriate? | undefined | no | |
 
### 5.4 Cross-sample comparisons
 
| ID | Check | Purpose | Status | Owner |
|---|---|---|---|---|
| X1 | Beam diversity | Spread of beams across sample | new | |
| X2 | Sensitivity diversity | Spread of sensitivities across sample | new | |
| X3 | Residual skewness | Distribution of residual skewness across sample | new | |
 
Cross-sample checks read only from the QA results (A2), so they come last.
 
### 5.5 Proposed additional checks (from design draft, not agreed)
 
New IDs below avoid collisions with §5.1–5.4. Postprocessing checks use the prefix `PP` (a stage not yet in this plan). Thresholds are draft suggestions only, to be calibrated (A11). σ = robust noise (MAD × 1.4826).
 
| ID | Stage | Check | Detects | Metric / computation | Pass / warn / fail (draft) | Needs CASA | Draft priority |
|---|---|---|---|---|---|---|---|
| P5 | Pre-imaging | Staging sanity | Missing EBs/fields/SPWs; line window off the band; regridding/frame errors | Staged data vs ms_key; SPW coverage of v_sys ± ½ v_width plus line-free margins; channel width/count, frame (LSRK), rest frequency vs config | All match / margin < N chan / missing, truncated or mismatched | yes (MS) | high impact, low effort |
| I5 | Imaging | Residual noise vs prediction | Wrong weights, unflagged RFI/atmospheric lines, edge-channel rolloff | σ in signal-free residual ÷ predicted noise (`apparentsens` or sum of weights), also per channel | 0.9–1.2 / 1.2–1.5 / > 1.5 or < 0.8 | yes (prediction) | high, low. Relation to I2 ("Antonio plot") and P4 to be checked |
| I6 | Imaging | Corrupt-output sanity | Crashed/empty planes, corrupt files | NaN/zero planes; non-finite pixels inside PB-valid area; values > 10× expected peak | none / – / any | no | high, low |
| PP1 | Postprocessing | PB correction | Missing/mismatched pb, wrong cutoff, applied twice or not at all | pb exists and matches grid; pixels below cutoff masked; σ ∝ 1/PB on pbcor cube | consistent / slope off 10–25% / missing or double | no | high, low |
| PP2 | Postprocessing | Feather flux recovery (only if TP in scope) | TP–interferometer flux-scale mismatch, wrong `sdfactor`, TP unit/beam errors, failed feather | Interferometer-only and feathered cubes convolved to TP beam on common grid/mask: integrated-flux ratio and per-channel spectral ratio vs TP | feathered/TP 0.9–1.1 / 0.8–1.2 / outside; int-only/TP > 1.1 → warn | no | draft's most important single check |
| PP3 | Postprocessing | Round-beam convolution | Unreachable target resolution, surviving per-plane beams, kernel errors | Output beam round (\|BMAJ−BMIN\|/BMAJ < 1%) and identical in all channels; target ≥ native BMAJ; σ change consistent with beam-area scaling | pass / noise scaling off > 15% / non-round or target < native | no | high, low (overlaps I1) |
| PP4 | Postprocessing | Headers and units | Silent unit/metadata errors propagating to all products | BUNIT, RESTFRQ, SPECSYS, beam keywords; Jy/beam→K factor vs value from beam and frequency | exact / – / any mismatch | no | high, low |
| PP5 | Postprocessing | Mosaic consistency (multi-part targets) | Flux-scale/alignment mismatch between parts, seams | In overlaps: flux ratio, σ ratio, astrometric offset; identical spectral grids | 0.9–1.1 / 0.8–1.2 / outside | no | medium |
| D3 | Products | Noise-cube validity | Biased noise model, so masks and uncertainties are wrong | σ and MAD of data/noise in signal-free voxels, vs channel and PB radius | 0.9–1.1 / 0.8–1.2 / outside | no | high, low |
 
Lower-priority candidates in the design draft (draft IDs, which differ from this plan's): flag fraction (S3), per-EB relative weights incl. 12m vs 7m (S4, relevant to P3/P4), continuum-subtraction residual (S5), clean-mask completeness (I4), TP spatial/spectral alignment (P3), multi-resolution flux consistency (D5).
 
The draft also proposes a sample-level layer: robust z-scores of every stored metric across the sample, to flag outliers that pass fixed thresholds. This generalises X1–X3.
 
### 5.6 Candidate definitions for new / undefined checks (from design draft, not agreed)
 
These are drafts for the owners to confirm or replace. Thresholds are uncalibrated suggestions (A11).
 
```
ID / name: I1 Beam checks
Stage: Imaging
What failure does it detect? Inconsistent per-channel beams; strongly elongated beams (esp. when combining multiple 12m arrays); target round beam not attainable.
Inputs (files / products): image/residual cube FITS headers (per-plane beam table); PSF cube (for sidelobe); target resolutions from config.
Metric(s) and how computed: fractional variation of BMAJ, BMIN, BPA across channels; axial ratio BMAJ/BMIN; peak PSF sidelobe; native BMAJ vs target round beam.
Pass / warn / fail criteria (+ justification): pass if variation < 5% and axial ratio < 1.5; warn 5–10% or 1.5–2; fail > 10%, > 2, or target < native. Per-plane variation must be removed by round-beam convolution; an elongated or unreachable beam breaks fixed-resolution products.
Output (values, plots): metrics per cube; BMAJ/BMIN/BPA vs channel plot. Values feed X1.
Needs CASA? Runtime estimate: no (headers; PSF via FITS export); seconds.
Owner: _TBD_
```
 
```
ID / name: I3 Convergence / iteration limit
Stage: Imaging
What failure does it detect? Clean stopped on the iteration/cycle cap instead of the threshold or convergence criterion; under-cleaning; divergence. ("Max loop breach" is read here as stopping on the cap; interpretation not confirmed, see §7.)
Inputs (files / products): clean-loop record (stopping reason, model flux per loop) from logs or provenance sidecar (A8, A9); residual cube; clean mask; noise estimate.
Metric(s) and how computed: stopping reason; peak residual inside mask ÷ σ; model-flux growth over loops (monotonic? last-loop fractional change).
Pass / warn / fail criteria (+ justification): pass if stopped on threshold/convergence and residual < 2σ; warn if stopped on cap or residual 2–4σ; fail if residual > 4σ or model flux non-monotonic. Uncleaned flux remains in dirty-beam units, biasing fluxes and morphology.
Output (values, plots): metrics; model-flux vs loop plot.
Needs CASA? Runtime estimate: no; seconds.
Owner: _TBD_
```
 
```
ID / name: I4 Artefact capture
Stage: Imaging
What failure does it detect? Sidelobe / deconvolution artefacts; large-scale negative bowls (missing short spacings, poor deconvolution of extended emission); striping.
Inputs (files / products): residual (and image) cube; clean/signal mask.
Metric(s) and how computed: fraction of signal-free voxels below −3σ and −4σ vs Gaussian expectation (accounting for beam-correlated voxels); repeat after smoothing to ~3× beam; FFT of residual planes for striping; residual skewness stored as raw metric (feeds X3).
Pass / warn / fail criteria (+ justification): negative-tail excess ≤ 2× Gaussian / 2–5× / > 5×; significant FFT spike → warn. Pure noise should follow Gaussian tails; excess negatives indicate artefacts.
Output (values, plots): metrics; residual histogram vs Gaussian; smoothed-residual map.
Needs CASA? Runtime estimate: no; minutes per cube (smoothing).
Owner: _TBD_
```
 
```
ID / name: D1 Mask consistency
Stage: Products
What failure does it detect? (a) Masks expected to be identical that differ; (b) masks picking up noise (false positives).
Inputs (files / products): cubes, noise cubes, strict/broad masks; mask settings.
Metric(s) and how computed: (a) if identity is expected: voxel-wise comparison of the masks in question (which products/versions is still open, see §7); (b) run strict/broad masking on the inverted cube (−data); flux of detections ÷ flux in the positive mask.
Pass / warn / fail criteria (+ justification): (a) identical / – / any difference; (b) < 2% / 2–5% / > 5%. Inverted-cube detections estimate the false-positive rate directly.
Output (values, plots): metrics; mask-difference and false-positive maps.
Needs CASA? Runtime estimate: no; minutes per cube.
Owner: _TBD_
```
 
```
ID / name: D2 Moment-map clipping
Stage: Products
What failure does it detect? Clipping/masking removing real flux; emission truncated at the velocity-window edges (biasing mom0/mom1/mom2); moment or uncertainty-map bugs.
Inputs (files / products): cube, masks, noise cube, mom0/emom0/mom1, v_sys and window from keys.
Metric(s) and how computed: mom0 map sum vs masked-cube sum; broad-mask mom0 flux ÷ total cube flux; masked flux in first/last N channels of the window; fraction of finite emom0; mom1 range vs v_sys ± v_width.
Pass / warn / fail criteria (+ justification): internal agreement < 2% and broad/total > 0.8 → pass; edge flux < 1% of total → warn; ≥ 1% or internal mismatch → fail.
Output (values, plots): metrics; edge-channel spectrum; mom0 vs masked-sum comparison.
Needs CASA? Runtime estimate: no; seconds–minutes.
Owner: _TBD_
```
 
### Template for defining a check (fill in before implementing)
 
```
ID / name:
Stage:
What failure does it detect?
Inputs (files / products):
Metric(s) and how computed:
Pass / warn / fail criteria (+ justification):
Output (values, plots):
Needs CASA? Runtime estimate:
Owner:
```
 
---
 
## 6. Phased plan
 
| Phase | Goal | Key tasks | Exit criterion |
|---|---|---|---|
| **0 — Inventory** | Know what exists | Fork + branches; obtain Annie/Daizhong code; inventory (§10) | Done 2026-11-18, except definitions of `undefined` checks |
| **1 — Baseline run** | Reference outputs | Run Daizhong's package on NGC1097 (ALMA CMZ data) on MPCDF; record environment (package versions) | Reference outputs stored on MPCDF |
| **2 — Port existing** | Prove the framework | Port each of Daizhong's plots as a separate issue on `QA-build`; validate against Phase 1 outputs (§3); merge to `CMZ-QA` | All of Daizhong's plots ported and validated; infrastructure ready by Christmas 2026 |
| **3 — Quick wins** | High impact, low effort | I1 (beams), I3 (convergence) | Run on a test subset of targets |
| **4 — Residuals & products** | | I2, I4, D1, D2 | |
| **5 — CASA-level** | Hardest checks | P3, P4 | |
| **6 — Sample view** | | X1–X3; summary report / dashboard | QA run on full sample |
 
Proposed (design draft, not agreed):
- Phase 1: use I1 (beam checks, FITS headers only) as the "one check end-to-end" instead of a dummy check.
- Phase 3: add cheap FITS-only checks I6, PP4, D3 alongside I1 and I3, if adopted from §5.5.
- Resolve A2, A7 and A8 before Phase 1 code, since they shape the results schema and whether existing handlers need hooks.
- Use the Phase 3 test-subset run to calibrate thresholds empirically (A11).
---
 
## 7. Open questions
 
- [ ] What exactly is the **"Antonio plot"**? Candidate: per-channel 2D value-density spectrum (label used in both Annie's and Daizhong's code); to confirm with Annie
- [ ] "Max loop breach before convergence" — which parameter/log does this refer to?
- [ ] Mask consistency (D1): identical *across which products / versions*?
- [ ] Artefact capture (I4): which artefacts, detected how?
- [ ] Which CASA version(s) must QA support?
- [x] ~~Test subset of targets for development?~~ NGC1097 (2026-11-18)
- [ ] Where are QA outputs stored for the full sample, and who can access them? (QA runs on MPCDF; storage location and access still open)
- [ ] Upstream plan: PR will come from `CMZ-QA`; when do we talk to the pipeline maintainers?
- [x] ~~Are Annie & Daizhong happy for their scripts to be ported/modified in our fork?~~ Yes, incl. sharing with the team
- [ ] How do Annie & Daizhong prefer to be credited (code headers, upstream PR, publications)? (Hengyue to ask)
- [ ] Is `phangs_alma_qa_pipeline` Daizhong's current version, and will he keep developing it? (Hengyue to ask)
- [ ] Technical questions for Annie & Daizhong: final list still to be agreed (candidates: which code P1 refers to; "Antonio plot"; what `cmz_qa_idl` adds; whether self-generated noise/mask in `run_cmz_qa.pro` is intentional)
- [ ] Validation tolerance for ported code (§3). Proposal (not agreed): numeric outputs (JSON, FITS) same keys/shapes/NaN positions and `numpy.allclose(rtol=1e-6)`; plots compared via the plotted arrays saved alongside, not PNG pixels; PDF/HTML reports excluded; both versions run in the same recorded MPCDF environment
- [ ] Review requirement for merges `QA-build` → `CMZ-QA`: named reviewer per PR, or none for now?
- [x] ~~Location of QA code within the package (A1)~~ `QAHandler` in `phangsPipeline`, enabled by `do_qa = True` in the run script (2026-11-23)
- [ ] Data scope for PHANGS-CMZs: targets, lines, configurations, TP or not (see §1 Scope)
- [ ] Is postprocessing (PB correction, feathering, round-beam convolution, mosaicking) in scope for QA? (§5.5)
- [ ] Which of the proposed checks in §5.5 to adopt, and with which owners?
- [ ] Interpretation of "max loop breach" for I3: does it mean clean stopping on the iteration/cycle cap? (candidate definition in §5.6)
- [ ] Noise reference for I5: `apparentsens`, sum of weights, or Tsys-based radiometer estimate?
- [ ] Feather QA method for PP2 (if in scope): comparison region/mask, image-plane vs uv-overlap comparison, TP calibration uncertainty, which product is the flux reference
- [ ] Minimal required plot set per check (A5)
- [ ] How do members' own branches (new plots/checks) get merged into `CMZ-QA`: same review rule as the port? Only after the infrastructure is in place?
- [ ] Reporting layer: reuse Daizhong's HTML report/portal, Annie's `cmz_qa_site` (GitHub Pages), or both?
 
## 8. Next actions
 
> Interim list until the GitHub Project board exists. Once it does, replace this table with a link to the board.
 
| Task | Owner | Status | Issue / PR |
|---|---|---|---|
| Obtain Annie's and Daizhong's QA code | Hengyue | done (see §10) | — |
| Create fork and branches (`CMZ-QA`, `QA-build`) | Hengyue | done | — |
| Give team access to the fork; set up GitHub Project | Hengyue | open | — |
| Set up code copy on MPCDF | Hengyue | open | — |
| Run Daizhong's package on NGC1097 on MPCDF; record environment | Hengyue | open | — |
| Open one issue per Daizhong plot to be ported | Hengyue | open | — |
| Agree validation tolerance and review rule (§7) | _TBD_ | open | — |
| Ask Annie & Daizhong: preferred form of credit; whether Daizhong's package is his current version | Hengyue | open | — |
| Clean up FoV coverage plot (P2) for porting | Jakob | open | — |
| Fill in data scope (§1) | All | open | — |
| Fill in definitions for `undefined` checks and assign owners (§5) | All | open | — |
| Architecture discussion: A1, A2, A6, A7, A8, with §10 as input; record outcomes in §4 | All | open | — |
 
---
 
## 9. Decision log
 
| Date | Decision | Who |
|---|---|---|
| 2026-11-26 | Each issue is developed on a branch `QA-build-<task name>` off `QA-build` and merged via a PR into `QA-build` after review by team members; the PR shows Daizhong's and our plot side by side (§3 rule 7) | Team meeting |
| 2026-11-26 | Every bug found in Daizhong's code while porting is recorded and gets its own fix issue; the port itself stays faithful (§3 rule 9) | Team meeting |
| 2026-11-26 | Plot data saved as astropy Tables (ECSV) instead of `.npz` (§3 rule 10) | Team meeting |
| 2026-11-26 | Modularity: reuse existing repo code for QA utilities; flag port-only duplicates in issues for later cleanup issues, where plots may then differ from Daizhong's (§3 rule 8) | Team meeting |
| 2026-11-23 | A1: QA is a handler (`QAHandler`) in `phangsPipeline`, run in series with the other pipeline stages; `do_qa = True` in the run script produces the plots. No standalone tool for now | Team |
| 2026-11-23 | A5 (partial): QA output root is a new `qa_root` key in `master_key.txt`, handled by `KeyHandler` like the other stage roots | Hengyue |
| 2026-11-18 | Work in Hengyue's fork; `CMZ-QA` is the integration branch (supersedes `qa` from 2026-11-05); development on `QA-build`; fork `master` mirrors upstream; upstream PR from `CMZ-QA` | Team meeting |
| 2026-11-18 | Hengyue leads the infrastructure build; goal: QA infrastructure by Christmas 2026, galaxy QA from the New Year | Team meeting |
| 2026-11-18 | Port Daizhong's code; validate on NGC1097 (ALMA CMZ data): ported output must agree with Daizhong's within a small tolerance before merging to `CMZ-QA` | Team meeting |
| 2026-11-18 | One GitHub issue per ported Daizhong plot; plots not in Daizhong's code are not part of the infrastructure port. Members may develop their own plots/checks on their own branches | Team meeting |
| 2026-11-18 | All QA runs on MPCDF; each member works from their own MPCDF copy (edit → push to GitHub → pull on MPCDF) | Team meeting |
| 2026-11-12 | Annie & Daizhong agree that their QA code may be shared with the team and ported/modified in our fork; form of credit still open (reported by Hengyue) | Annie, Daizhong |
| 2026-11-05 | Work in team fork; `qa` integration branch; feature branches off `qa` | Team meeting |
| 2026-11-05 | This file is the shared source of truth for the QA effort | Team meeting |

## 10. Inventory of existing QA code (2026-11-16)

Status as received; not yet tested on PHANGS-CMZs products.

**Daizhong: `phangs-alma-data-quality-assessment-scripts`** (private; package `phangs_alma_qa_pipeline`, v0.1.0)
- Pure Python (astropy, spectral-cube, radio-beam; optional python-casacore for MS QA). No CASA. Standalone tool reading the PHANGS master key; no pipeline handler hooks.
- Modules: MS (metadata, uv coverage, field/SPW coverage), imaging, postprocess (incl. postprocess/imaging flux ratio, PB stats), derived (moment maps).
- `diagnostics/`: line-by-line port of Annie's older `phangs_cube_show.pro` (robust_sigma, per-channel stats in/out of mask, rms0, histograms, "Antonio" density spectra, channel maps) plus Daizhong's legacy per-channel 5-panel figures.
- Outputs per cube: JSON stats, pdflatex PDF (IDL layout), unified HTML report; survey-wide portal `index.html`. Production run on 90 cubes reported in its TODO.
- No pass/warn/fail or thresholds; raw metrics and plots only.
- Suspected issues: beam-area unit conversion in `imaging_utils.extract_cube_info` (BMAJ in degrees treated as radians); fixed 60″ PB in MS coverage plot; hard-coded test paths; vendored `analysisUtils.py` (upstream is removing this dependency, PR #402).
- Per-channel beams not supported (found 2026-11-23, NGC 1097 imaging baseline): `extract_cube_info` reads only the `BMAJ`/`BMIN`/`BPA` header keywords. CASA imaging cubes with per-channel beams store them in a `BEAMS` table extension with no `BMAJ` keyword (confirmed for `ngc1097_12mext+12m+7m_xproj_co21_joint_cube.fits`: HDUs `PRIMARY`, `BEAMS`), so the beam is set to 0 and `plot_beam_info` is skipped ("No valid beam information"). Affects imaging-stage cubes; postprocessed cubes have a common beam. A faithful port has the same limitation, so `beam_info` can only be validated on postprocessed cubes.
- `sdintimaging` imaging cubes are not found (found 2026-11-23, GitHub issue #3): FITS export names them `<t>_<c>_<p>_joint_cube.fits` (+ `_joint_cube_residual`, …), which `DataDiscovery.parse_filename` classes as 'other', so `phangs-qa run` silently does no imaging QA. Baseline workaround: symlinks with the plain `tclean` names. The port builds file names from `imaging_method` instead (#4).
- `qa_results.json` always reports `"success": false` (found 2026-11-23): `modules/imaging/qa_module.py` writes the JSON before setting `result['success'] = True`. The run-level `qa_summary.json` reports the correct status.
- PDF failures are not recorded as errors (found 2026-11-23): the cube_show PDF needs `subfigure.sty` (loaded twice in `reporting/pdf_generator.py`, never used), which is missing from the MPCDF TeX Live, so pdflatex stops. The cube_show `errors` list stays empty; the only sign is `pdf_file: null` and `success: false` in `<name>_cube_show.json` (details in `pdf_build/*.log`). Workaround: `--skip-pdf`.
- Also contains archived legacy code: Annie's older IDL suite (`idl_code_by_annie_hughes/cube_compare/`, incl. `phangs_cube_show.pro`, the reference for the Python port) and Daizhong's older Python QA (`python_code_by_daizhong_liu/`).
- Not ported to the package (legacy only): `phangs_cube_compare.pro` (regrid two cubes to common grid/resolution/FoV and compare statistics, e.g. ALMA TP vs. IRAM HERA), `phangs_tpcube_show.pro` (TP cube inspection), Daizhong's two-cube comparison and calibrator-flux scripts.
- Vendors a copy of `analysisUtils.py` (upstream is removing this dependency, PR #402).

**Annie: `cmz_qa_idl`** (public)
- IDL; CMZ-specific fork of `phangs_cube_show.pro` (`cmz_cube_show.pro`); one-row FITS summary table (~100 stats columns), PNG plots. Does not include the cube-comparison or TP routines.
- Dependencies not bundled: IDLAstro, Freudenreich robust routines, CPROPStoo, Coyote Graphics, ImageMagick.
- `run_cmz_qa.pro` currently passes the data cube as residual and generates noise and mask from the cube (CPROPStoo), so residual-based outputs are not meaningful yet.
- `cmz_check_header` requires K units and reads only single-beam keywords.
- Code comparison with the older `phangs_cube_show.pro` (and hence Daizhong's port): helper routines identical; statistics identical. CMZ version adds per-channel mask maps, a velocity-collapsed mask map and a channel-averaged noise map (not in Daizhong's port); enables channel maps (already in Daizhong's port); drops the uv report and LaTeX PDF. `gennoise`/`genmask` exist in both IDL versions but not in Daizhong's port. Numerical agreement IDL vs. Python untested.

**Annie: `cmz_qa_site`** (public)
- jinja2 static-site generator deployed via GitHub Pages; displays Annie's PNGs and selected FITS-table columns per galaxy/product. Display only.
- Expects `cmz_qa_output.fits`, whereas the IDL code writes `<name>_cube_show_output.fits`.

**Already in upstream `phangs_imaging_scripts`** (relevant to QA)
- `casaImagingRoutines.check_noise_convergence()` (+ tests): candidate basis for I3.
- `handlerTestImaging`: beam properties, PSF radial profiles, CSV summary (relevant to I1, P3).
- `utilsTheoreticalNoise`: theoretical noise maps from AOT pointings (candidate noise reference for P4, I5).
