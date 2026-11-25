from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("studio", "0003_universaljob")]
    operations = [
        migrations.RemoveConstraint(model_name="universaljob", name="rp_job_valid_status"),
        migrations.AddConstraint(model_name="universaljob", constraint=models.CheckConstraint(condition=models.Q(status__in=["queued", "running", "completed", "error", "cancelled"]), name="rp_job_valid_status")),
    ]
