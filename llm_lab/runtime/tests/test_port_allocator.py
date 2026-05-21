"""Tests for port allocation logic."""

import pytest

from llm_lab.runtime.models import PortAllocation
from llm_lab.runtime.services.port_allocator import allocate_pair
from llm_lab.runtime.services.port_allocator import release
from llm_lab.runtime.tests.factories import ContainerInstanceFactory


@pytest.fixture(autouse=True)
def _no_docker_bound(monkeypatch):
    """Stub out the docker-daemon port view so unit tests don't interact
    with whatever real containers happen to be running on the host."""
    monkeypatch.setattr(
        "llm_lab.runtime.services.port_allocator.docker_manager.list_bound_host_ports",
        lambda: set(),
    )


@pytest.mark.django_db
def test_allocate_first_pair():
    """First allocation should return a matching backend/frontend pair."""
    PortAllocation.objects.all().delete()
    backend, frontend = allocate_pair()
    assert frontend - backend == 3000
    assert PortAllocation.objects.filter(
        backend_port=backend,
        frontend_port=frontend,
    ).exists()


@pytest.mark.django_db
def test_allocate_second_pair_increments():
    """Second allocation should increment both ports."""
    PortAllocation.objects.all().delete()
    first_backend, first_frontend = allocate_pair()
    backend, frontend = allocate_pair()
    assert backend == first_backend + 1
    assert frontend == first_frontend + 1


@pytest.mark.django_db
def test_allocate_respects_existing_db_rows():
    """Allocation skips ports already recorded in the DB."""
    PortAllocation.objects.all().delete()
    first_backend, first_frontend = allocate_pair()
    PortAllocation.objects.all().delete()
    PortAllocation.objects.create(
        backend_port=first_backend,
        frontend_port=first_frontend,
    )
    backend, frontend = allocate_pair()
    assert backend == first_backend + 1
    assert frontend == first_frontend + 1


@pytest.mark.django_db
def test_release_removes_allocation():
    """release() should delete the PortAllocation row."""
    PortAllocation.objects.all().delete()
    container = ContainerInstanceFactory(backend_port=5001, frontend_port=8001)
    alloc = PortAllocation.objects.create(
        backend_port=5001,
        frontend_port=8001,
        container=container,
    )
    assert alloc.pk is not None
    release(container)
    assert not PortAllocation.objects.filter(pk=alloc.pk).exists()
