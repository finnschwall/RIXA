import os

from django.shortcuts import render, get_object_or_404, resolve_url
from django.http import HttpResponseForbidden, JsonResponse
import json
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from rixaplugin import _memory
from django.contrib import messages
from account_managment.models import RixaUser
from dashboard.forms import ChatConfigurationForm
from dashboard.models import ChatConfiguration
from django.http import HttpResponseNotFound

from urllib.parse import urlparse
import functools
def conditional_decorator(decorator, condition):
    def decorate(func):

        if condition:
            return decorator(func)
        else:
            return func

    return decorate


def conditional_login(view_func):
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        login_url = "about"
        if settings.MAINTENANCE_MODE:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                return render(request, 'maintenance.html')
        if request.user.is_authenticated and settings.REQUIRE_LOGIN_CHAT:
            return view_func(request, *args, **kwargs)
        path = request.build_absolute_uri()
        resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)

        login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
        current_scheme, current_netloc = urlparse(path)[:2]
        if (not login_scheme or login_scheme == current_scheme) and (
                not login_netloc or login_netloc == current_netloc
        ):
            path = request.get_full_path()
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(path, resolved_login_url)

    return _wrapped_view



latest_time = os.path.getmtime("..")
for root, dirs, files in os.walk(".."):
    for name in files + dirs:
        filepath = os.path.join(root, name)
        if os.path.isdir(filepath):
            file_time = os.path.getmtime(filepath)
            if file_time > latest_time:
                latest_time = file_time

# @conditional_decorator(login_required(login_url="about"), settings.REQUIRE_LOGIN_CHAT)
@login_required(login_url="about")
def edit_chat_configuration(request,):
    query_params = request.GET
    template_id = query_params.get("template_id", None)
    if template_id:
        try:
            chat_config = ChatConfiguration.objects.get(name=template_id)
        except ChatConfiguration.DoesNotExist:
            return HttpResponseNotFound("No chat config with that name")
        user_has_permission = request.user.rixauser.configuration_write.filter(id=chat_config.id).exists()
        if not user_has_permission:
            return HttpResponseForbidden("You do not have permission to edit this configuration")
        if request.method == 'POST':
            form = ChatConfigurationForm(request.POST, instance=chat_config)
            if form.is_valid():
                form.save()
                messages.success(request, 'Chat configuration updated successfully')

        else:
            form = ChatConfigurationForm(instance=chat_config)

        return render(request, 'edit_chat_configuration.html', {'is_form':True, 'form': form, "config_name":chat_config.name})
    else:
        names = ChatConfiguration.objects.values_list('name', flat=True)
        names_list = list(names)
        return render(request, 'edit_chat_configuration.html', {'is_form': False, "available_configs": names_list})



@login_required(login_url="about")
def home(request):
    user_settings = request.session.get("settings", None)

    if user_settings:
        enable_function_calls = user_settings.get("enable_function_calls", True)
        enable_knowledge_retrieval = user_settings.get("enable_knowledge_retrieval", True)
        selected_chat_mode = user_settings.get("selected_chat_mode", "default")
    else:
        enable_function_calls = True
        enable_knowledge_retrieval = True
        selected_chat_mode = "default"
    executor_work = (_memory.executor.get_active_task_count()/_memory.executor.get_max_task_count())*100
    task_queue_count = _memory.executor.get_queued_task_count()
    server_status = f"""Last updated (webserver): {datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')}<br>
DB: {"SQLITE" if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3" else "OK"}<br>
CHAT UTILIZATION: {executor_work:.1f}<br>
QUEUED TASKS: {task_queue_count}<br>
LLM BACKENDS: MISSING<br>
CALLABLE PLUGINS: {_memory.get_all_plugin_names()}<br>
GONE SKYNET?: NO(t yet)<br>"""
    globally_available_configs = set(ChatConfiguration.objects.filter(available_to_all=True).values_list('name', flat=True))
    user_available_chat_modes = set(request.user.rixauser.configurations_read.values_list('name', flat=True))
    available_chat_modes = list(globally_available_configs.union(user_available_chat_modes))




    plugin_settings = _memory.get_all_variables()
    user_settings = request.session.get("plugin_variables", {})
    for key, val in user_settings.items():
        if key in plugin_settings:
            for varkey, varval in val.items():
                if varkey in plugin_settings[key]:
                    plugin_settings[key][varkey]["value"] = varval

    context = {"chat_disabled": settings.DISABLE_CHAT, "website_title": settings.WEBSITE_TITLE,
               "chat_title": settings.CHAT_TITLE, "always_maximize_chat": settings.ALWAYS_MAXIMIZE_CHAT,
               "theme":settings.BOOTSTRAP_THEME, "enable_function_calls": enable_function_calls,
                "enable_knowledge_retrieval": enable_knowledge_retrieval,
               "available_chat_modes": available_chat_modes, "selected_chat": str(request.session.get("selected_chat", 0)),
               "selected_chat_mode" :selected_chat_mode,
               "server_status": server_status,
               "plugin_settings":json.dumps(plugin_settings)}
    return render(request, 'home.html', context)


@login_required(login_url="about")
def home_new(request):
    user_settings = request.session.get("settings", None)

    if user_settings:
        enable_function_calls = user_settings.get("enable_function_calls", True)
        enable_knowledge_retrieval = user_settings.get("enable_knowledge_retrieval", True)
        selected_chat_mode = user_settings.get("selected_chat_mode", "default")
    else:
        enable_function_calls = True
        enable_knowledge_retrieval = True
        selected_chat_mode = "default"
    executor_work = (_memory.executor.get_active_task_count()/_memory.executor.get_max_task_count())*100
    task_queue_count = _memory.executor.get_queued_task_count()
    server_status = f"""Last updated (webserver): {datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')}<br>
DB: {"SQLITE" if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3" else "OK"}<br>
CHAT UTILIZATION: {executor_work:.1f}<br>
QUEUED TASKS: {task_queue_count}<br>
LLM BACKENDS: MISSING<br>
CALLABLE PLUGINS: {_memory.get_all_plugin_names()}<br>
GONE SKYNET?: NO(t yet)<br>"""
    globally_available_configs = set(ChatConfiguration.objects.filter(available_to_all=True).values_list('name', flat=True))
    user_available_chat_modes = set(request.user.rixauser.configurations_read.values_list('name', flat=True))
    available_chat_modes = list(globally_available_configs.union(user_available_chat_modes))




    plugin_settings = _memory.get_all_variables()
    user_settings = request.session.get("plugin_variables", {})
    for key, val in user_settings.items():
        if key in plugin_settings:
            for varkey, varval in val.items():
                if varkey in plugin_settings[key]:
                    plugin_settings[key][varkey]["value"] = varval

    context = {"chat_disabled": settings.DISABLE_CHAT, "website_title": settings.WEBSITE_TITLE,
               "chat_title": settings.CHAT_TITLE, "always_maximize_chat": settings.ALWAYS_MAXIMIZE_CHAT,
               "theme":settings.BOOTSTRAP_THEME, "enable_function_calls": enable_function_calls,
                "enable_knowledge_retrieval": enable_knowledge_retrieval,
               "available_chat_modes": available_chat_modes, "selected_chat": str(request.session.get("selected_chat", 0)),
               "selected_chat_mode" :selected_chat_mode,
               "server_status": server_status,
               "plugin_settings":json.dumps(plugin_settings)}
    return render(request, 'home_new.html', context)


def about(request):
    context = {"website_title": settings.WEBSITE_TITLE}
    return render(request, 'about.html', context)


def test(request):
    context = {}
    return render(request, 'test.html', context)



