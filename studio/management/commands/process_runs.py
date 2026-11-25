from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from studio.models import TestRun
from studio.views import complete_local_run

class Command(BaseCommand):
    help = "Process bounded queued trusted Gno scenarios. Run one worker with SQLite."

    def handle(self, *args, **options):
        for _ in range(20):
            with transaction.atomic():
                query = TestRun.objects.filter(status="pending", execution_status="queued").order_by("started_at")
                if connection.features.has_select_for_update_skip_locked:
                    query = query.select_for_update(skip_locked=True)
                else:
                    query = query.select_for_update()
                run = query.first()
                if run is None:
                    return
                run.execution_status = "local_running"
                run.save(update_fields=["execution_status"])
            complete_local_run(run)
            self.stdout.write(f"{run.pk}: {run.status}")
