# Native test catalog

Reference: https://github.com/gnolang/gno. Reads administrator-installed source via GNOROOT. No source vendored. Discovery is heuristic, capped at 20,000 entries; not execution or coverage. Go host tests and VM filetests need dedicated runners. Do not expose arbitrary uploaded code to the web process. Current ledger lab is a separate trusted runner.
