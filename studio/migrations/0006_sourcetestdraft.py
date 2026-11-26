from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import studio.models

class Migration(migrations.Migration):
    dependencies = [("studio", "0005_sourcesnapshot"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="SourceTestDraft", fields=[
            ("id", models.UUIDField(primary_key=True, default=studio.models.uid, editable=False, serialize=False)),
            ("path", models.CharField(max_length=240)),
            ("source_digest", models.CharField(max_length=64)),
            ("proposal_key", models.CharField(max_length=64)),
            ("proposal", models.JSONField()),
            ("expected", models.JSONField()),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("snapshot", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="test_drafts", to="studio.sourcesnapshot")),
            ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        ], options={"constraints": [models.UniqueConstraint(fields=("snapshot", "path", "proposal_key"), name="rp_unique_source_draft")]}),
    ]
