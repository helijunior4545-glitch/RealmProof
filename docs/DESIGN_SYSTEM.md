# PM2 — Design system foundation

The shared stylesheet owns the existing chromatic palette, semantic status aliases, spacing and control tokens. It is loaded last by the shared base template. Legacy page-specific styles remain intentionally intact; this is incremental consolidation, not a full rewrite.

## Contracts

- Neutral surfaces; violet primary action; cyan information/focus; green confirmed pass; red failure/error; amber pending; neutral inconclusive/cancelled.
- Status labels must remain textual. A decorative dot in the shell is neutral and does not imply service health.
- Static panels do not change border on hover. Interactive controls retain feedback.
- Preserve keyboard focus, reduced motion, bounded code overflow and mobile control sizing.
- Separate execution status, assertion verdict and evidence provenance; never use a green status to imply on-chain verification.
- Existing routes and jury flow remain unchanged.

## Acceptance

CI must render existing templates and collect the new static asset. Browser review still required at 320, 768, 1280 and 1920 CSS pixels, keyboard-only traversal, zoom, contrast, reduced motion, long file paths and JSON, and guest entry. No WCAG conformance or live deployment claim is made. PM3 will introduce a contextual source workspace using these tokens.
