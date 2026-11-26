"""Deterministic review suggestions, never executable tests or inferred verdicts."""

RULES = {
    "arithmetic_boundary": ("boundary", "Exercise numeric limits", "Select zero, minimum, maximum and adjacent values appropriate to the operand types.", "Confirm arithmetic results and invariants against the intended numeric policy."),
    "divisor_boundary": ("negative", "Exercise divisor boundaries", "Where controllable, try zero and nonzero divisors, including signed boundaries.", "Confirm the intended rejection or error behavior and absence of unintended state changes."),
    "compound_update": ("state", "Exercise state transitions", "Identify the updated value and compare before and after valid and invalid operations.", "Confirm the intended delta and preservation of unrelated state."),
    "index_boundary": ("boundary", "Exercise indexing boundaries", "Determine the operand type; try empty collections, missing keys or boundary indices as applicable.", "Confirm the intended lookup or failure behavior."),
    "panic_candidate": ("negative", "Exercise failure paths", "Resolve the call target and identify inputs reaching the failure path.", "Confirm intended error behavior and state preservation."),
}

def recommend(structure):
    if structure.get("status") != "parsed" or "indicators" not in structure:
        return {"status": "unavailable", "items": [], "partial": True}
    items = []
    seen = set()
    partial = bool(structure.get("indicators_truncated"))
    for indicator in structure["indicators"]:
        rule = indicator["rule"]
        if rule not in RULES:
            partial = True
            continue
        key = (rule, indicator["function"], indicator["line"])
        if key in seen:
            continue
        seen.add(key)
        if len(items) >= 100:
            partial = True
            break
        family, title, inputs, oracle = RULES[rule]
        items.append({"rule": rule, "function": key[1], "line": key[2],
                      "family": family, "title": title, "inputs": inputs,
                      "oracle": oracle, "status": "proposed",
                      "expected": None})
    return {"status": "proposed", "items": items, "partial": partial}
