# Native Gno transaction inspection

Uses the official Gno RPC protocol rather than importing an EVM engine. Reference: https://github.com/gnolang/gno (v1.8.0). No upstream source copied. Block and receipt schema based on observed Onyx responses. Supply a transaction hash and block height when tx indexing is disabled. Hash matching is not a consensus proof. Package activation and availability remain separate, unverified states. All queries are read-only.
