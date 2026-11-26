from django.db import migrations, models
import django.db.models.deletion
import studio.models

class Migration(migrations.Migration):
    dependencies = [("studio", "0004_job_cancelled")]
    operations = [
        migrations.CreateModel(name="SourceSnapshot", fields=[
            ("id", models.UUIDField(primary_key=True, default=studio.models.uid, editable=False, serialize=False)),
            ("digest", models.CharField(max_length=64)),
            ("files", models.JSONField()),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="source_snapshots", to="studio.project")),
        ], options={"constraints": [models.UniqueConstraint(fields=("project", "digest"), name="rp_source_unique_digest")]}),
    ]
