"""Sync database :class:`ScaffoldingTemplate` rows from on-disk file-tree templates.

Run after adding or removing templates under ``llm_lab/runtime/scaffolding/``.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from llm_lab.generation.models import ScaffoldingTemplate
from llm_lab.runtime.services.scaffolding_engine import available_templates
from llm_lab.runtime.services.scaffolding_engine import load_template


class Command(BaseCommand):
    help = "Create/update ScaffoldingTemplate rows from discovered on-disk templates."

    def handle(self, *args: object, **options: object) -> None:  # noqa: ARG002
        slugs = available_templates()
        for slug in slugs:
            manifest = load_template(slug)
            tech_stack: dict[str, str] = {}
            if manifest.backend:
                tech_stack["backend"] = manifest.backend.get("language", "python")
            if manifest.frontend:
                tech_stack["frontend"] = manifest.frontend.get("framework", "")

            row, created = ScaffoldingTemplate.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": manifest.display_name,
                    "description": manifest.description or "",
                    "tech_stack": tech_stack,
                    "is_default": slug == "react-flask",
                },
            )
            verb = "created" if created else "updated"
            self.stdout.write(self.style.SUCCESS(f"{verb}: {slug}"))

        # Drop DB rows for templates that no longer exist on disk.
        stale = ScaffoldingTemplate.objects.exclude(slug__in=slugs)
        stale_count = stale.count()
        stale.delete()
        if stale_count:
            self.stdout.write(self.style.WARNING(f"removed {stale_count} stale template rows"))
