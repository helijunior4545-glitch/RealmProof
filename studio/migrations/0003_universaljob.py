import django.db.models.deletion
import studio.models
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("studio", "0002_align_model_fields"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="UniversalJob", fields=[
            ("id", models.UUIDField(primary_key=True, default=studio.models.uid, editable=False, serialize=False)),
            ("suite", models.CharField(max_length=40)),
            ("status", models.CharField(max_length=16, default="queued")),
            ("token", models.UUIDField(null=True, editable=False)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("started_at", models.DateTimeField(null=True)),
            ("finished_at", models.DateTimeField(null=True)),
            ("result", models.JSONField(default=dict, blank=True)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="studio.organization")),
            ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        ], options={"indexes": [models.Index(fields=["status", "created_at"], name="rp_job_queue_idx")],
                    "constraints": [models.CheckConstraint(condition=models.Q(status__in=["queued", "running", "completed", "error"]), name="rp_job_valid_status"),
                                    models.UniqueConstraint(fields=["organization"], condition=models.Q(status="running"), name="rp_job_one_running")]}),
    ]
