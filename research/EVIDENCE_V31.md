# V31 — Methodological Audit

The initial V31 run `36787649896` is **discarded**.

Reason: the test continuation and its A/B reference continuations used the same rotation angle. Consequently, each test condition was effectively compared against itself, producing 100% identity across the table.

No scientific inference is retained from that run.

A corrected V31 implementation has been committed. It compares rotated test states (30°, 90°, 150°) against the unrotated local A/B reference pair inside the same donor-independent receiver context.

The corrected run is the only version that should be interpreted.