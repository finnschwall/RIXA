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
from pyalm import ConversationTracker, ConversationRoles
from django.contrib import admin
from django import forms
database_log = logging.getLogger("rixa.database")


def generate_default_plugins():
    return list([_memory.plugins[i]["name"] for i in _memory.plugins])


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
    custom_user_settings = models.JSONField(default=dict, blank=True)

    def delete(self, *args, **kwargs):
        if self.name == 'default':
            raise ValidationError("This configuration cannot be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class Conversation(models.Model):
    id = models.TextField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    tracker_yaml = models.TextField(editable=True)
    timestamp = models.DateTimeField(auto_now=True)
    model_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Identifier of the LLM used"
    )

    def clean(self):
        try:
            ConversationTracker.from_yaml(self.tracker_yaml)
        except Exception as e:
            raise ValidationError(f"Invalid conversation YAML: {str(e)}")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_tracker(self):
        return ConversationTracker.from_yaml(self.tracker_yaml)

    def update_from_tracker(self, tracker):
        self.tracker_yaml = tracker.to_yaml()
        self.save()

    def __str__(self):
        return f"Conversation {self.id} by {self.user.username} ({self.timestamp})"

    def get_readable_conversation(self):
        try:
            tracker = self.get_tracker()
            conversation_lines = []
            for entry in tracker:
                role = entry.get("role", "unknown")
                content = entry.get("content", "")
                metadata = entry.get("metadata", {})
                metadata_info = ", ".join(f"{key}: {value}" for key, value in metadata.items())
                conversation_lines.append(f"{role}: {content}\nMETA: {metadata_info}")
            return "\n\n".join(conversation_lines)
        except Exception as e:
            return f"Error parsing conversation: {str(e)}"

    class Meta:
        ordering = ['-timestamp']
        unique_together = ['id', 'user']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'timestamp', 'model_name', 'short_conversation')
    list_filter = ('user', 'model_name', 'timestamp')
    # fields = ("tracker_yaml",)
    readonly_fields = ('id', 'user', 'timestamp', 'model_name', 'readable_conversation')

    def short_conversation(self, obj):
        return obj.get_readable_conversation()[:75] + '...'

    short_conversation.short_description = 'Conversation Preview'

    def readable_conversation(self, obj):
        return obj.get_readable_conversation()

    readable_conversation.short_description = 'Readable Conversation'

    # def get_readonly_fields(self, request, obj=None):
    #     return ['readable_conversation'] + [f.name for f in self.model._meta.fields]
