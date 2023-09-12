from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Permission


# shows how to exemplary create new permissions to select user access
class DashboardPermissions(models.Model):
    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model.

        default_permissions = ()  # disable "add", "change", "delete"
        # and "view" default permissions

        permissions = (
            ('request_GPU', 'Is user allowed to request GPU intensive resources'),
        )


class User(AbstractUser):
    pass

