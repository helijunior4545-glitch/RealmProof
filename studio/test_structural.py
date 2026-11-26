import shutil
from unittest import skipUnless
from django.test import SimpleTestCase
from .structural import analyze

@skipUnless(shutil.which("realmproof-source-parser"), "Optional parser not installed")
class StructuralTests(SimpleTestCase):
    def test_declarations(self):
        result = analyze("package ledger\n// func Fake() {}\nvar balance int\nfunc Balance() int { return balance }\nfunc Deposit(amount int) { balance += amount }")
        self.assertEqual(result["status"], "parsed")
        self.assertEqual(result["package"], "ledger")
        self.assertEqual([s["name"] for s in result["symbols"]], ["balance", "Balance", "Deposit"])
        self.assertEqual([s["public"] for s in result["symbols"]], [False, True, True])
        self.assertIn("amount int", result["symbols"][2]["signature"])

    def test_invalid_syntax(self):
        self.assertEqual(analyze("package ledger\nfunc Broken(")["status"], "syntax_error")

    def test_call_candidates(self):
        result = analyze('package ledger\nimport "fmt"\nfunc A() { B(); fmt.Println("x"); f := func(){ Hidden() }; f() }\nfunc B() {}')
        self.assertEqual(result["status"], "parsed")
        self.assertEqual([(c["caller"], c["target"], c["kind"]) for c in result["calls"]], [("A", "B", "identifier"), ("A", "fmt.Println", "selector"), ("A", "f", "identifier")])
        self.assertFalse(result["calls_truncated"])

    def test_call_limit(self):
        result = analyze("package ledger\nfunc A() {" + "B();" * 2001 + "}")
        self.assertEqual(len(result["calls"]), 2000)
        self.assertTrue(result["calls_truncated"])

    def test_risk_indicators(self):
        result = analyze('package ledger\nfunc A(x int, a []int) { x += 1; x = x / 2; x = a[x]; x = x * 2; panic("x") }')
        self.assertEqual([i["rule"] for i in result["indicators"]], ["compound_update", "divisor_boundary", "index_boundary", "arithmetic_boundary", "panic_candidate"])
        self.assertTrue(all(i["function"] == "A" and i["line"] == 2 for i in result["indicators"]))

    def test_risk_comments_and_limit(self):
        result = analyze('package ledger\nfunc A() { // panic("x")\n _ = "x / 0" }')
        self.assertEqual(result["indicators"], [])
        result = analyze("package ledger\nfunc A() {" + "x+=1;" * 501 + "}")
        self.assertEqual(len(result["indicators"]), 500)
        self.assertTrue(result["indicators_truncated"])
