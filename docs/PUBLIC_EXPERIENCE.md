# Public experience — editorial verification narrative

The public homepage uses an editorial, non-card layout. The hero schematizes source → declared intent → evidence. The interactive inspector is **explicitly browser-only**, not a Gno execution or chain-verified proof. Its deterministic model illustrates balance/authorization outcomes but never writes or fetches application data.

The body documents four actual disciplines: source snapshots and structural analysis, test scenario authoring, supported local Gno fixture execution, and provenance-aware evidence review. On-chain publication and arbitrary imported-contract execution remain unverified and are not advertised as operational.

UI icons are local SVG symbols in the Lucide visual language, with an attribution link to the permissively licensed open-source Lucide project. No CDN, third-party scripts or remote fonts are required. The page is keyboard navigable and respects reduced-motion settings. The existing guest form and its CSRF POST action are preserved. Authenticated visitors see an "Open studio" action. Guest provisioning remains opt-in and deployment-controlled; the page does not bypass tenant authorization or enable public execution by itself.

The last CI run before this design showed Docker and Django success, but a Chromium assertion for the delayed POST feedback failed. The visual test must be repaired independently on evidence; passing unrelated suites does not imply that acceptance has passed.
