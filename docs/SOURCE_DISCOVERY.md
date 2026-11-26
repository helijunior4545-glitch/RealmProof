# Source Discovery V5.0 foundation

The service accepts a complete mapping of relative .gno paths to UTF-8 text. It never writes or executes uploaded code. Snapshots are scoped to projects, content-addressed, deduplicated and limited to 100 files, 1 MiB and 20 distinct snapshots per project. Compare reports added, removed and modified paths. This is an internal service foundation; browser import, explorer, audit events, organization-wide quotas and structural parsing are not yet implemented. Database-level immutability is not enforced.
