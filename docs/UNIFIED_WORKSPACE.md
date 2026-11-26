# PM3 — Source workspace and request feedback

The existing source route now presents snapshot/file navigation, source and contextual static intelligence in separate responsive regions. All prior inventory and analysis sections remain available. No imported code execution or browser intent confirmation is introduced.

Native same-window POST forms receive delayed (180 ms) request feedback and a per-form duplicate-submit guard. Submitter name/value and native validation are preserved; cancelled submit events and restored pages reset the state. This is not server idempotency, progress reporting or a guarantee of completion. GET links and asynchronous monitor refresh are unchanged. No automatic retry.

Browser acceptance pending: named suite buttons, invalid JSON, keyboard submit, slow response, back/forward cache, no JavaScript, reduced motion, mobile layout and long paths. CI does not establish browser behavior.
