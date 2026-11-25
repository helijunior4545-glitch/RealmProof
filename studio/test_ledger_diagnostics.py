from django.test import SimpleTestCase
from .ledger_lab import diagnostic_excerpt

class LedgerDiagnosticTests(SimpleTestCase):
    def test_root_error_survives_long_stack(self):
        output = "panic: package is immutable post-init\n" + "x" * 9000 + "\nledger.gno:12"
        excerpt = diagnostic_excerpt(output)
        self.assertIn("panic: package is immutable post-init", excerpt)
        self.assertIn("ledger.gno:12", excerpt)
        self.assertLessEqual(len(excerpt), 1400)

    def test_short_output_is_unchanged(self):
        self.assertEqual(diagnostic_excerpt("error"), "error")
