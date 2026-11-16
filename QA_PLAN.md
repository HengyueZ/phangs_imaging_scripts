# PHANGS-CMZs Imaging Quality Assurance — Plan
 
> **This file is the single source of truth for the QA effort.**
> Decisions, owners, open questions and status live here — not in individual chats.
> If a chat (with a colleague or with Claude) produces a decision or change, update this file and commit it.
 
| | |
|---|---|
| **Last updated** | 2026-11-16 |
| **Upstream repo** | [akleroy/phangs_imaging_scripts](https://github.com/akleroy/phangs_imaging_scripts) |
| **Team fork** | [HengyueZ/phangs_imaging_scripts](https://github.com/HengyueZ/phangs_imaging_scripts) (personal fork; collaborator access for team members to be set up) |
| **Integration branch** | `CMZ-QA` exists on the fork (created by Hengyue, currently identical to upstream `master` @ `b96bbc6`). ⚠ §9 records `qa` as the branch name; rename the branch or confirm `CMZ-QA` (see §7). |
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
| Hengyue | Create fork + `qa` branch; liaise with Annie & Daizhong; get existing QA scripts onto GitHub |
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
 
1. Fork `phangs_imaging_scripts` → team fork.
2. Create `qa` branch on the fork — this is the integration branch. Protect it (changes via PR only).
3. Every new feature/check: **branch off `qa`** → PR back into `qa` → at least one reviewer.
4. Periodically merge upstream `master` into the fork to avoid drift.
5. Long term: PR the QA module upstream (coordinate with pipeline maintainers early).
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
| A1 | Where does QA live? | (a) new `handlerQA` following handler pattern; (b) standalone post-hoc tool; (c) both. Design draft suggests (c) led by (a): `handlerQA` as entry point, image-level checks written CASA-free on numpy/FITS so they also run standalone, existing handlers gain only provenance hooks (see A9) | (a) reuses key files and target lists | _open_ |
| A2 | QA results format | (i) one record per *target × product × check*: status, metric values, thresholds used, plot paths. (ii) Design draft: one row per *metric* (long format), raw values stored, pass/warn/fail computed from the thresholds file at a `collect` step, so retuning thresholds needs no QA rerun and X1–X3 read raw metrics directly. Per-target JSON-lines, aggregated to one table (Parquet / ECSV). | — | _open_ |
| A3 | CASA vs pure Python | Split checks needing CASA (visibility-level: per-part PSF, sensitivity) from FITS-only checks | Keep separate | _open_ |
| A4 | Thresholds | Config/key file, never hard-coded; per-target/per-product overrides? | Config | _open_ |
| A5 | Plots | Standard per-target diagnostic directory + naming convention (draft: `qa/plots/<target>/<product>/<config>/<check_id>.png` + thumbnails); minimal required plot set per check | — | _open_ |
| A6 | Integration of Annie/Daizhong scripts (external) | Port into new framework vs wrap as-is; maintenance falls to us either way | Depends on inventory | _open_ |
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
| P1 | Integrated flux over cube | Detect TP bandwidth problems | exists? Not located in the received code. Candidates: Annie's `phangs_cube_compare.pro` / `phangs_tpcube_show.pro`, Daizhong's `phangs_alma_QA_two_cube_image_comparison.py` (to confirm, see §7) | ? | _TBD (porting)_ |
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
| **0 — Inventory** | Know what exists | Fork + `qa` branch; upload Annie/Daizhong scripts; define all `undefined` checks; list inputs each needs | Existing scripts on GitHub; every check in §5 has a written definition |
| **1 — Architecture** | Agree framework | Resolve A1–A6; push skeleton | Skeleton on `qa`, one dummy check runs end-to-end |
| **2 — Port existing** | Prove the framework | Port P1, P2 into schema | Existing checks produce schema output + plots |
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
 
- [ ] What exactly is the **"Antonio plot"**? (owner of definition: ?)
- [ ] "Max loop breach before convergence" — which parameter/log does this refer to?
- [ ] Mask consistency (D1): identical *across which products / versions*?
- [ ] Artefact capture (I4): which artefacts, detected how?
- [ ] Which CASA version(s) must QA support?
- [ ] Test subset of targets for development?
- [ ] Where are QA outputs stored for the full sample, and who can access them?
- [ ] Upstream plan: when do we talk to the pipeline maintainers?
- [ ] Are Annie & Daizhong happy for their scripts to be ported/modified in our fork, and how should they be credited? (Hengyue to ask)
- [ ] Data scope for PHANGS-CMZs: targets, lines, configurations, TP or not (see §1 Scope)
- [ ] Is postprocessing (PB correction, feathering, round-beam convolution, mosaicking) in scope for QA? (§5.5)
- [ ] Which of the proposed checks in §5.5 to adopt, and with which owners?
- [ ] Interpretation of "max loop breach" for I3: does it mean clean stopping on the iteration/cycle cap? (candidate definition in §5.6)
- [ ] Noise reference for I5: `apparentsens`, sum of weights, or Tsys-based radiometer estimate?
- [ ] Feather QA method for PP2 (if in scope): comparison region/mask, image-plane vs uv-overlap comparison, TP calibration uncertainty, which product is the flux reference
- [ ] Minimal required plot set per check (A5)
- [ ] Integration branch name: rename `CMZ-QA` → `qa` (as recorded in §9), or confirm `CMZ-QA` and log the change
- [ ] Keep the fork under Hengyue's account or move it to a GitHub organisation?
- [ ] Which code does P1 refer to? (Hengyue to ask Annie & Daizhong)
- [ ] Is the "Antonio plot" the per-channel 2D value-density spectrum used in both code bases? (Hengyue to ask Annie)
- [ ] Is Daizhong's `phangs_alma_qa_pipeline` package his current version, and will he keep developing it? (affects A6)
- [ ] What does Annie's `cmz_qa_idl` add beyond the older `phangs_cube_show.pro` that Daizhong ported? Were the self-generated noise cube and mask in `run_cmz_qa.pro` intentional or a stopgap?
- [ ] Reporting layer: reuse Daizhong's HTML report/portal, Annie's `cmz_qa_site` (GitHub Pages), or both?
---
 
## 8. Next actions
 
> Interim list until the GitHub Project board exists. Once it does, replace this table with a link to the board.
 
| Task | Owner | Status | Issue / PR |
|---|---|---|---|
| Contact Annie & Daizhong (external); get existing QA scripts | Hengyue | done: code received (see §10) | — |
| Create fork and integration branch; add fork URL to header | Hengyue | done: fork + `CMZ-QA` created; branch name to be settled (§7) | — |
| Add team members as collaborators; enable branch protection (PR + 1 reviewer) | Hengyue | open | — |
| Ask Annie & Daizhong: permission/credit, P1 code, "Antonio plot", current versions, CMZ-specific additions (§7) | Hengyue | open | — |
| Clean up FoV coverage plot (P2) for porting | Jakob | open | — |
| Diff Annie's `cmz_cube_show.pro` against Daizhong's Python port; list missing features | _TBD_ | open | — |
| Test-run Daizhong's `phangs-qa` on one PHANGS-CMZs target with real pipeline products | _TBD_ | open | — |
| Verify suspected issues in Daizhong's code: beam-area unit conversion (`imaging_utils.extract_cube_info`), fixed 60″ PB in MS coverage plot | _TBD_ | open | — |
| Fill in data scope (§1) | All | open | — |
| Fill in definitions for `undefined` checks and assign owners (§5) | All | open | — |
| Architecture discussion: A1, A2, A6, A7, A8, with §10 as input; record outcomes in §4 | All | open | — |
| Set up GitHub Project board; one issue per check | _TBD_ | open | — |
 
---
 
## 9. Decision log
 
| Date | Decision | Who |
|---|---|---|
| 2026-11-05 | Work in team fork; `qa` integration branch; feature branches off `qa` | Team meeting |
| 2026-11-05 | This file is the shared source of truth for the QA effort | Team meeting |

## 10. Inventory of existing QA code (2026-11-16)

Status as received; not yet tested on PHANGS-CMZs products.

**Daizhong: `phangs-alma-data-quality-assessment-scripts`** (private; package `phangs_alma_qa_pipeline`, v0.1.0)
- Pure Python (astropy, spectral-cube, radio-beam; optional python-casacore for MS QA). No CASA. Standalone tool reading the PHANGS master key (A1 option b); no pipeline handler hooks.
- Modules: MS (metadata, uv coverage, field/SPW coverage), imaging, postprocess (incl. postprocess/imaging flux ratio, PB stats), derived (moment maps).
- `diagnostics/`: line-by-line port of Annie's older `phangs_cube_show.pro` (robust_sigma, per-channel stats in/out of mask, rms0, histograms, "Antonio" density spectra, channel maps) plus Daizhong's legacy per-channel 5-panel figures.
- Outputs per cube: JSON stats, pdflatex PDF (IDL layout), unified HTML report; survey-wide portal `index.html`. Production run on 90 cubes reported in its TODO.
- No pass/warn/fail or thresholds; raw metrics and plots only.
- Not ported (legacy only): Annie's `phangs_cube_compare.pro`, `phangs_tpcube_show.pro`; Daizhong's two-cube comparison and calibrator-flux scripts.
- Vendors a copy of `analysisUtils.py` (upstream is removing this dependency, PR #402).

**Annie: `cmz_qa_idl`** (public)
- IDL; newer CMZ-specific fork of the `phangs_cube_show.pro` lineage (`cmz_cube_show.pro`), one-row FITS summary table (~100 stats columns), PNG plots.
- Dependencies not bundled: IDLAstro, Freudenreich robust routines, CPROPStoo, Coyote Graphics, ImageMagick.
- `run_cmz_qa.pro` currently passes the data cube as residual and generates noise and mask from the cube (CPROPStoo), so residual-based outputs are not meaningful yet.
- `cmz_check_header` requires K units and reads only single-beam keywords.

**Annie: `cmz_qa_site`** (public)
- jinja2 static-site generator deployed via GitHub Pages; displays Annie's PNGs and selected FITS-table columns per galaxy/product. Display only.
- Expects `cmz_qa_output.fits`, whereas the IDL code writes `<name>_cube_show_output.fits`.

**Already in upstream `phangs_imaging_scripts`** (relevant to QA)
- `casaImagingRoutines.check_noise_convergence()` (+ tests): candidate basis for I3.
- `handlerTestImaging`: beam properties, PSF radial profiles, CSV summary (relevant to I1, P3).
- `utilsTheoreticalNoise`: theoretical noise maps from AOT pointings (candidate noise reference for P4, I5).
 
