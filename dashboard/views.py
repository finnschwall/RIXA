from django.shortcuts import render
from django.http import HttpResponseForbidden, JsonResponse
import json
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required


def conditional_decorator(decorator, condition):
    def decorate(func):

        if condition:
            return decorator(func)
        else:
            return func

    return decorate


@conditional_decorator(login_required, settings.REQUIRE_LOGIN_CHAT)
def home(request):
    context = {"chat_disabled": settings.DISABLE_CHAT, "website_title": settings.WEBSITE_TITLE,
               "chat_title": settings.CHAT_TITLE, "always_maximize_chat": settings.ALWAYS_MAXIMIZE_CHAT,
               "theme":settings.BOOTSTRAP_THEME}
    return render(request, 'home.html', context)


@conditional_decorator(login_required, settings.REQUIRE_LOGIN_CHAT)
def user_study(request):
    from plugins import api
    context = {"chat_disabled": settings.DISABLE_CHAT, "website_title": settings.WEBSITE_TITLE,
               "chat_title": settings.CHAT_TITLE, "always_maximize_chat": settings.ALWAYS_MAXIMIZE_CHAT,
               "study_mode" : settings.USER_STUDY_MODE, "css_key":settings.BOOTSTRAP_THEME
               }
    return render(request, 'userstudy.html', context)


def test(request):
    context = {}
    return render(request, 'test.html', context)


def dict_to_markdown(data, indent=0):
    markdown = ""
    for key, value in data.items():
        if isinstance(value, dict):
            # Recursively convert nested dictionaries
            markdown += f"{'  ' * indent}- **{key}**:\n"
            markdown += dict_to_markdown(value, indent + 1)
        else:
            # Format key-value pairs
            markdown += f"{'  ' * indent}- **{key}**: {value}\n"
    return markdown


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
