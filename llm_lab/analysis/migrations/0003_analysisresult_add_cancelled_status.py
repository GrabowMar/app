from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analysis", "0002_add_query_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="analysisresult",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("running", "Running"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                    ("skipped", "Skipped"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
