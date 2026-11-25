from django.test import TestCase, SimpleTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch
from datetime import timedelta
from .models import Organization, Membership, UniversalJob, AuditEvent
from .universal_queue import enqueue, claim, finish, expire, process_one, QuotaExceeded, error_result
from .failure_intelligence import classify

class QueueTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Queue", slug="queue")
        self.user = get_user_model().objects.create_user(username="queue-user")
        self.member = Membership.objects.create(organization=self.org, user=self.user, role="editor")

    def test_active_quota(self):
        for _ in range(4):
            UniversalJob.objects.create(organization=self.org, actor=self.user, suite="ledger-v1")
        with self.assertRaises(QuotaExceeded):
            enqueue(self.member, "ledger-v1")

    def test_duplicate_active_request(self):
        first = enqueue(self.member, "ledger-v1")
        self.assertEqual(enqueue(self.member, "ledger-v1").pk, first.pk)
        self.assertEqual(UniversalJob.objects.count(), 1)

    def test_cancel_queued_only(self):
        from .universal_queue import cancel
        job = enqueue(self.member, "ledger-v1")
        self.assertTrue(cancel(self.member, job.pk))
        job.refresh_from_db()
        self.assertEqual(job.status, "cancelled")
        self.assertIsNone(claim())
        job = enqueue(self.member, "ledger-v1")
        claim()
        self.assertFalse(cancel(self.member, job.pk))

    def test_one_running_per_org(self):
        enqueue(self.member, "ledger-v1")
        enqueue(self.member, "transfer-v1")
        self.assertIsNotNone(claim())
        self.assertIsNone(claim())

    def test_finish_is_fenced(self):
        enqueue(self.member, "ledger-v1")
        job = claim()
        self.assertTrue(finish(job.pk, job.token, error_result("timeout")))
        self.assertFalse(finish(job.pk, job.token, error_result("timeout")))
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_expired_worker(self):
        enqueue(self.member, "ledger-v1")
        job = claim()
        UniversalJob.objects.filter(pk=job.pk).update(started_at=timezone.now()-timedelta(minutes=11))
        expire()
        job.refresh_from_db()
        self.assertEqual(job.status, "error")
        self.assertEqual(job.result["failure_category"], "worker_interrupted")

    @patch("studio.universal_queue.execute")
    def test_revoked_member(self, run):
        job = enqueue(self.member, "ledger-v1")
        self.member.delete()
        process_one()
        run.assert_not_called()
        job.refresh_from_db()
        self.assertEqual(job.result["failure_category"], "permission_error")

    def test_daily_quota(self):
        for _ in range(30):
            UniversalJob.objects.create(organization=self.org, actor=self.user, suite="ledger-v1", status="completed")
        with self.assertRaises(QuotaExceeded):
            enqueue(self.member, "ledger-v1")

class ClassificationTests(SimpleTestCase):
    def test_immutable_package(self):
        self.assertEqual(classify(error_result("package is immutable post-init")), "immutable_package")

    def test_mismatch(self):
        self.assertEqual(classify({"execution": "completed", "verdict": "failed"}), "assertion_mismatch")
