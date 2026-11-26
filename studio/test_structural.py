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
