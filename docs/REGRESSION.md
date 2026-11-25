# Regression queue
Queue trusted transfer scenarios from a project, then run `python manage.py process_runs` in a separate process with Gno installed. PostgreSQL uses skip-locked claims. SQLite requires one worker. No automatic crash recovery or OS sandbox is provided. Evidence export is membership scoped and limited to 200 runs.
