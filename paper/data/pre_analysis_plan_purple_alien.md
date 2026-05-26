# Pre-Analysis Plan: Purple Alien HydraNet Variant

## Date
2026-05-26

## Motivation
Bright_starship (the first HydraNet variant tested) produces near-zero predictions
for non-state and one-sided violence. The per-type extension is meaningless when
99.7-100% of cell-months are ties (both versions degenerate at zero).

Purple_alien is a second HydraNet variant with calibration-partition predictions
available. Initial inspection shows substantially more nonzero predictions across
all three violence types:
- lr_sb_best: 13,006 / 471,960 nonzero in origin_0 (2.8%)
- lr_ns_best: 4,241 / 471,960 nonzero in origin_0 (0.9%)
- lr_os_best: 9,488 / 471,960 nonzero in origin_0 (2.0%)

This is qualitatively different from bright_starship (566 ns, 40 os nonzero).

## Differences from bright_starship analysis
1. **Partition:** Calibration (Jan 2017 - Dec 2020), not validation (Jan 2021 - Dec 2024).
   The calibration partition overlaps with training data, so predictions may be
   better calibrated but less indicative of genuine out-of-sample performance.
2. **Model:** Purple_alien, not bright_starship. Same HydraNet architecture,
   different training configuration.

## What we observed with bright_starship (state-based)
- 6,725 cell-months after join (reported best > 0)
- Classical CRPS: tight wins 209 (3.1%), ties 1,301 (19.3%), honest wins 5,215 (77.5%)
- Factor-of-two subset: 1,048 (15.6%)
- In factor-of-two subset, classical tight wins: 209
- Parametric reversal: 209/209 (100%)
- RVI reversal: 208/209 (99.5%)

## Predictions for purple_alien

### State-based
Expect similar pattern to bright_starship: most cell-months are honest-wins or ties,
a small factor-of-two subset, and near-complete reversal of classical tight wins
under both parametric and RVI constructors. The exact numbers will differ due to
different model and different partition.

### Non-state
This is the key test. If purple_alien produces meaningful nonzero predictions for
non-state violence, we expect:
- Fewer ties than bright_starship (which had 99.7%)
- A factor-of-two subset with some classical tight wins
- Reversal rates comparable to state-based

If the tie rate is still >90%, purple_alien is also effectively a state-based-only
forecaster for the purposes of this paper.

### One-sided
Same logic as non-state. Bright_starship had 100% ties. Purple_alien has more
nonzero predictions, so we may see actual spread.

## Analysis protocol
1. Copy purple_alien calibration prediction frames to repo data directory
2. Run score_hydranet() for each violence type with eval_start=2017, eval_end=2020
3. Report: cell-month count, tie rate, factor-of-two subset size, reversal rates
4. Compare against bright_starship state-based results above
5. Decide whether per-type HydraNet extension is viable

## Decision criteria
- If all three violence types show reversal rates >90% in the factor-of-two subset:
  the per-type extension works, update the paper accordingly.
- If non-state or one-sided still have >90% ties: the model doesn't produce useful
  predictions for those types, and the paper should keep state-based-only framing.
- If reversal rates differ substantially across types: report the gradient, analogous
  to the per-type synthetic comparison.
