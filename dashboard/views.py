import os

from django.shortcuts import render, get_object_or_404
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

def conditional_decorator(decorator, condition):
    def decorate(func):

        if condition:
            return decorator(func)
        else:
            return func

    return decorate


latest_time = os.path.getmtime("..")
for root, dirs, files in os.walk(".."):
    for name in files + dirs:
        filepath = os.path.join(root, name)
        if os.path.isdir(filepath):
            file_time = os.path.getmtime(filepath)
            if file_time > latest_time:
                latest_time = file_time

@conditional_decorator(login_required(login_url="about"), settings.REQUIRE_LOGIN_CHAT)
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
                #display success message
                messages.success(request, 'Chat configuration updated successfully')

        else:
            form = ChatConfigurationForm(instance=chat_config)
        return render(request, 'edit_chat_configuration.html', {'is_form':True, 'form': form, "config_name":chat_config.name})
    else:
        names = ChatConfiguration.objects.values_list('name', flat=True)
        names_list = list(names)
        return render(request, 'edit_chat_configuration.html', {'is_form': False, "available_configs": names_list})


@conditional_decorator(login_required(login_url="about"), settings.REQUIRE_LOGIN_CHAT)
def home(request):
    user_settings = request.session.get("settings", None)
    if user_settings:
        enable_function_calls = user_settings.get("enable_function_calls", True)
        enable_knowledge_retrieval = user_settings.get("enable_knowledge_retrieval", True)
    else:
        enable_function_calls = True
        enable_knowledge_retrieval = True
    executor_work = (_memory.executor.get_active_task_count()/_memory.executor.get_max_task_count())*100
    task_queue_count = _memory.executor.get_queued_task_count()
    server_status = f"""Last updated (webserver): {datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')}<br>
DB: {"UNSTABLE. NO DATA PERSISTENCE GUARANTEE" if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3" else "OK"}<br>
CHAT UTILIZATION: {executor_work:.1f}<br>
QUEUED TASKS: {task_queue_count}<br>
BACKEND CONNECTION?: {'openai_server' in _memory.plugins}<br>
LLM BACKENDS: ERROR<br>
CALLABLE PLUGINS: ERROR<br>"""
    available_chat_modes = list(request.user.rixauser.configurations_read.values_list('name', flat=True))+["default"]

    context = {"chat_disabled": settings.DISABLE_CHAT, "website_title": settings.WEBSITE_TITLE,
               "chat_title": settings.CHAT_TITLE, "always_maximize_chat": settings.ALWAYS_MAXIMIZE_CHAT,
               "theme":settings.BOOTSTRAP_THEME, "enable_function_calls": enable_function_calls,
                "enable_knowledge_retrieval": enable_knowledge_retrieval,
               "available_chat_modes": available_chat_modes, "selected_chat": str(request.session.get("selected_chat", 0)),
               "selected_chat_mode" : request.session.get("selected_chat_mode", "default"),
               "server_status": server_status}
    return render(request, 'home.html', context)


def about(request):
    context = {"website_title": settings.WEBSITE_TITLE}
    return render(request, 'about.html', context)


def test(request):
    context = {}
    return render(request, 'test.html', context)



def json_stripped(dic):
    s = json.dumps(dic, indent="\t")
    s = s.replace("{", "")
    s = s.replace(",", "NEWLINEHERE")
    s = s.replace("}", "")
    s = s.replace("]", "")
    s = s.replace("[", "")
    s = s.replace("\"", "")
    s = [line for line in s.split('\n') if line.strip() != '']
    s = [i[1:] for i in s]
    s = "\n".join(s)
    s = s.replace("NEWLINEHERE", "\n")
    return s
