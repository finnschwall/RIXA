from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Permission
from django.conf import settings
from django.utils.crypto import get_random_string

from dashboard.models import PluginScope, ChatConfiguration
from django.utils import timezone

# class UserTag(models.Model):
#     name = models.CharField(max_length=100, unique=True)


class Invitation(models.Model):
    code = models.CharField(max_length=20, unique=True, blank=True, primary_key=True)
    name = models.CharField(max_length=100, blank=True)
    max_uses = models.PositiveIntegerField(default=10)
    uses = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # tags = models.ManyToManyField(UserTag, blank=True)
    configuration_write = models.ManyToManyField(ChatConfiguration, related_name="invitation_configuration_write", blank=True)
    configurations_read = models.ManyToManyField(ChatConfiguration, related_name="invitation_configurations_read", blank=True)
    scope_write = models.ManyToManyField(PluginScope, related_name="invitation_scope_write", blank=True)
    scope_read = models.ManyToManyField(PluginScope, related_name="invitation_scope_read", blank=True)

    url = models.URLField(blank=True)

    def __str__(self):
        return f"Invitation {self.code}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = get_random_string(20)
        self.url = settings.PRIMARY_URL + "/account_management/signup/?registration_id=" + str(self.code)
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        return self.uses < self.max_uses


class User(AbstractUser):
    pass


class Message(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True,
        blank=True,)

    def is_expired(self):
        if self.expiration_date is None:
            return False
        return timezone.now() > self.expiration_date

    def __str__(self):
        return self.content[:50]

class RixaUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scope_read = models.ManyToManyField(PluginScope, related_name="scope_read", blank=True)
    scope_write = models.ManyToManyField(PluginScope, related_name="scope_write", blank=True)
    configuration_write = models.ManyToManyField(ChatConfiguration, related_name="configuration_write", blank=True)
    configurations_read = models.ManyToManyField(ChatConfiguration, related_name="configurations_read", blank=True)
    no_tracker_saving = models.BooleanField(default=False)
    # user_tags = models.ManyToManyField(UserTag, blank=True)
    total_messages = models.IntegerField(default=0)
    total_time_spent = models.IntegerField(default=0)
    messages_per_session = models.JSONField(default=None, blank=True, null=True)
    total_sessions = models.IntegerField(default=0)
    seen_messages = models.ManyToManyField(Message, related_name='seen_by', blank=True)

    def __str__(self):
        try:
            return self.user.username
        except:
            return "USER HAS NO RIXAUSER. ACTIVATE PATCH_USER_MODEL!"





