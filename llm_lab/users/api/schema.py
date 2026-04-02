from datetime import datetime

from django.urls import reverse
from ninja import ModelSchema
from ninja import Schema

from llm_lab.users.models import User


class UpdateUserSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["name"]


class UserSchema(ModelSchema):
    url: str

    class Meta:
        model = User
        fields = ["email", "name"]

    @staticmethod
    def resolve_url(obj: User):
        return reverse("api:retrieve_user", kwargs={"pk": obj.pk})


class ApiTokenSchema(Schema):
    key_preview: str
    created_at: datetime


class ApiTokenCreatedSchema(Schema):
    key: str
    created_at: datetime
