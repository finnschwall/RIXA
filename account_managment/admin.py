from django.contrib import admin
from django.contrib.admin import ModelAdmin

from account_managment.models import UserTag, RixaUser
from .models import Invitation, User
# from django.contrib.auth.admin import UserAdmin
from django.contrib.sessions.models import Session
from django.urls import path
from .views import user_statistics_view
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class SessionAdmin(ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()

    list_display = ['session_key', '_session_data', 'expire_date']


class InvitationAdmin(admin.ModelAdmin):
    list_display = ['code', 'max_uses', 'uses', 'created_at', 'is_available']
    search_fields = ['code']
    list_filter = ['created_at']  # , 'is_available']
    readonly_fields = ['uses', 'created_at', 'url']

    def save_model(self, request, obj, form, change):
        if not change:
            pass
        super().save_model(request, obj, form, change)


class UserTagAdmin(admin.ModelAdmin):
    list_display = ['name']

    def save_model(self, request, obj, form, change):
        if not change:
            pass
        super().save_model(request, obj, form, change)


class RixaUserInline(admin.StackedInline):
    model = RixaUser
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = [RixaUserInline]


admin.site.register(UserTag, UserTagAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(Session, SessionAdmin)
# admin.site.unregister(User)
admin.site.register(User, UserAdmin)
