# V36 Audit Note

V36 run #1 (GitHub Actions run 36791264668) completed successfully, but post-run inspection found an indexing error in the bootstrap resampling code.

The permutation null was correctly constructed at the history-seed block level and is not affected by this bug. The reported observed contrasts and permutation p-values are therefore retained as descriptive/null-test outputs.

The bootstrap interval was invalid because the implementation sampled indices from the first history-seed row repeatedly rather than resampling within every row/stratum.

Correction committed in 2b7e7c35467c5d044e88903c66a7b42844f72576. GitHub Actions run #2 is the corrected execution.

Policy for the evidence record:
- run #1 bootstrap intervals are superseded;
- run #1 permutation results remain reproducible but are not the final V36 evidence;
- corrected run #2 must be used for all confidence intervals;
- no scientific conclusion is based on the invalid interval.

This audit preserves the failed methodological branch instead of silently replacing it.
