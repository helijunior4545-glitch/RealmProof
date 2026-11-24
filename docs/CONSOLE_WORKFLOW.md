# Console Workflow

RealmProof is an English-first, intent-driven console.

## Console screens

1. **Overview:** enter a workspace or create an organization.
2. **Project Workbench:** review scenario inventory, assertion verdict totals, pending evidence, and latest runs.
3. **Scenario Builder:** define the hypothesis in three progressive steps:
   - **Intent:** name the test, select a family, describe the desired behavior.
   - **Inputs:** specify a JSON object representing inputs and initial state.
   - **Assertions:** define the JSON fields whose observed values should match.
4. **Run:** create a frozen snapshot and an *unexecuted* run record.
5. **Evaluate:** manually supply independently collected evidence in JSON form.
6. **Investigate:** compare expected and observed values; expand technical evidence for raw source records.

## Important distinctions

- `PASSED` means an assertion comparison succeeded. It does **not** mean a transaction succeeded.
- `reverted` can be the **expected** and correct execution outcome.
- `User supplied · unverified` is deliberately different from on-chain verified evidence.
- The current Studio **does not submit Gno transactions**. The separately authored Gno evidence registry also does not automatically prove contract behavior.
- Example presets assist with input authoring, not contract execution.

## Visual language

Colors are intentionally semantic: violet = primary navigation/action, green = assertion match, red = mismatch, amber = awaiting or unverified, blue = informational. Everything is built on a dark developer-console palette, but the visual language is original to RealmProof, not a reproduction of a third-party UI.

## Accessibility and resilience

The scenario builder progressively enhances a normal server-rendered Django form. Without JavaScript, every field remains visible and submittable. With JavaScript, each step validates its visible controls, including JSON object syntax, before advancing. Server-side Django validation remains authoritative. The UI supports keyboard navigation, status labels, responsive layouts, and reduced motion.
