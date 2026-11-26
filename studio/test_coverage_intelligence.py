from django.test import SimpleTestCase
from .coverage_intelligence import summarize

def symbol(name, line=1, kind="function"):
    return {"name": name, "line": line, "kind": kind, "public": True}

def structure(symbols, proposals=(), partial=False):
    return {"status": "parsed", "symbols": symbols, "recommendations": {
        "status": "proposed", "items": [{"function": name} for name in proposals],
        "partial": partial}}

class CoverageIntelligenceTests(SimpleTestCase):
    def test_inventory_never_infers_coverage(self):
        result = summarize(structure([symbol("A"), symbol("B"), symbol("X", kind="var")], ["A", "A"]))
        self.assertEqual(result["declarations"], 2)
        self.assertEqual(result["with_proposals"], 1)
        self.assertEqual([r["proposals"] for r in result["rows"]], [2, 0])
        self.assertIsNone(result["coverage_percent"])
        self.assertTrue(all(r["evidence_status"] == "not_linked" for r in result["rows"]))

    def test_ambiguous_and_unknown_targets(self):
        result = summarize(structure([symbol("A"), symbol("A", 2, "method")], ["A", "B"]))
        self.assertEqual(result["unresolved_proposals"], 2)
        self.assertEqual(result["with_proposals"], 0)
        self.assertTrue(result["partial"])
        self.assertTrue(all(r["proposals"] is None for r in result["rows"]))

    def test_unavailable_and_empty(self):
        self.assertEqual(summarize({"status": "syntax_error"})["status"], "unavailable")
        result = summarize(structure([]))
        self.assertEqual(result["rows"], [])
        self.assertIsNone(result["coverage_percent"])

    def test_display_limit_and_partial(self):
        result = summarize(structure([symbol(str(i)) for i in range(501)]))
        self.assertEqual(result["declarations"], 501)
        self.assertEqual(len(result["rows"]), 500)
        self.assertTrue(result["partial"])
        self.assertTrue(summarize(structure([], partial=True))["partial"])
