import os

from django.shortcuts import render, get_object_or_404, resolve_url
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect
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


current_study_mode = "UNKNOWN"

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
def edit_chat_configuration(request, ):
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

        return render(request, 'edit_chat_configuration.html',
                      {'is_form': True, 'form': form, "config_name": chat_config.name})
    else:
        names = ChatConfiguration.objects.values_list('name', flat=True)
        names_list = list(names)
        return render(request, 'edit_chat_configuration.html', {'is_form': False, "available_configs": names_list})


@login_required(login_url="about")
def home(request):
    global current_study_mode
    current_study_mode = "chat"
    user_settings = request.session.get("settings", None)

    if user_settings:
        enable_function_calls = user_settings.get("enable_function_calls", True)
        enable_knowledge_retrieval = user_settings.get("enable_knowledge_retrieval", True)
        selected_chat_mode = user_settings.get("selected_chat_mode", "default")
    else:
        enable_function_calls = True
        enable_knowledge_retrieval = True
        selected_chat_mode = "default"
    executor_work = (_memory.executor.get_active_task_count() / _memory.executor.get_max_task_count()) * 100
    task_queue_count = _memory.executor.get_queued_task_count()
    server_status = f"""Last updated (webserver): {datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')}<br>
DB: {"SQLITE" if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3" else "OK"}<br>
CHAT UTILIZATION: {executor_work:.1f}<br>
QUEUED TASKS: {task_queue_count}<br>
LLM BACKENDS: MISSING<br>
CALLABLE PLUGINS: {_memory.get_all_plugin_names()}<br>
GONE SKYNET?: NO(t yet)<br>"""
    globally_available_configs = set(
        ChatConfiguration.objects.filter(available_to_all=True).values_list('name', flat=True))
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
               "theme": settings.BOOTSTRAP_THEME, "enable_function_calls": enable_function_calls,
               "enable_knowledge_retrieval": enable_knowledge_retrieval,
               "available_chat_modes": available_chat_modes,
               "selected_chat": str(request.session.get("selected_chat", 0)),
               "selected_chat_mode": selected_chat_mode,
               "server_status": server_status,
               "plugin_settings": json.dumps(plugin_settings),
               }
    return render(request, 'home.html', context)


@login_required(login_url="about")
def dashboard(request):
    global current_study_mode
    current_study_mode = "dashboard"
    context = {"chat": False, "username": request.user.username,}
    return render(request, 'dashboard.html', context)


@login_required(login_url="about")
def dashboard2(request):
    global current_study_mode
    current_study_mode = "dashboard_chat"
    context = {"chat": True, "username": request.user.username,}
    return render(request, 'dashboard.html', context)

@login_required(login_url="about")
def study_status(request):
    current_index = "UNKNOWN"
    last_choices = "FAILURE TO GET LAST CHOICES"
    try:
        with open("/home/ies/schwall/rixaplugin_symlink/study_index.txt","r") as f:
            current_index=f.read()
        import pandas as pd
        last_choices = pd.read_csv("/home/ies/ashri/selections/ashri.txt", delimiter=";",
                                   names=["Timestamp","current_study_mode","Username","Index","ID","DatapointChoice","survey"])
        last_choices = last_choices.tail(20).to_html()

    except Exception as e:
        current_index = "Failure to get current index"


    if request.method == 'POST' and 'reset_button' in request.POST:
        import rixaplugin
        try:
            rixaplugin.execute("reset")
            return HttpResponseRedirect(request.path)
        except:
            return HttpResponseRedirect(f"{request.path}?error=FAILURE+TO+RESET")

    return render(request, 'study_status.html', {'current_index': current_index, "last_choices":last_choices})



@login_required(login_url="about")
def home_old(request):
    user_settings = request.session.get("settings", None)

    if user_settings:
        enable_function_calls = user_settings.get("enable_function_calls", True)
        enable_knowledge_retrieval = user_settings.get("enable_knowledge_retrieval", True)
        selected_chat_mode = user_settings.get("selected_chat_mode", "default")
    else:
        enable_function_calls = True
        enable_knowledge_retrieval = True
        selected_chat_mode = "default"
    executor_work = (_memory.executor.get_active_task_count() / _memory.executor.get_max_task_count()) * 100
    task_queue_count = _memory.executor.get_queued_task_count()
    server_status = f"""Last updated (webserver): {datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')}<br>
DB: {"SQLITE" if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3" else "OK"}<br>
CHAT UTILIZATION: {executor_work:.1f}<br>
QUEUED TASKS: {task_queue_count}<br>
LLM BACKENDS: MISSING<br>
CALLABLE PLUGINS: {_memory.get_all_plugin_names()}<br>
GONE SKYNET?: NO(t yet)<br>"""
    globally_available_configs = set(
        ChatConfiguration.objects.filter(available_to_all=True).values_list('name', flat=True))

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
               "theme": settings.BOOTSTRAP_THEME, "enable_function_calls": enable_function_calls,
               "enable_knowledge_retrieval": enable_knowledge_retrieval,
               "available_chat_modes": available_chat_modes,
               "selected_chat": str(request.session.get("selected_chat", 0)),
               "selected_chat_mode": selected_chat_mode,
               "server_status": server_status,
               "plugin_settings": json.dumps(plugin_settings)}
    return render(request, 'home_old.html', context)


def about(request):
    context = {"website_title": settings.WEBSITE_TITLE}
    return render(request, 'about.html', context)


def impressum(request):
    return render(request, 'impressum.html')


def test(request):
    context = {}
    return render(request, 'test.html', context)
