# Structural intelligence V5.1 foundation

Build with go build -o realmproof-source-parser tools/sourceparser/main.go and install the binary on PATH. The standard Go AST parser inspects compatible Gno syntax without executing source. It is not the native Gno parser, does not resolve types or validate Gno-specific syntax, and reports syntax errors rather than guessing. Analysis is per selected file, optional when the binary is absent, bounded to 1 MiB and a three-second subprocess timeout. Deployment packaging and native Gno compatibility remain pending.
