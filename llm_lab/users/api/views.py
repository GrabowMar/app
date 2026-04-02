from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from ninja import Router

from llm_lab.users.api.schema import ApiTokenCreatedSchema
from llm_lab.users.api.schema import ApiTokenSchema
from llm_lab.users.api.schema import UpdateUserSchema
from llm_lab.users.api.schema import UserSchema
from llm_lab.users.models import ApiToken
from llm_lab.users.models import User

router = Router(tags=["users"])


def _get_users_queryset(request) -> QuerySet[User]:
    return User.objects.filter(pk=request.user.pk)


@router.get("/", response=list[UserSchema])
def list_users(request):
    return _get_users_queryset(request)


@router.get("/me/", response=UserSchema)
def retrieve_current_user(request):
    return request.user


@router.get("/{pk}/", response=UserSchema)
def retrieve_user(request, pk: int):
    users_qs = _get_users_queryset(request)
    return get_object_or_404(users_qs, pk=pk)


@router.patch("/me/", response=UserSchema)
def update_current_user(request, data: UpdateUserSchema):
    user = request.user
    user.name = data.name
    user.save()
    return user


@router.patch("/{pk}/", response=UserSchema)
def update_user(request, pk: int, data: UpdateUserSchema):
    users_qs = _get_users_queryset(request)
    user = get_object_or_404(users_qs, pk=pk)
    user.name = data.name
    user.save()
    return user


@router.get("/me/token/", response={200: ApiTokenSchema, 404: dict})
def get_api_token(request):
    """Check if user has an API token."""
    try:
        token = request.user.api_token
        return 200, {
            "key_preview": f"...{token.key[-8:]}",
            "created_at": token.created_at,
        }
    except ApiToken.DoesNotExist:
        return 404, {"detail": "No API token found"}


@router.post("/me/token/", response={201: ApiTokenCreatedSchema})
def create_api_token(request):
    """Generate a new API token. Revokes existing token if any."""
    ApiToken.objects.filter(user=request.user).delete()
    key = ApiToken.generate_key()
    token = ApiToken.objects.create(user=request.user, key=key)
    return 201, {"key": key, "created_at": token.created_at}


@router.delete("/me/token/", response={204: None})
def revoke_api_token(request):
    """Revoke the user's API token."""
    ApiToken.objects.filter(user=request.user).delete()
    return 204, None
