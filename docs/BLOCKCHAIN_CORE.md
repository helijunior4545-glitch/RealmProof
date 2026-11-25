# Blockchain Core

The authenticated workspace network explorer queries pinned Onyx and mainnet RPC endpoints. It rejects custom networks, redirects and mismatched chain identity. No wallet secrets or broadcasts are accepted. RPC claims are not consensus proofs.

Install the compatible Gno CLI following https://docs.gno.land/builders/installation/ and run `python manage.py check_gno --settings=realmproof.settings_local` to validate network identity and all six trusted Gno transfer cases. Arbitrary tenant code is not supported. CLI discovery alone does not prove compatibility.

Network reference: https://docs.gno.land/resources/gnoland-networks/

No deployment is claimed by this change.
