from collections import Counter
from django.test import SimpleTestCase
from . import regression

class RegressionTests(SimpleTestCase):
    def test_selection(self):
        cases = regression.cases()
        self.assertEqual(len(cases), 300)
        self.assertEqual(Counter(c["input"]["category"] for c in cases),
                         {k: v//2 for k,v in regression.GROUPS.items()})

    def test_harness(self):
        case = regression.cases()[0]
        self.assertEqual(regression.harness_for([case]).count("fmt.Println"), len(case["input"]["operations"])+1)

    def test_parse(self):
        case = regression.cases()[0]
        output = "\n".join(f"RP_TRACE {case['id']} {j} true 5 0 0" for j in range(len(case["input"]["operations"])+1))
        self.assertEqual(regression.parse_output(output, [case])[case["id"]][0]["available"], 5)

    def test_missing_trace(self):
        with self.assertRaises(RuntimeError):
            regression.parse_output("", regression.cases()[:1])

    def test_difference(self):
        case = regression.cases()[0]
        old = [{"accepted": True, "available": 5}]
        new = [{"accepted": False, "available": 5}]
        result = regression.compare(case, old, new, {})
        self.assertEqual(result["verdict"], "failed")
        self.assertEqual(result["evidence"]["differences"], [{"step": 0, "fields": ["accepted"]}])

    def test_unchanged(self):
        case = regression.cases()[0]
        trace = [{"accepted": True, "available": 5}]
        self.assertEqual(regression.compare(case, trace, trace, {})["verdict"], "passed")
