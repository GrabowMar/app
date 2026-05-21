"""Add ContainerInstance.subdomain and backfill from generation_job UUIDs."""

from __future__ import annotations

from django.db import migrations
from django.db import models


def _backfill(apps, schema_editor):
    ContainerInstance = apps.get_model("runtime", "ContainerInstance")
    used: set[str] = set()
    qs = ContainerInstance.objects.all().order_by("created_at")
    for inst in qs.iterator():
        job = inst.generation_job
        hexstr = job.id.hex if job else inst.id.hex
        for n in range(8, 13):
            candidate = hexstr[:n]
            if candidate not in used:
                used.add(candidate)
                inst.subdomain = candidate
                inst.save(update_fields=["subdomain"])
                break


def _noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("runtime", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="containerinstance",
            name="subdomain",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text=(
                    "Stable URL slug used for /app/<subdomain>/ proxy routing."
                ),
                max_length=12,
                null=True,
                unique=True,
                verbose_name="subdomain",
            ),
        ),
        migrations.RunPython(_backfill, _noop_reverse),
    ]
