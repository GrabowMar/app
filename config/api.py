from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI
from ninja.security import SessionAuth

api = NinjaAPI(
    urls_namespace="api",
    auth=SessionAuth(),
    docs_decorator=staff_member_required,
)

api.add_router("/users/", "llm_lab.users.api.views.router")
api.add_router("/models/", "llm_lab.llm_models.api.views.router")
api.add_router("/generation/", "llm_lab.generation.api.views.router")
api.add_router("/analysis/", "llm_lab.analysis.api.views.router")
api.add_router("/statistics/", "llm_lab.statistics.api.views.router")
api.add_router("/rankings/", "llm_lab.rankings.api.views.router")
api.add_router("/reports/", "llm_lab.reports.api.views.router")
