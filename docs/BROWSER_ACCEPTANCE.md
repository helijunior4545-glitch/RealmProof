# Browser acceptance

CI uses Playwright and Chromium with disposable SQLite and isolated guest mode.
The checks open the transfer project from the public entry, verify that separate
visitors cannot access each other's projects, check the old test link, and
exercise keyboard navigation and the native entry button without JavaScript.
Screenshots cover 320, 768, and 1366 pixel widths.

The browser job checks navigation and the prepared scenario actions. Use the
local Gno runtime to verify scenario execution end to end.
