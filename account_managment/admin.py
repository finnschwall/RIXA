from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.sessions.models import Session
class SessionAdmin(ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()
    list_display = ['session_key', '_session_data', 'expire_date']
admin.site.register(Session, SessionAdmin)

admin.site.register(User, UserAdmin)