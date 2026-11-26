"""Inventory review gaps without claiming runtime coverage."""

def summarize(structure):
    if structure.get("status") != "parsed":
        return {"status": "unavailable", "coverage_percent": None}
    functions = [s for s in structure["symbols"] if s["kind"] in ("function", "method")]
    by_name = {}
    for symbol in functions:
        by_name.setdefault(symbol["name"], []).append(symbol)
    recommendations = structure.get("recommendations", {})
    counts = {}
    unresolved = 0
    for proposal in recommendations.get("items", []):
        name = proposal["function"]
        if len(by_name.get(name, [])) != 1:
            unresolved += 1
            continue
        counts[name] = counts.get(name, 0) + 1
    rows = []
    for symbol in functions[:500]:
        name = symbol["name"]
        ambiguous = len(by_name[name]) != 1
        count = None if ambiguous else counts.get(name, 0)
        rows.append({"name": name, "line": symbol["line"], "kind": symbol["kind"],
                     "public": symbol["public"], "proposals": count,
                     "review_status": "ambiguous" if ambiguous else ("proposed" if count else "no_proposal"),
                     "evidence_status": "not_linked"})
    return {"status": "inventory_only", "coverage_percent": None,
            "declarations": len(functions), "rows": rows,
            "with_proposals": len(counts),
            "unresolved_proposals": unresolved,
            "partial": len(functions) > 500 or bool(unresolved) or
                       recommendations.get("status") != "proposed" or
                       bool(recommendations.get("partial"))}
