from django.test import TestCase
from studio.services import evaluate

class StrictAssertionsTests(TestCase):
    def test_boolean_is_not_integer(self):
        self.assertEqual(evaluate({"x":True},{"x":1}).status,"failed")
    def test_nested_types(self):
        self.assertEqual(evaluate({"x":[{"a":1}]},{"x":[{"a":True}]}).status,"failed")
    def test_missing_null(self):
        self.assertEqual(evaluate({"x":None},{}).status,"failed")
