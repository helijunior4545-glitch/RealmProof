from django.test import SimpleTestCase, TestCase
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth import get_user_model
from .models import Organization, Project, Membership
from .source_discovery import inventory, capture, compare

class InventoryTests(SimpleTestCase):
    def test_order_independent(self):
        self.assertEqual(inventory({"a.gno":"a","b.gno":"b"})[0], inventory({"b.gno":"b","a.gno":"a"})[0])

    def test_invalid_paths(self):
        for path in ("../a.gno", "/a.gno", "a\\b.gno", "a.py", "a//b.gno"):
            with self.subTest(path=path), self.assertRaises(ValidationError):
                inventory({path:"package a"})

    def test_size(self):
        with self.assertRaises(ValidationError):
            inventory({"a.gno":"x" * (1024*1024+1)})

class CaptureTests(TestCase):
    def test_scope_and_diff(self):
        user = get_user_model().objects.create_user(username="source")
        org = Organization.objects.create(name="A", slug="a")
        other = Organization.objects.create(name="B", slug="b")
        member = Membership.objects.create(organization=org, user=user, role="editor")
        project = Project.objects.create(organization=org, name="A")
        foreign = Project.objects.create(organization=other, name="B")
        first, created = capture(member, project.pk, {"a.gno":"a","b.gno":"b"})
        self.assertTrue(created)
        self.assertEqual(capture(member, project.pk, {"a.gno":"a","b.gno":"b"}), (first, False))
        second, _ = capture(member, project.pk, {"a.gno":"c","c.gno":"c"})
        self.assertEqual(compare(first, second), {"added":["c.gno"],"removed":["b.gno"],"modified":["a.gno"]})
        with self.assertRaises(Project.DoesNotExist):
            capture(member, foreign.pk, {"a.gno":"a"})
        member.role = "viewer"
        member.save()
        with self.assertRaises(PermissionDenied):
            capture(member, project.pk, {"a.gno":"a"})
