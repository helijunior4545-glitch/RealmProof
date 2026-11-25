from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import SimpleTestCase
from .native_catalog import inventory, summarize
class NativeCatalogTests(SimpleTestCase):
    def test_discovery_and_runtime_separation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "examples/demo"
            folder.mkdir(parents=True)
            (folder/"demo_test.gno").write_text("func TestTransfer(t *testing.T) {}")
            (folder/"host_test.go").write_text("func TestHost(t *testing.T) {}")
            (folder/"demo.gno").write_text("func TestNotATestFile() {}")
            rows, truncated = inventory(root)
            self.assertFalse(truncated)
            self.assertEqual(summarize(rows)["kinds"], {"gno":1,"go":1})
            self.assertEqual(summarize(rows)["packages"],1)
