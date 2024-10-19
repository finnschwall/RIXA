import os
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from rixaplugin import _memory
from django.conf import settings
import pandas as pd
from django.db.models.signals import post_save, post_delete
from rixaplugin.internal.networking import create_keys
import logging

database_log = logging.getLogger("rixa.database")


def generate_default_plugins():
    return list([ _memory.plugins[i]["name"] for i in _memory.plugins])


def generate_default_document_tags():
    if not settings.KNOWLEDGE_DB_LOC:
        return []
    try:
        doc_metadata_db = pd.read_pickle(settings.KNOWLEDGE_DB_LOC + "/doc_metadata_df.pkl")
        return list(doc_metadata_db["tags"].explode().unique().tolist())
    except Exception as e:
        return []


class PluginScope(models.Model):
    """
    Scopes are used to control which chat scopes can access which plugins.
    E.g. the private plugin of user A can be made accessible to user B by adding B to the scope to which As plugin belongs.
    """
    name = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        from dashboard.views import latest_time
        if self.name == 'server' or self.name == 'client':
            raise ValidationError("This name is not allowed.")
        create_keys(self.name, metadata={"scope": self.name, "for": settings.PRIMARY_URL,
                                         "server_version_timestamp": datetime.fromtimestamp(latest_time).strftime(
                                             '%Y-%m-%d %H:%M:%S')})
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # if self.name == 'server' or self.name == 'client':
        #     raise ValidationError("This name is not allowed.")
        if not os.path.exists(os.path.join(settings.AUTH_KEY_LOC, self.name)):
            database_log.error(f"Key directory for scope {self.name} does not exist.")
        else:
            os.rmdir(os.path.join(settings.AUTH_KEY_LOC, self.name))
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class ChatConfiguration(models.Model):
    """
    A chat configuration defines the behavior of a chat.
    """
    name = models.CharField(max_length=100, unique=True)
    # tags = models.ManyToManyField(SelectionTag)
    available_to_all = models.BooleanField(default=False)
    chat_title = models.CharField(max_length=70, blank=True)
    system_message = models.TextField(blank=True)
    first_message = models.TextField(blank=True)
    included_scopes = models.ManyToManyField(PluginScope, blank=True)
    use_function_calls = models.BooleanField(default=False)
    included_plugins = models.JSONField(default=generate_default_plugins, blank=True)
    use_document_retrieval = models.BooleanField(default=False)
    document_tags = models.JSONField(default=generate_default_document_tags, blank=True)

    def delete(self, *args, **kwargs):
        if self.name == 'default':
            raise ValidationError("This configuration cannot be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name
