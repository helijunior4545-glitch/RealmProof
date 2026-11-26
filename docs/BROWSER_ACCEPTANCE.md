# PM6.3 — Browser acceptance foundation

CI installs pinned Playwright and Chromium in a separate job using disposable local SQLite settings and isolated guest mode. Tests exercise actual navigation, delayed native POST feedback, duplicate submit suppression, two independent browser contexts, cross-tenant rejection, no-JavaScript launch, keyboard skip navigation and landing widths 320/768/1280/1920. Screenshots and server logs are CI artifacts. No production credentials or deployment are used.

The guided first-test banner now appears for isolated guests as well as the legacy demo account. Browser tests do not execute Gno, certify accessibility, cover all routes, verify production HTTPS or test other browser engines. Reduced-motion preference is enabled in responsive checks but animation suppression is not independently asserted. CI results must be reviewed before claiming acceptance.
