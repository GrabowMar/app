"""Delete every scaffolded-app artifact: DB rows, docker objects, build dirs.

Usage::

    python manage.py purge_app_containers          # interactive confirmation
    python manage.py purge_app_containers --yes    # no prompt
"""

from __future__ import annotations

import shutil
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management.base import CommandParser

from llm_lab.runtime.models import ContainerAction
from llm_lab.runtime.models import ContainerInstance
from llm_lab.runtime.models import PortAllocation
from llm_lab.runtime.services import docker_manager


class Command(BaseCommand):
    help = "Stop+remove every llm- container, delete llm-job-* images, wipe DB rows and /tmp/build_*."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--yes", action="store_true", help="Skip confirmation.")

    def handle(self, *args: object, **options: object) -> None:  # noqa: ARG002
        if not options.get("yes"):
            answer = input(
                "This will destroy ALL scaffolded apps, containers, images and build dirs. "
                "Continue? [y/N]: ",
            ).strip().lower()
            if answer != "y":
                self.stdout.write("Aborted.")
                return

        client = docker_manager.client()
        if client is not None:
            removed = 0
            for ctr in client.containers.list(all=True):
                if ctr.name.startswith("llm-"):
                    try:
                        ctr.remove(force=True)
                        removed += 1
                    except Exception as exc:  # noqa: BLE001
                        self.stderr.write(f"  ! could not remove {ctr.name}: {exc}")
            self.stdout.write(self.style.SUCCESS(f"docker: removed {removed} containers"))

            img_removed = 0
            for img in client.images.list():
                for tag in img.tags:
                    if tag.startswith("llm-job-"):
                        try:
                            client.images.remove(image=tag, force=True)
                            img_removed += 1
                        except Exception as exc:  # noqa: BLE001
                            self.stderr.write(f"  ! could not remove image {tag}: {exc}")
                        break
            self.stdout.write(self.style.SUCCESS(f"docker: removed {img_removed} images"))
        else:
            self.stderr.write("docker client unavailable; skipping container/image cleanup")

        for path in Path("/tmp").glob("build_*"):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
        self.stdout.write(self.style.SUCCESS("/tmp/build_* cleaned"))

        actions = ContainerAction.objects.all().count()
        instances = ContainerInstance.objects.all().count()
        ports = PortAllocation.objects.all().count()
        ContainerAction.objects.all().delete()
        ContainerInstance.objects.all().delete()
        PortAllocation.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"db: deleted {instances} instances, {actions} actions, {ports} port allocations",
            ),
        )
